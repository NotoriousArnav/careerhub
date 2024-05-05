from fastapi import FastAPI
from argon2 import PasswordHasher
# import argon2.exceptions.VerifyMismatchError
from pymongo import MongoClient
from data_class import *
import os

app = FastAPI()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.careerhub

ph = PasswordHasher()

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
    import json
    obj = db.users.find_one({"resume.basic.email": ud.resume.basic.email})
    ud.password = ph.hash(ud.password)
    data = json.loads(ud.json())
    if not obj:
        user_id = db.users.insert_one(data).inserted_id
        msg = "User added"
    else:
        msg = "User Already exists with this Mail"
    return {
        'message': msg
    }
