from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import List, Dict, Optional, Annotated
from datetime import datetime

class SocialProfiles(BaseModel):
    network: str
    username: str
    url: HttpUrl

class BasicInfo(BaseModel):
    name: str
    email: EmailStr
    image: str
    phone: str
    url: Optional[HttpUrl]
    summary: Optional[str]
    location: str
    profiles: Optional[List[SocialProfiles]]

class Education(BaseModel):
    institution: str
    url: str
    area: str
    studytype: str
    start_date: datetime
    end_date: datetime
    score: float
    courses: List[str]

class Skill(BaseModel):
    name: str
    level: float = Field(None, ge=0, li=100)
    keywords: List[str]

class Language(BaseModel):
    name: str
    fluency: float = Field(None, ge=0, li=100)

class Project(BaseModel):
    name: str
    desription: str
    start_date: datetime
    end_date: datetime
    url: Optional[HttpUrl]
    highlights: List[str]

class Certificate(BaseModel):
    name: str
    date: datetime
    issuer: str
    url: Optional[HttpUrl]

class Award(BaseModel):
    title: str
    date: datetime
    awarder: str
    summary: str

class Experience(BaseModel):
    name: str
    position: str
    url: HttpUrl
    start_date: datetime
    enddate: datetime
    summary: str

class Interest(BaseModel):
    name: str
    keywords: List[str]

class Resume(BaseModel):
    basic: BasicInfo
    education: List[Education]
    skills: List[Skill]
    languages: List[Language]
    projects: Optional[List[Project]]
    certificates: Optional[List[Certificate]]
    awards: Optional[List[Award]]
    work: Optional[List[Experience]]
    interests: Optional[List[Interest]]

# User Data
class UserData(BaseModel):
    resume: Resume
    username: str
    password: str

class LoginData(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str

