from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class Contact(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    github: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None

class SocialAccount(BaseModel):
    name: str
    url: str

class Education(BaseModel):
    institution: str
    area: Optional[str] = None
    studyType: Optional[str] = None
    startDate: date
    endDate: Optional[date] = None
    score: Optional[float] = None
    description: Optional[str] = None

class Experience(BaseModel):
    name: str
    company: str
    location: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None
    startDate: date
    endDate: Optional[date] = None
    current: Optional[bool] = None
    roles: List[str] = []
    description: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    startDate: date
    endDate: Optional[date] = None
    roles: List[str] = []
    website: Optional[str] = None
    repository: Optional[str] = None

class Skill(BaseModel):
    name: str
    level: Optional[int] = None
    keywords: Optional[List[str]] = None

class Resume(BaseModel):
    basics: Contact
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: List[Skill]
    social: List[SocialAccount]
    summary: Optional[str] = None
    languages: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    references: Optional[List[str]] = None
    publications: Optional[List[str]] = None
    awards: Optional[List[str]] = None
    volunteering: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
