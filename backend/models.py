from sqlalchemy import Column, Integer, String, Date, Time, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HCPProfile(Base):
    __tablename__ = "hcp_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialty = Column(String)
    preferred_brand = Column(String)
    sample_restrictions = Column(String)
    has_sample_restrictions = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    monthly_sample_limit = Column(Integer, default=0)

class SampleDistributionLog(Base):
    __tablename__ = "sample_distribution_logs"
    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcp_profiles.id"), index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    quantity = Column(Integer)
    date = Column(String) # Storing as YYYY-MM-DD string for simplicity

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
