from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.models import Farm, EnvironmentalReport, User, Notification
from app.schemas.schemas import EnvironmentalReportOut
from app.api.deps import get_current_user
from app.services.environment_service import EnvironmentService

router = APIRouter()

@router.get("/farms/{farm_id}/weather", response_model=EnvironmentalReportOut)
async def get_farm_weather(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership of farm
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=404,
            detail="Farm not found or not owned by you."
        )

    # Call environment service to get current details (fetches weather/simulates based on lat/lon)
    metrics = await EnvironmentService.get_current_metrics(farm.latitude, farm.longitude)

    # Save to history log
    report = EnvironmentalReport(
        farm_id=farm_id,
        temperature=metrics["temperature"],
        humidity=metrics["humidity"],
        rainfall=metrics["rainfall"],
        soil_moisture=metrics["soil_moisture"],
        wind_speed=metrics["wind_speed"],
        risk_score=metrics["risk_score"],
        stress_score=metrics["stress_score"],
        recommendations=metrics["recommendations"]
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Check for critical thresholds to trigger notifications
    if report.soil_moisture < 30:
        notif = Notification(
            user_id=current_user.id,
            type="weather",
            title="Critical Soil Dryness Alert",
            message=(
                f"Soil moisture at your farm '{farm.name}' has dropped to {report.soil_moisture}%. "
                f"Irrigation is urgently recommended to prevent crop wilting."
            ),
            is_read=False
        )
        db.add(notif)
        db.commit()
    elif report.risk_score > 75:
        notif = Notification(
            user_id=current_user.id,
            type="weather",
            title="High Fungal Risk Alert",
            message=(
                f"Current temperature ({report.temperature}°C) and humidity ({report.humidity}%) "
                f"indicate a high fungal infection risk at '{farm.name}'. Inspect leaves for symptoms."
            ),
            is_read=False
        )
        db.add(notif)
        db.commit()

    return report

@router.get("/farms/{farm_id}/weather/history", response_model=List[EnvironmentalReportOut])
def get_farm_weather_history(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership of farm
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=404,
            detail="Farm not found or not owned by you."
        )

    history = db.query(EnvironmentalReport).filter(
        EnvironmentalReport.farm_id == farm_id
    ).order_by(EnvironmentalReport.created_at.desc()).limit(30).all()
    
    return history
