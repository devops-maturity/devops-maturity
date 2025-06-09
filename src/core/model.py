from pydantic import BaseModel
from sqlalchemy import Column, Integer, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Criteria(BaseModel):
    id: str
    question: str
    weight: float


class UserResponse(BaseModel):
    id: str
    answer: bool


class Assessment(Base):  # type: ignore
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    responses = Column(JSON)


engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def init_db():
    global engine
    engine = create_engine("sqlite:///./devops_maturity.db")
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
