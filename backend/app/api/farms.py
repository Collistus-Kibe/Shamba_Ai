from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.models import Farm, User, CropProfile
from app.schemas.schemas import FarmCreate, FarmOut, FarmUpdate, CropProfileCreate, CropProfileOut
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[FarmOut])
def read_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farms = db.query(Farm).filter(Farm.user_id == current_user.id).all()
    return farms

@router.post("/", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(
    farm_in: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farm = Farm(
        user_id=current_user.id,
        name=farm_in.name,
        crop_type=farm_in.crop_type,
        latitude=farm_in.latitude,
        longitude=farm_in.longitude,
        boundary=farm_in.boundary,
        area_hectares=farm_in.area_hectares
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    
    # Auto-seed a default crop profile for this farm
    default_profile = CropProfile(
        farm_id=farm.id,
        crop_name=farm.crop_type,
        status="healthy",
        health_score=92  # Match initial Stitch UI dashboard state
    )
    db.add(default_profile)
    db.commit()
    
    return farm

@router.get("/{farm_id}", response_model=FarmOut)
def read_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found or not owned by you."
        )
    return farm

@router.put("/{farm_id}", response_model=FarmOut)
def update_farm(
    farm_id: int,
    farm_in: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
        
    update_data = farm_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farm, field, value)
        
    db.commit()
    db.refresh(farm)
    return farm

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_444_NOT_FOUND,
            detail="Farm not found."
        )
    db.delete(farm)
    db.commit()
    return None


# --- CROP PROFILE SUB-ROUTES ---

@router.get("/{farm_id}/crops", response_model=List[CropProfileOut])
def read_farm_crops(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check farm ownership
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=404,
            detail="Farm not found or not owned by current user."
        )
        
    crops = db.query(CropProfile).filter(CropProfile.farm_id == farm_id).all()
    return crops

@router.post("/{farm_id}/crops", response_model=CropProfileOut, status_code=status.HTTP_201_CREATED)
def create_farm_crop(
    farm_id: int,
    crop_in: CropProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=404,
            detail="Farm not found or not owned by current user."
        )
        
    crop = CropProfile(
        farm_id=farm_id,
        crop_name=crop_in.crop_name,
        variety=crop_in.variety,
        planting_date=crop_in.planting_date,
        status="healthy",
        health_score=100
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop
