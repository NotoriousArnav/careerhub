from fastapi import FastAPI, Depends, HTTPException, status
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from bson.objectid import ObjectId
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pymongo import MongoClient
from data_class import *
import git
import datetime
import dns
import os
import json

repo = git.Repo(search_parent_directories=True)
sha = repo.head.object.hexsha

app = FastAPI(
    title = "CareerHub Backend API",
    description = f"""## CareerHub
The Official Backend API of CareerHub. All API routes have been Documented using OpenAPI Standard.

**Currently Running on Commit: {sha[:7]}**
"""
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.careerhub

ph = PasswordHasher()

origins = ["*"] # Should be configured to Only allow selected apps.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        if exp is None or datetime.datetime.utcnow() >= datetime.datetime.fromtimestamp(exp):
            raise credentials_exception
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

def is_recruiter_or_company_owner(current_user: UserData, company_handle: Optional[str] = None):
    """
    Check if the current user is a recruiter or a company owner.
    If company_handle is provided, it checks for the specified company.
    If company_handle is not provided, it checks if the user is a recruiter or company owner for any company.
    """
    if company_handle:
        # Check if the user is a recruiter for the specified company
        recruiter = db.recruiters.find_one({
            "recruiter": current_user.username,
            "company_handle": company_handle
        })
        if recruiter:
            return True

        # Check if the user is a founder/owner of the specified company
        founder = db.founders.find_one({
            "founder_email": current_user.resume.basic.email,
            "company_handle": company_handle
        })
        if founder:
            return True

    else:
        # Check if the user is a recruiter for any company
        recruiter = db.recruiters.find_one({
            "recruiter": current_user.username
        })
        if recruiter:
            return True

        # Check if the user is a founder/owner of any company
        founder = db.founders.find_one({
            "founder_email": current_user.resume.basic.email
        })
        if founder:
            return True

    return False

@app.get('/')
async def index():
    return {
        'message': 'The Service is up'
    }

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

@app.delete("/register")
async def unregister_user(request: UnregisterUserRequest, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Unregister a user from the system.
    """
    # Verify that the email in the request matches the current user's email
    if request.email != current_user.resume.basic.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Email does not match the current user.")

    # Delete the user document from the database
    result = db.users.delete_one({"resume.basic.email": request.email})

    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Delete any other associated data (e.g., applications, recruiters, etc.)
    db.applications.delete_many({"candidate_email": request.email})
    db.recruiters.delete_many({"recruiter_email": request.email})
    # ... (delete any other associated data)

    # Log the unregister reason
    logging.info(f"User {request.email} unregistered. Reason: {request.reason}")

    return {"message": "User unregistered successfully."}

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

@app.delete("/register/company", response_model=dict)
async def unregister_company(request: UnregisterCompanyRequest, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Unregister a company.
    """
    company_handle = request.company_handle
    # Check if the current user is the founder/owner of the company
    founder = db.founders.find_one({
        "founder_email": current_user.resume.basic.email,
        "company_handle": company_handle
    })
    if not founder:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the company owner can unregister the company.")

    # Delete the company from the database
    result = db.company.delete_one({"handle": company_handle})

    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Company not found.")

    # Delete the founder document
    db.founders.delete_one({"_id": founder["_id"]})

    # Delete all recruiters associated with the company
    db.recruiters.delete_many({"company_handle": company_handle})

    # Delete all opportunities associated with the company
    db.opportunities.delete_many({"company.handle": company_handle})

    # Notify recruiters about company unregistration
    recruiters = db.recruiters.find({"company_handle": company_handle})
    for recruiter in recruiters:
        # Send notification to the recruiter's email
        recruiter_email = recruiter["recruiter_email"]
        # Include the reason for unregistration in the notification
        # ... (your notification logic here)

    return {"message": "Company unregistered successfully.", "reason": request.reason}

@app.post('/register/recruiter')
async def be_recruiter(company_handle: str, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    data = Recruiter(
        company_handle=company_handle,
        recruiter_email=current_user.resume.basic.email,
        recruiter=current_user.username
    )
    obj = db.recruiters.find_one(data.dict())
    if obj:
        return HTTPException(
            status_code = 302,
            detail=f"Recruiter already exists"
        )
    rid = db.recruiters.insert_one(data.dict()).inserted_id
    return data

@app.delete('/register/recruiter')
async def delete_recruiter(company_handle: str, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    data = Recruiter(
        company_handle=company_handle,
        recruiter_email=current_user.resume.basic.email,
        recruiter=current_user.username
    )
    obj = db.recruiters.find_one(data.dict())
    if not obj:
        return data
    db.recruiters.delete_one(data.dict())
    return {
        'data': data,
        'removed': True
    }

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


@app.post("/opportunities", response_model=Opportunity)
async def create_opportunity(opportunity: Opportunity, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Create a new job or internship opportunity.
    """
    # Check if the user is a recruiter or company owner
    if not is_recruiter_or_company_owner(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only recruiters and company owners can create opportunities.")

    # Convert the Pydantic model to a dictionary
    opportunity_data = json.loads(opportunity.json())

    # Insert the opportunity into the database
    opportunity_id = db.opportunities.insert_one(opportunity_data).inserted_id

    # Retrieve the inserted opportunity from the database
    inserted_opportunity = db.opportunities.find_one({"_id": opportunity_id})

    # Convert the database object to a Pydantic model
    return OpportunityWithID(**inserted_opportunity)

@app.get('/opportunities')
async def list_all_opportunities(
    company: Optional[str] = None,
    location: Optional[str] = None,
    opportunity_type: Optional[str] = None,
    keyword: Optional[str] = None
):
    """
    Get a list of job and internship opportunities with filtering options.
    """
    query = {}

    if company:
        query["company.name"] = company
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if opportunity_type:
        query["opportunity_type"] = opportunity_type
    if keyword:
        query["$text"] = {"$search": keyword}

    opportunities = [OpportunityWithID(**opportunity) for opportunity in db.opportunities.find(query)]
    return opportunities

@app.get("/opportunities/{opportunity_id}", response_model=Opportunity)
async def get_opportunity(opportunity_id: str):
    """
    Get details of a specific job or internship opportunity.
    """
    opportunity = db.opportunities.find_one({"_id": ObjectId(opportunity_id)})
    if not opportunity:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    return Opportunity(**opportunity)

@app.put("/opportunities/{opportunity_id}", response_model=Opportunity)
async def update_opportunity(opportunity_id: str, opportunity: Opportunity, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Update an existing job or internship opportunity.
    """
    # Check if the user is a recruiter or company owner
    if not is_recruiter_or_company_owner(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only recruiters and company owners can update opportunities.")

    # Convert the Pydantic model to a dictionary
    opportunity_data = opportunity.dict()

    # Update the opportunity in the database
    result = db.opportunities.update_one({"_id": ObjectId(opportunity_id)}, {"$set": opportunity_data})

    if result.modified_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    # Retrieve the updated opportunity from the database
    updated_opportunity = db.opportunities.find_one({"_id": ObjectId(opportunity_id)})

    # Convert the database object to a Pydantic model
    return Opportunity(**updated_opportunity)

@app.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(opportunity_id: str, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Delete a job or internship opportunity.
    """
    # Check if the user is a recruiter or company owner
    if not is_recruiter_or_company_owner(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only recruiters and company owners can delete opportunities.")

    # Delete the opportunity from the database
    result = db.opportunities.delete_one({"_id": ObjectId(opportunity_id)})

    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    return {"message": "Opportunity deleted successfully."}

@app.post("/opportunities/{opportunity_id}/apply", response_model=dict)
async def apply_for_opportunity(opportunity_id: str, application: CandidateApplication, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Apply for a job or internship opportunity.
    """
    # Check if the current user is not a recruiter or company owner
    if is_recruiter_or_company_owner(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Recruiters and company owners cannot apply for opportunities.")

    # Check if the opportunity exists
    opportunity = db.opportunities.find_one({"_id": ObjectId(opportunity_id)})
    if not opportunity:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    # Insert the application data into the database
    application_data = application.dict()
    application_data["opportunity_id"] = opportunity_id
    application_id = db.applications.insert_one(application_data).inserted_id

    return {"message": "Application submitted successfully.", "application_id": str(application_id)}


@app.get("/opportunities/{opportunity_id}/applications", response_model=List[CandidateApplication])
async def get_opportunity_applications(opportunity_id: str, current_user: Annotated[UserData, Depends(get_current_active_user)]):
    """
    Get a list of candidates who applied for a job or internship opportunity.
    """
    # Check if the current user is a recruiter or company owner
    if not is_recruiter_or_company_owner(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only recruiters and company owners can view applications.")

    # Check if the opportunity exists
    opportunity = db.opportunities.find_one({"_id": ObjectId(opportunity_id)})
    if not opportunity:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    # Retrieve the applications for the opportunity from the database
    applications = [CandidateApplication(**application) for application in db.applications.find({"opportunity_id": opportunity_id})]

    return applications
