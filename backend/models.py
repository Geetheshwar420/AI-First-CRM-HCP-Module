from sqlalchemy import Column, Integer, String, Date, Time, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HCPProfile(Base):
    __tablename__ = "hcp_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialty = Column(String)
    preferred_brand = Column(String)
    sample_restrictions = Column(String)

class InteractionLog(Base):
    __tablename__ = "interaction_logs"
    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, index=True)
    interaction_type = Column(String)
    date = Column(String)
    time = Column(String)
    attendees = Column(String)
    topics_discussed = Column(Text)
    materials_shared = Column(String)
    samples_distributed = Column(String)
    sentiment = Column(String)
    outcomes = Column(Text)
    follow_up_actions = Column(Text)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, index=True)
    interaction_id = Column(Integer, index=True)
    description = Column(String)
    due_date = Column(String)
    status = Column(String)
