from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.models import Notification, User
from app.schemas.schemas import NotificationOut
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[NotificationOut])
def read_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return notifs

@router.put("/{notif_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )
        
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

@router.put("/read-all", response_model=List[NotificationOut])
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).all()
    
    for n in notifs:
        n.is_read = True
        
    db.commit()
    
    # Return all notifications
    return db.query(Notification).filter(Notification.user_id == current_user.id).all()

@router.delete("/{notif_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )
        
    db.delete(notif)
    db.commit()
    return None
