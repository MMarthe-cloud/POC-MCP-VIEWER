"""
FastAPI backend for mobile mapping viewer
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_service import MappingAgent
from service import MappingService

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Mobile Mapping Viewer API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent (in production, would be per-session)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable not set")

agent = MappingAgent(GROQ_API_KEY)


class AskRequest(BaseModel):
    question: str


@app.get("/")
def read_root():
    return {"status": "ok", "service": "mobile-mapping-viewer"}


@app.get("/campaign")
def get_campaign():
    """Get the current campaign data"""
    campaign = MappingService.get_campaign()
    return campaign.model_dump()


@app.post("/ask")
def ask_question(request: AskRequest):
    """
    Ask a question to the AI agent
    Returns: answer text + map commands to execute
    """
    try:
        result = agent.ask(request.question)
        return result
    except Exception as e:
        import traceback
        print(f"Error in ask_question: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
def clear_conversation():
    """Clear conversation history"""
    agent.clear_history()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

