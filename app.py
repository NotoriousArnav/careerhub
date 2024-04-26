"""
# CareerHub FastAPI Backend
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os, json
from supabase import create_client, Client

app = FastAPI()

@app.middleware('http')
async def auth_middleware(request: Request, call_next):
    # Check if 'Authorization' header is present
    if 'Authorization' not in request.headers:
        pass

    # Extract the JWT token from the header
    try:
        token = request.headers['Authorization'].replace('Bearer ', '')
    except:
        token = None
    # Use supabase.auth.get_user(jwt) to get user information
    try:
        user = supabase.auth.get_user(token)
    except:
        user = None
    # Attach the user information to the request state for future use
    request.state.user = user

    # Continue with the request handling
    response = await call_next(request)
    return response

supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

@app.get('/')
async def index(request: Request):
    if request.state.user:
        data = {
            'message': 'Hello',
            'data': json.loads(request.state.user.json())
        }
    else:
        data = {
            'message': 'Hello',
            'data': None
        }
    return JSONResponse(content=data)
