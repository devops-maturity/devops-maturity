from pydantic import BaseModel
from sqlalchemy import Column, Integer, JSON, create_engine
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
    responses = Column(JSON)


def init_db():
    Base.metadata.create_all(bind=engine)
