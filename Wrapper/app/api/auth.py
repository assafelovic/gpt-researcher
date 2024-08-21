from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/google/login")
async def google_login():
    return RedirectResponse(settings.GOOGLE_AUTH_URL)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    # Get the authorization code from the request
    code = request.query_params.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Create a flow instance to handle the token request
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    # Exchange the authorization code for credentials
    flow.fetch_token(code=code)

    # Get the ID token from the credentials
    id_info = id_token.verify_oauth2_token(
        flow.credentials.id_token, 
        requests.Request(), 
        settings.GOOGLE_CLIENT_ID
    )

    # Extract user information from id_info
    email = id_info.get("email")
    first_name = id_info.get("given_name")
    last_name = id_info.get("family_name")
    
    if not email:
        raise HTTPException(status_code=400, detail="Unable to fetch email from Google account")

    # Check if user exists, if not create a new user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=email.split("@")[0]  # Using email prefix as username
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Set user session
    request.session["user_id"] = user.id

    # Redirect to home page or dashboard
    return RedirectResponse(url="/")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

async def exchange_code_for_token(code: str):
    # Implement token exchange with Google API
    pass

def verify_token(token: str):
    idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
    return idinfo