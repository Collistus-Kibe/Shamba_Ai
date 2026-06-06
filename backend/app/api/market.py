from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database.session import get_db
from app.models.models import MarketPrice, User
from app.schemas.schemas import MarketPriceOut
from app.api.deps import get_current_user
from app.services.market_service import MarketService

router = APIRouter()

@router.get("/prices", response_model=List[MarketPriceOut])
def read_prices(
    crop: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Auto-seed if database is empty to make it immediately operational
    MarketService.seed_prices_if_empty(db)
    
    prices = MarketService.get_prices(db, crop=crop, region=region)
    return prices

@router.get("/crops", response_model=List[str])
def get_available_crops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    MarketService.seed_prices_if_empty(db)
    
    crops = db.query(MarketPrice.crop).distinct().all()
    # Flatten list of tuples
    return [c[0] for c in crops]

@router.get("/regions", response_model=List[str])
def get_available_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    MarketService.seed_prices_if_empty(db)
    
    regions = db.query(MarketPrice.region).distinct().all()
    return [r[0] for r in regions]

@router.get("/best-market", response_model=MarketPriceOut)
def get_best_market(
    crop: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    MarketService.seed_prices_if_empty(db)
    
    # Get the market with the highest price for the given crop
    best = db.query(MarketPrice).filter(
        MarketPrice.crop.ilike(f"%{crop}%")
    ).order_by(MarketPrice.current_price.desc()).first()
    
    if not best:
        raise HTTPException(
            status_code=404,
            detail=f"No market price found for crop '{crop}'."
        )
    return best
