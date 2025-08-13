# InfluenceAI - Backend

This is the backend for the InfluenceAI project, an autonomous AI agent for generating and posting LinkedIn content. This project was created for the Influence OS AI Intern Assessment.

## Features

* **AI Content Generation:** Creates engaging, professional LinkedIn posts using Google Gemini.
* **Secure LinkedIn Login:** Implements a full OAuth 2.0 flow for secure user authentication.
* **User Profile Analysis:** Fetches and uses a user's LinkedIn profile data.
* **Automated Posting:** Shares generated content directly to a user's LinkedIn feed via the API.
* **Post History:** Stores all generated content in a PostgreSQL database.

## Tech Stack

* **Framework:** Python, FastAPI
* **Database:** PostgreSQL with SQLAlchemy ORM
* **AI Orchestration:** LangChain
* **API Communication:** httpx

---

## Setup and Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/influence-os-backend.git](https://github.com/YOUR_USERNAME/influence-os-backend.git)
cd influence-os-backend
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Note: You will need to create a `requirements.txt` file by running `pip freeze > requirements.txt` in your terminal.)*

### 4. Set Up Environment Variables
This project requires several API keys to function. You must get your own keys from the respective platforms.

Create a new file in the root directory named `.env` and add your keys to it like this:

```
GOOGLE_API_KEY="your_google_api_key_here"
LINKEDIN_CLIENT_ID="your_linkedin_client_id_here"
LINKEDIN_CLIENT_SECRET="your_linkedin_client_secret_here"
```

### 5. Run the Development Server
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## Live Demo

This project is deployed and live.
* **Frontend:** [https://influence-ai-frontend.vercel.app/](https://influence-ai-frontend.vercel.app/)
* **Backend API:** [https://influence-ai-backend.onrender.com/docs](https://influence-ai-backend.onrender.com/docs)