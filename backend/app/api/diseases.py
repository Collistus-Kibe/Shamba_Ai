import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models.models import DiseaseReport, User, Farm, Notification
from app.schemas.schemas import DiseaseReportOut, DiseaseReportCreate
from app.api.deps import get_current_user
from app.services.disease_detection import DiseaseDetectionService

router = APIRouter()

# Local upload directory setup
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/diagnose", response_model=DiseaseReportOut, status_code=status.HTTP_201_CREATED)
async def diagnose_crop(
    image: UploadFile = File(...),
    crop_type: Optional[str] = Form(None),
    farm_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If farm_id is provided, verify ownership
    farm = None
    if farm_id:
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
        if not farm:
            raise HTTPException(
                status_code=404,
                detail="Linked farm not found or not owned by you."
            )
        # Auto-infer crop type if not explicitly passed
        if not crop_type:
            crop_type = farm.crop_type

    # Read image content
    image_bytes = await image.read()
    
    # Run the diagnostics pipeline (Gemini Vision or local fallback)
    mime_type = image.content_type or "image/jpeg"
    diagnosis = await DiseaseDetectionService.diagnose_crop_image(
        image_bytes=image_bytes,
        crop_type=crop_type,
        mime_type=mime_type
    )

    # Save uploaded file locally
    file_ext = os.path.splitext(image.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(image_bytes)
    except Exception as e:
        print(f"Failed to write image file: {e}")
        # Keep going with a mock URL if write fails
        unique_filename = "placeholder.jpg"

    # Relative path for image access
    image_url = f"/static/uploads/{unique_filename}"

    # Save report to Database
    report = DiseaseReport(
        farm_id=farm_id,
        image_url=image_url,
        crop_type=crop_type or "Unknown",
        disease_name=diagnosis["disease_name"],
        confidence=diagnosis["confidence"],
        severity=diagnosis["severity"],
        symptoms=diagnosis["symptoms"],
        causes=diagnosis["causes"],
        treatment_commercial=diagnosis["treatment_commercial"],
        treatment_local=diagnosis["treatment_local"],
        treatment_traditional=diagnosis["treatment_traditional"],
        prevention=diagnosis["prevention"]
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)

    # Trigger a warning notification if severity is high
    if report.severity.lower() in ["medium", "high"]:
        alert_title = f"High Risk: {report.disease_name} Detected" if report.severity.lower() == "high" else f"Alert: {report.disease_name} Detected"
        notif = Notification(
            user_id=current_user.id,
            type="disease",
            title=alert_title,
            message=(
                f"A diagnosis run on your {report.crop_type or 'crop'} has flagged an active infection of "
                f"{report.disease_name} with {report.severity} severity. Please review treatments immediately."
            ),
            is_read=False
        )
        db.add(notif)
        db.commit()

    return report

@router.get("/reports", response_model=List[DiseaseReportOut])
def read_reports(
    farm_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DiseaseReport).join(Farm, DiseaseReport.farm_id == Farm.id, isouter=True)
    
    # Filter by user ownership (if linked to a farm)
    query = query.filter((Farm.user_id == current_user.id) | (DiseaseReport.farm_id == None))
    
    if farm_id:
        query = query.filter(DiseaseReport.farm_id == farm_id)
        
    reports = query.order_by(DiseaseReport.created_at.desc()).all()
    return reports

@router.get("/reports/{report_id}", response_model=DiseaseReportOut)
def read_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(DiseaseReport).filter(DiseaseReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Disease report not found."
        )
        
    # Check ownership if farm is linked
    if report.farm_id:
        farm = db.query(Farm).filter(Farm.id == report.farm_id, Farm.user_id == current_user.id).first()
        if not farm:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this report."
            )
            
    return report
