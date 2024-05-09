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

app = FastAPI(
    title = "CareerHub Backend API",
    description = """The Official Backend API of CareerHub. All API routes have been Documented using OpenAPI Standard"""
)
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

def get_user_by_email(email: str):
    obj = db.users.find_one(
        {
            "resume.basic.email": email # Finds out if the request is from a Existing User
        }
    )
    if obj:
        return UserData(**obj)

def get_company_by_handle(handle: str):
    obj = db.company.find_one(
        {
            "handle": handle
        }
    )
    if obj:
        return Company(**obj)


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
    except JWTError as e:
        print(e)
        raise credentials_exception
    user = get_user_by_username(token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[UserData, Depends(get_current_user)],
):
    return current_user


@app.post('/register', response_model=RegistrationStatus)
async def register(ud: UserData):
    """
    # Registration Route
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
    obj = get_user_by_email(ud.resume.basic.email)
    obj1 = get_user_by_username(ud.username)
    ud.password = ph.hash(ud.password)
    data = json.loads(ud.json()) # Kinda Important as MongoDB requires a Dict
    uid = None # Don't ask me why it is so complicated. It works,so should you.
    if obj is None and obj1 is None:
        uid = db.users.insert_one(data).inserted_id
    username_taken = True if obj1 else False
    email_used = True if obj else False
    return RegistrationStatus(
        user_created =True if ((obj is None) and (obj1 is None)) else False,
        uid = str(uid),
        message = UserCheck(username_taken = username_taken, email_used = email_used)
    )

@app.post('/token')
async def get_jwt(login: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """# Get Token Route
    Post your username and Password in Exchange for a JWT Token valid for 15 Minutes.
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
                data = {"sub": user.username},
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

@app.put('/resume', response_model=UserData)
async def modify_user_resume(resume: Resume, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    # Modify User Resume
    Update the resume details for the current user.
    """
    try:
        # Update the resume field in the UserData object
        current_user.resume = resume

        # Convert the updated UserData object to a dictionary
        import json
        updated_user_data = json.loads(current_user.json())

        # Update the document in MongoDB
        result = db.users.update_one(
            {'username': current_user.username},
            {'$set': updated_user_data}
        )

        if result.modified_count > 0:
            # Return the updated UserData object
            return current_user
        else:
            return {'message': 'No changes made'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/change-password')
async def change_password(new_password: str, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    # Change User Password
    Update the password for the current user.
    """
    try:
        # Hash the new password
        hashed_password = ph.hash(new_password)

        # Update the password field in the UserData object
        current_user.password = hashed_password

        # Convert the updated UserData object to a dictionary
        updated_user_data = current_user.dict()

        # Update the document in MongoDB
        result = db.users.update_one(
            {'username': current_user.username},
            {'$set': updated_user_data}
        )

        if result.modified_count > 0:
            # Return the updated UserData object
            return {
                'password_changed': true
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/regsiter/company', response_model=Founder)
async def register_company(company: Company, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """# Register a Company"""
    if get_company_by_handle(company.handle):
        return {
            "company_exists": True
        }
    founder = Founder(founder_email=current_user.resume.basic.email, company_handle=company.handle)
    cid = db.company.insert_one(json.loads(company.json())).inserted_id
    fid = db.founders.insert_one(json.loads(founder.json())).inserted_id
    return founder

@app.post('/register/recruiter')
async def be_recruiter(company_handle: str, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    data = Recruiter(
        company_handle=company_handle,
        recruiter_email=current_user.resume.basic.email
    )
    obj = db.recruiters.find_one(data.dict())
    if obj:
        return HTTPException(
            status_code = 302,
            detail=f"Recruiter already exists"
        )
    rid = db.recruiters.insert_one(data.dict()).inserted_id
    return data


@app.get('/recruiter', response_model=List[Recruiter])
async def list_recruiters():
    data = [Recruiter(**x) for x in db.recruiters.find({})]
    return data

@app.get('/company', response_model=List[Company])
async def list_companies():
    data = [Company(**x) for x in db.company.find({})]
    return data

@app.get('/company/{company_handle}', response_model=Company)
async def company_details(company_handle):
    data = Company(**db.company.find_one({'handle': company_handle}))
    return data

@app.get('/company/{company_handle}/recruiters')
async def list_recruiters_from_company(company_handle: str):
    data = [Recruiter(**x) for x in db.recruiters.find({ 'company_handle': company_handle })]
    return data


