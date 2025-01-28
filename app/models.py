from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from .database import Base

class HealthCheck(Base):
    __tablename__ = "health_checks"
    Check_Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
