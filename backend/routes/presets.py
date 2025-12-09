"""
User Presets API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db, engine, Base
from models.db_models import UserPreset

router = APIRouter(prefix="/api/user-presets", tags=["User Presets"])


# Pydantic schemas
class PresetConfig(BaseModel):
    currentFollowers: dict
    postsPerWeek: int
    platformAllocation: dict
    contentMix: dict
    preset: str
    months: int
    enablePaid: bool
    paidFunnelBudgetWeek: float
    paidCPM: float
    paidAllocation: dict
    enableBudget: bool
    paidBudgetWeek: float
    creatorBudgetWeek: float
    acquisitionBudgetWeek: float
    cpfMin: float
    cpfMid: float
    cpfMax: float
    valuePerFollower: float
    audienceMix: dict
    selectedPresetId: str


class PresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: PresetConfig


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[PresetConfig] = None


class PresetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    config: dict

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PresetResponse])
async def list_presets(db: Session = Depends(get_db)):
    """Get all saved presets"""
    presets = db.query(UserPreset).order_by(UserPreset.updated_at.desc().nullsfirst(), UserPreset.created_at.desc()).all()
    return presets


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: int, db: Session = Depends(get_db)):
    """Get a specific preset by ID"""
    preset = db.query(UserPreset).filter(UserPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@router.post("/", response_model=PresetResponse)
async def create_preset(preset_data: PresetCreate, db: Session = Depends(get_db)):
    """Create a new preset"""
    preset = UserPreset(
        name=preset_data.name,
        description=preset_data.description,
        config=preset_data.config.dict()
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


@router.put("/{preset_id}", response_model=PresetResponse)
async def update_preset(preset_id: int, preset_data: PresetUpdate, db: Session = Depends(get_db)):
    """Update an existing preset"""
    preset = db.query(UserPreset).filter(UserPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    if preset_data.name is not None:
        preset.name = preset_data.name
    if preset_data.description is not None:
        preset.description = preset_data.description
    if preset_data.config is not None:
        preset.config = preset_data.config.dict()

    db.commit()
    db.refresh(preset)
    return preset


@router.delete("/{preset_id}")
async def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    """Delete a preset"""
    preset = db.query(UserPreset).filter(UserPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    db.delete(preset)
    db.commit()
    return {"message": "Preset deleted successfully"}


@router.get("/health/db")
async def check_db_health():
    """Check if database is configured and connected"""
    if engine is None:
        return {"status": "not_configured", "message": "DATABASE_URL not set"}
    try:
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        return {"status": "connected", "message": "Database is ready"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
