# --- Imports ---
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import os

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