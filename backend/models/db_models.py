"""
SQLAlchemy database models for user presets
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class UserPreset(Base):
    """User-saved configuration presets"""
    __tablename__ = "user_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Store all configuration as JSON for flexibility
    config = Column(JSON, nullable=False)

    # Config structure:
    # {
    #   "currentFollowers": {"Instagram": 385400, "TikTok": 574200, ...},
    #   "postsPerWeek": 40,
    #   "platformAllocation": {"Instagram": 35, "TikTok": 35, ...},
    #   "contentMix": {...},
    #   "preset": "Emerging Platform Play",
    #   "months": 12,
    #   "enablePaid": true,
    #   "paidFunnelBudgetWeek": 600,
    #   "paidCPM": 5,
    #   "paidAllocation": {...},
    #   "enableBudget": true,
    #   "paidBudgetWeek": 1250,
    #   "creatorBudgetWeek": 0,
    #   "acquisitionBudgetWeek": 0,
    #   "cpfMin": 0.10,
    #   "cpfMid": 0.15,
    #   "cpfMax": 0.20,
    #   "valuePerFollower": 0.20,
    #   "audienceMix": {"parents": 80, "gifters": 10, "collectors": 10},
    #   "selectedPresetId": "emerging_platforms"
    # }
