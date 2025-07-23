from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine("sqlite:///./devops_maturity.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Criteria(BaseModel):
    id: str
    category: str
    criteria: str
    weight: float


class UserResponse(BaseModel):
    id: str
    answer: bool


class Assessment(Base):  # type: ignore
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    user_id = Column(Integer)
    responses = Column(JSON)


class User(Base):  # type: ignore
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # nullable for OAuth users
    oauth_provider = Column(String, nullable=True)  # e.g., 'google', 'github'
    oauth_id = Column(String, nullable=True)  # provider user id


def init_db():
    Base.metadata.create_all(bind=engine)
