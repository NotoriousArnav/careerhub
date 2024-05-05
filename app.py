from fastapi import FastAPI
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pymongo import MongoClient
from data_class import *
import os
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.careerhub

ph = PasswordHasher()

def verify_password(password, hashed):
    try:
        ph.verify(hashed, password)
        return True
    except Exception as e:
        return False

def get_user(email: str):
    obj = db.users.find_one(
        {
            "resume.basic.email": email # Finds out if the request is from a Existing User
        }
    )
    return UserData(**obj)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv('TOKEN_SECRET_KEY'), algorithm='HS256')
    return encoded_jwt

@app.post('/register')
async def register(ud: UserData):
    """
    # Registraion Route
    These Details are Atleast Required!
    - Basic Details
        - Name
        - Email
        - Phone
        - Biodata (summary)
        - Location
    - Education
        Institute (Array)
        - Name
        - Website (url)
        - Area of Study (area)
        - Study Type (HSC, Bachelor, Masters, PHd, etc)
        - Start Date
        - End Date
        - Score (your marks)
        - Courses (Optional)
    - Skills
        Skill (Array)
        - Name
        - Level (0-100)
        - Keywords
    - Languages
        Language (Array)
        - Name
        - Fluency (0-100)
    - Password

    """
    obj = get_user(ud.resume.basic.email)
    ud.password = ph.hash(ud.password)
    data = json.loads(ud.json()) # Kinda Important as MongoDB requires a Dict
    uid = None
    if obj is None:
        uid = db.users.insert_one(data).inserted_id
    return {
        'user_created': True if obj is None else False,
        'uid': uid
    }

@app.post('/token')
async def get_jwt(login: LoginData):
    """# Get Token Route
    Post your Email and Password in Exchange for a JWT Token.
    """
    user = get_user(login.email)
    if user:
        if verify_password(login.password, user.password):
            token = create_access_token(json.loads(user.resume.basic.json()))
            return {
                'access_token': token,
                'type': 'Bearer'
            }
        else:
            return {
                'message': 'Incorrect Password'
            }
    else:
        return {
            'message': 'User not Found'
        }
    return {}
