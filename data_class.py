from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import List, Dict, Optional, Annotated, Literal
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

class Company(BaseModel):
    name: str
    handle: str
    industry: str
    founded: int
    description: str
    logo: str

class CurrentJob(BaseModel):
    company: Company
    position: str

class Resume(BaseModel):
    basic: BasicInfo
    working_at: Optional[CurrentJob] = None
    education: List[Education]
    skills: List[Skill]
    languages: List[Language]
    projects: Optional[List[Project]]
    certificates: Optional[List[Certificate]]
    awards: Optional[List[Award]]
    work: Optional[List[Experience]]
    interests: Optional[List[Interest]]

class Founder(BaseModel):
    founder_email: EmailStr # Founder's Email
    company_handle: str

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

class UserCheck(BaseModel):
    username_taken: bool
    email_used: bool

class RegistrationStatus(BaseModel):
    user_created: bool
    uid: str
    message: UserCheck

class Recruiter(BaseModel):
    recruiter_email: EmailStr
    recruiter: str
    company_handle: str

class Opportunity(BaseModel):
    position: str
    company: Company
    description: str
    location: str
    opportunity_type: Literal['job', 'internship']
    start_date: datetime
    end_date: Optional[datetime] = None  # Only for internships
    requirements: List[Education] = []
    preferred_skills: List[Skill] = []
    preferred_experience: List[Experience] = []
    application_deadline: datetime
    salary_range: Optional[str] = None
    url: Optional[HttpUrl] = None

    @validator('opportunity_type')
    def check_opportunity_type(cls, value):
        if value not in ['job', 'internship']:
            raise ValueError('opportunity_type must be either "job" or "internship"')
        return value

    @validator('end_date')
    def check_end_date(cls, value, values):
        if values.get('opportunity_type') == 'job' and value is not None:
            raise ValueError('end_date should not be provided for job opportunities')
        return value

class OpportunityWithID(Opportunity):
    id: str

    def __init__(self, **data):
        if '_id' in data:
            data['id'] = str(data['_id'])
        super().__init__(**data)

    class Config:
        orm_mode = True
