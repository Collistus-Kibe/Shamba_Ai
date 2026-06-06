from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database.session import get_db
from app.core.config import settings
from app.core.security import verify_token, verify_firebase_token
from app.models.models import User
from app.schemas.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Try to decode local JWT first
    payload = verify_token(token)
    
    user_id = None
    email = None
    
    if payload:
        user_id_str = payload.get("sub")
        if user_id_str:
            user_id = int(user_id_str)
    else:
        # 2. Try to decode as Firebase ID Token
        firebase_payload = verify_firebase_token(token)
        if firebase_payload:
            email = firebase_payload.get("email")
            firebase_uid = firebase_payload.get("firebase_uid")
            
            # Check if user already exists locally by firebase_uid or email
            user = db.query(User).filter(
                (User.firebase_uid == firebase_uid) | (User.email == email)
            ).first()
            
            if not user:
                # Auto-create local user profile for Firebase accounts
                user = User(
                    email=email,
                    full_name=firebase_payload.get("full_name"),
                    firebase_uid=firebase_uid
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            return user
            
    if user_id is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user
