from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_query(query: str):
    return model.encode(query).tolist()

def retrieve_similar_cases(db, query_vector, top_k=3):
    from models import Case
    from sqlalchemy.orm import Session
    from pgvector.sqlalchemy import Vector
    cases = db.query(Case).order_by(
        Case.similarity_vector.cosine_distance(query_vector)
    ).limit(top_k).all()
    return cases

def generate_answer(query: str, cases: list):
    if not cases:
        return "لم يتم العثور على سوابق مشابهة."
    context = "\n".join([case.legal_principles for case in cases])
    return f"بناءً على السوابق القضائية، {query} يُفسَّر غالبًا على النحو التالي:\n{context[:500]}..."