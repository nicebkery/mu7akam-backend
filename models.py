from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base
from pgvector.sqlalchemy import Vector

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    points = Column(Integer, default=10)
    is_admin = Column(Boolean, default=False)

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    legal_principles = Column(Text)
    verdict = Column(String)
    similarity_vector = Column(Vector(384))
    source_file = Column(String)