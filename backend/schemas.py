from pydantic import BaseModel
from typing import Optional, List

class InteractionBase(BaseModel):
    hcp_id: Optional[int] = None
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class Interaction(InteractionBase):
    id: int
    class Config:
        from_attributes = True

class HCPProfileResponse(BaseModel):
    id: int
    name: str
    specialty: str
    preferred_brand: str
    sample_restrictions: str
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    current_form_state: InteractionBase
    chat_history: Optional[List[ChatMessage]] = None
    
class ChatResponse(BaseModel):
    updated_form_state: InteractionBase
    suggested_follow_ups: List[str]
    reply_message: Optional[str] = None
