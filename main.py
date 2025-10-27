from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import jwt, JWTError
from datetime import timedelta
import os

# استيراد المكونات المحلية
from database import get_db, engine
from models import User
from auth import authenticate_user, create_access_token, get_password_hash
from schemas import UserCreate, Token, QueryRequest, QueryResponse, AddPointsRequest
from rag import embed_query, retrieve_similar_cases, generate_answer

# إعدادات الأمان
SECRET_KEY = os.getenv("SECRET_KEY", "mu7akam_secret_key_2025_sudan")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="مُحكَم - Backend API")

# CORS: السماح لواجهة Netlify بالاتصال
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mu7akam.netlify.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تفعيل pgvector تلقائيًا عند بدء التشغيل
@app.on_event("startup")
def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    print("✅ pgvector enabled successfully.")

# دالة للحصول على المستخدم من التوكن
def get_current_user(token: str = Header(...), db: Session = Depends(get_db)):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = token[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# === Endpoints ===

@app.post("/auth/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user.password)
    new_user = User(email=user.email, password=hashed_pw, points=10)
    db.add(new_user)
    db.commit()
    return {"msg": "User created"}

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/query", response_model=QueryResponse)
def query_rag(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.points <= 0:
        raise HTTPException(status_code=402, detail="Insufficient points")
    current_user.points -= 1
    db.commit()

    query_vec = embed_query(request.query)
    cases = retrieve_similar_cases(db, query_vec, top_k=3)
    answer = generate_answer(request.query, cases)
    context = [c.legal_principles for c in cases] if cases else []
    source_files = list(set(c.source_file for c in cases)) if cases else []

    return QueryResponse(answer=answer, context=context, source_files=source_files)

@app.post("/admin/add-points")
def add_points(
    body: AddPointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.points += body.points
    db.commit()
    return {"msg": f"Added {body.points} points to {body.email}"}