import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas, database, agent
from database import engine, get_db

# Create all database tables
models.Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI-First CRM HCP Module")

# Parse FRONTEND_URL to allow multiple origins if comma-separated
frontend_origins = os.environ.get("FRONTEND_URL", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/interactions", response_model=schemas.Interaction)
def create_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = models.InteractionLog(**interaction.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@app.post("/api/chat", response_model=schemas.ChatResponse)
def process_chat(chat_req: schemas.ChatRequest):
    chat_history = [msg.model_dump() for msg in chat_req.chat_history] if chat_req.chat_history else []
    result = agent.run_agent(chat_req.message, chat_req.current_form_state.model_dump(), chat_history)
    
    return schemas.ChatResponse(
        updated_form_state=result["updated_form_state"],
        suggested_follow_ups=result["suggested_follow_ups"],
        reply_message=result.get("reply_message")
    )

@app.get("/api/hcp/{hcp_id}", response_model=schemas.HCPProfileResponse)
def get_hcp(hcp_id: int, db: Session = Depends(get_db)):
    hcp = db.query(models.HCPProfile).filter(models.HCPProfile.id == hcp_id).first()
    if hcp is None:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp

# Dummy endpoint to seed an HCP for testing
@app.post("/api/hcp/seed")
def seed_hcp(db: Session = Depends(get_db)):
    hcp = models.HCPProfile(
        name="Dr. Smith",
        specialty="Cardiology",
        preferred_brand="BrandX",
        sample_restrictions="Max 5 samples per visit"
    )
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp
