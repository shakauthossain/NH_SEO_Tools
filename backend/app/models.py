from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    audits = relationship("Audit", back_populates="owner")
    jobs = relationship("BulkJob", back_populates="owner")

class Audit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    url = Column(String, nullable=False)
    seo_score = Column(String, default="N/A")
    speed_score = Column(String, default="N/A")
    report_id = Column(String, unique=True, index=True)
    full_results = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="audits")

class BulkJob(Base):
    __tablename__ = "bulk_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_filename = Column(String, nullable=False)
    output_filename = Column(String, nullable=True)
    status = Column(String, default="pending")
    total_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="jobs")
