from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .database import Base

class HealthCheck(Base):
    __tablename__ = "health_checks"
    Check_Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    file_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
