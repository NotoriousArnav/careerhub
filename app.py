from fastapi import FastAPI, Depends, HTTPException, status
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


def get_user(email: str, username: str):
    obj = db.users.find_one(
        {
            "resume.basic.email": email # Finds out if the request is from a Existing User
        }
    )
    if obj and obj['username']==username:
        return UserData(**obj)

def get_user_by_username(username: str):
    obj = db.users.find_one(
        {
            "username": username # Finds out if the request is from a Existing User
        }
    )
    if obj:
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

def authenticate_user(login:str, password: str):
    user = get_user_by_username(login)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv('TOKEN_SECRET_KEY'), algorithms=['HS256'])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(email=username)
    except JWTError:
        raise credentials_exception
    user = get_user(token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[UserData, Depends(get_current_user)],
):
    return current_user


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
    obj = get_user(ud.resume.basic.email, ud.username)
    obj1 = get_user_by_username(ud.username)
    ud.password = ph.hash(ud.password)
    data = json.loads(ud.json()) # Kinda Important as MongoDB requires a Dict
    uid = None
    if obj is None and obj1 is None:
        uid = db.users.insert_one(data).inserted_id
    return {
        'user_created': True if ((obj is None) and (obj1 is None)) else False,
        'uid': str(uid)
    }

@app.post('/token')
async def get_jwt(login: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """# Get Token Route
    Post your username and Password in Exchange for a JWT Token.
    Note: Your Username is your Registered Email
    """
    user = authenticate_user(login.username, login.password)
    if not user:
        raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail = "Login Details Incorrect",
                    headers = {'WWW-Authenticate', 'Bearer'}
                )
    access_token_expires = timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 20)))
    access_token = create_access_token(
                data = {"sub": [user.resume.basic.email, user.username]},
                expires_delta = access_token_expires
            )
    return Token(access_token=access_token, token_type="Bearer")


@app.get('/resume', response_model=Resume)
async def get_user_resume(current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    # Return the Resume of the User
    requires
    - Authorization Token in the Header
    """
    return Resume(**current_user.resume.dict())

@app.get('/resume/{username}', response_model=Resume)
async def get_user_resume_username(username: str):
    """
    # Get Resume of a Specific User
    """
    user = get_user_by_username(username)
    if user:
        return user.resume

@app.post('/resume')
async def modify_user_resume(current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """# Modify User Resume"""
    return {}
