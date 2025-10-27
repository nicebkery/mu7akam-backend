from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    context: List[str]
    source_files: List[str]

class AddPointsRequest(BaseModel):
    email: str
    points: int