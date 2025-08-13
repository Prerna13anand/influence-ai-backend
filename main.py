# --- Imports ---
from fastapi import FastAPI, Depends, Security 
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import os
from fastapi.responses import RedirectResponse
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Import from our other project files
import models
import schemas
import crud
from database import SessionLocal, engine

# AI-related imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# --- App and DB Setup ---
# Create all database tables defined in models.py
models.Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(
    title="Influence OS AI Intern Project",
    description="API for generating LinkedIn content using Google Gemini.",
)
# NEW: Define the security scheme
security = HTTPBearer()

# CORS middleware configuration to allow frontend communication
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- AI Setup ---
# Initialize the Google Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")

# Create the prompt template
prompt = ChatPromptTemplate.from_template(
    "You are an expert LinkedIn copywriter. Your goal is to create an engaging post."
    "\n\n"
    "Write a LinkedIn post for a person whose professional role is '{role}'."
    " The post should be about the topic: '{topic}'."
    " The tone of the post must be {tone}."
    "\n\n"
    "Please include 3-5 relevant hashtags in your response."
)

# Create the processing chain using LangChain Expression Language (LCEL)
chain = prompt | llm | StrOutputParser()


# --- Pydantic Models for Requests ---
# Defines the expected data for creating a post
class PostRequest(BaseModel):
    role: str
    topic: str
    tone: str = "professional"

# NEW: Defines the expected data for sharing a post
class ShareRequest(BaseModel):
    post_text: str


# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"status": "Influence OS API is running."}


# NEW ENDPOINT TO GET ALL POSTS
@app.get("/posts", response_model=List[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of all posts from the database.
    """
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts
# --- LINKEDIN AUTHENTICATION ENDPOINTS ---

@app.get("/auth/linkedin")
async def login_via_linkedin():
    """
    Redirects the user to LinkedIn's authorization page.
    """
    # The required permissions (scopes) for your app
    scope = "profile openid email w_member_social"

    # The URL the user will be sent to on LinkedIn
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={os.getenv('LINKEDIN_CLIENT_ID')}"
        f"&redirect_uri=http://127.0.0.1:8000/auth/linkedin/callback"
        f"&scope={scope}"
    )
    return RedirectResponse(url=linkedin_auth_url)
@app.get("/users/me")
async def get_user_profile(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Uses the access token to fetch the user's LinkedIn profile.
    """
    access_token = credentials.credentials
    profile_url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(profile_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch profile", "details": response.text}

# --- NEW ENDPOINT TO SHARE A POST ON LINKEDIN ---
@app.post("/posts/share")
async def share_post_on_linkedin(
    request: ShareRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Shares a post on behalf of the authenticated user.
    This function gets the user's URN, constructs a share payload,
    and posts it to the LinkedIn API.
    """
    access_token = credentials.credentials

    # 1. First, we need to get the user's unique LinkedIn ID (URN)
    profile_url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        profile_response = await client.get(profile_url, headers=headers)

    if profile_response.status_code != 200:
        return {"error": "Could not fetch user profile to get author URN"}

    user_urn = profile_response.json()["sub"] # The user's ID is in the 'sub' field

    # 2. Now, construct the request body for the share API
    share_url = "https://api.linkedin.com/v2/posts"
    share_payload = {
        "author": f"urn:li:person:{user_urn}",
        "commentary": request.post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    # 3. Make the POST request to share the content
    async with httpx.AsyncClient() as client:
        share_response = await client.post(share_url, headers=headers, json=share_payload)

    if share_response.status_code == 201: # 201 Created means success
        return {"message": "Post shared successfully on LinkedIn!"}
    else:
        return {"error": "Failed to share post", "details": share_response.json()}


@app.get("/auth/linkedin/callback")
async def linkedin_callback(code: str):
    """
    Handles the callback from LinkedIn after user authorization.
    Exchanges the authorization code for an access token, then
    redirects the user back to the frontend with the token.
    """
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = "http://127.0.0.1:8000/auth/linkedin/callback"

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        # NEW: Redirect to the frontend with the token in the URL
        frontend_url = f"http://localhost:3000?token={access_token}"
        return RedirectResponse(url=frontend_url)
    else:
        # If it fails, redirect to the frontend with an error message
        return RedirectResponse(url="http://localhost:3000?error=auth_failed")



@app.post("/generate-post", response_model=schemas.Post)
def generate_post(request: PostRequest, db: Session = Depends(get_db)):
    """
    Generates a LinkedIn post and saves it to the database.
    """
    generated_text = chain.invoke({
        "role": request.role,
        "topic": request.topic,
        "tone": request.tone
    })

    # Create a new Post object and save it to the database
    db_post = models.Post(post_text=generated_text)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return db_post