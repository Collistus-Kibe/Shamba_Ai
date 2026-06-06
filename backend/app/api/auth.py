from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.session import get_db
from app.core.config import settings
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    verify_google_token,
    verify_firebase_token
)
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, UserOut, Token, GoogleLoginRequest, FirebaseLoginRequest
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user email is taken
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists in the system."
        )
        
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm maps username -> email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", response_model=Token)
def login_google(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    google_payload = verify_google_token(req.credential)
    if not google_payload:
        raise HTTPException(
            status_code=400,
            detail="Invalid Google credentials."
        )
        
    email = google_payload["email"]
    google_id = google_payload["google_id"]
    
    # Check if user already exists
    user = db.query(User).filter(
        (User.google_id == google_id) | (User.email == email)
    ).first()
    
    if not user:
        # Register user automatically
        user = User(
            email=email,
            full_name=google_payload["full_name"],
            google_id=google_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update google_id if it wasn't linked before
        if not user.google_id:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
            
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/firebase", response_model=Token)
def login_firebase(req: FirebaseLoginRequest, db: Session = Depends(get_db)):
    firebase_payload = verify_firebase_token(req.id_token)
    if not firebase_payload:
        raise HTTPException(
            status_code=400,
            detail="Invalid Firebase credentials."
        )
        
    email = firebase_payload["email"]
    firebase_uid = firebase_payload["firebase_uid"]
    
    user = db.query(User).filter(
        (User.firebase_uid == firebase_uid) | (User.email == email)
    ).first()
    
    if not user:
        user = User(
            email=email,
            full_name=req.full_name or firebase_payload.get("full_name"),
            firebase_uid=firebase_uid
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
            db.commit()
            db.refresh(user)
            
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
