# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_classes import Resume, Contact, EmailStr
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///resume.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the Resume model for the database
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)

    resume_id = Column(Integer, ForeignKey("resumes.id"))
    resume = relationship("ResumeDB", backref="user")

class ResumeDB(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    basics = Column(String)
    education = Column(String)
    experience = Column(String)
    projects = Column(String)
    skills = Column(String)
    social = Column(String)
    summary = Column(String)
    languages = Column(String)
    interests = Column(String)
    references = Column(String)
    publications = Column(String)
    awards = Column(String)
    volunteering = Column(String)
    certifications = Column(String)

Base.metadata.create_all(engine)

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get the current user
def get_current_user(db: SessionLocal = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = db.query(UserDB).filter(UserDB.email == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user

@app.post("/register")
async def register(resume: Resume, db: SessionLocal = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.email == resume.basics.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    # Create a new user
    new_user = UserDB(email=resume.basics.email, password="password")  # Replace with password hashing
    db.add(new_user)
    db.commit()
    # Create a new resume
    new_resume = ResumeDB(
        email=resume.basics.email,
        basics=resume.basics.json(),
        education=[edu.json() for edu in resume.education],
        experience=[exp.json() for exp in resume.experience],
        projects=[proj.json() for proj in resume.projects],
        skills=[skill.json() for skill in resume.skills],
        social=[social.json() for social in resume.social],
        summary=resume.summary,
        languages=resume.languages,
        interests=resume.interests,
        references=resume.references,
        publications=resume.publications,
        awards=resume.awards,
        volunteering=resume.volunteering,
        certifications=resume.certifications,
        user=new_user
    )
    db.add(new_resume)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "User created successfully"})

@app.post("/token")
async def login_for_access_token(email: EmailStr, password: str, db: SessionLocal = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user or user.password!= password:  # Replace with password hashing
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = "access_token"  # Replace with a secure token generation
    return JSONResponse(status_code=200, content={"access_token": access_token, "token_type": "bearer"})

@app.get("/me")
async def read_user_me(current_user: UserDB = Depends(get_current_user)):
    resume = current_user.resume
    return JSONResponse(status_code=200, content={
        "email": current_user.email,
        "resume": {
            "basics": resume.basics,
"education": resume.education,
            "experience": resume.experience,
            "projects": resume.projects,
            "skills": resume.skills,
            "social": resume.social,
            "summary": resume.summary,
            "languages": resume.languages,
            "interests": resume.interests,
            "references": resume.references,
            "publications": resume.publications,
            "awards": resume.awards,
            "volunteering": resume.volunteering,
            "certifications": resume.certifications,
        }
    })
