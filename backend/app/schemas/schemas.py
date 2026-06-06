from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# --- AUTH SCHEMAS ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token

class FirebaseLoginRequest(BaseModel):
    id_token: str  # Firebase ID token
    full_name: Optional[str] = None


# --- FARM SCHEMAS ---

class FarmCreate(BaseModel):
    name: str
    crop_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary: Optional[Dict[str, Any]] = None  # GeoJSON polygon/multipolygon
    area_hectares: Optional[float] = None

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    crop_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary: Optional[Dict[str, Any]] = None
    area_hectares: Optional[float] = None

class FarmOut(BaseModel):
    id: int
    user_id: int
    name: str
    crop_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary: Optional[Dict[str, Any]] = None
    area_hectares: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- CROP PROFILE SCHEMAS ---

class CropProfileCreate(BaseModel):
    crop_name: str
    variety: Optional[str] = None
    planting_date: Optional[date] = None

class CropProfileOut(BaseModel):
    id: int
    farm_id: int
    crop_name: str
    variety: Optional[str] = None
    planting_date: Optional[date] = None
    status: str
    health_score: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- DISEASE REPORT SCHEMAS ---

class DiseaseReportCreate(BaseModel):
    farm_id: Optional[int] = None
    crop_type: Optional[str] = None
    disease_name: str
    confidence: float
    severity: str
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    treatment_commercial: Optional[str] = None
    treatment_local: Optional[str] = None
    treatment_traditional: Optional[str] = None
    prevention: Optional[str] = None

class DiseaseReportOut(BaseModel):
    id: int
    farm_id: Optional[int] = None
    image_url: Optional[str] = None
    crop_type: Optional[str] = None
    disease_name: str
    confidence: float
    severity: str
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    treatment_commercial: Optional[str] = None
    treatment_local: Optional[str] = None
    treatment_traditional: Optional[str] = None
    prevention: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- ENVIRONMENTAL REPORT SCHEMAS ---

class EnvironmentalReportOut(BaseModel):
    id: int
    farm_id: int
    temperature: float
    humidity: float
    rainfall: float
    soil_moisture: float
    wind_speed: Optional[float] = None
    risk_score: float
    stress_score: float
    recommendations: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- MARKET PRICE SCHEMAS ---

class MarketPriceOut(BaseModel):
    id: int
    crop: str
    region: str
    market_name: str
    current_price: float
    currency: str
    price_unit: str
    trend_percentage: float
    forecast_info: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# --- CHAT SCHEMAS ---

class ChatMessageCreate(BaseModel):
    message_text: str

class ChatMessageOut(BaseModel):
    id: int
    conversation_id: int
    sender: str
    message_text: str
    media_url: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatConversationCreate(BaseModel):
    title: str
    farm_id: Optional[int] = None

class ChatConversationOut(BaseModel):
    id: int
    user_id: int
    title: str
    farm_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageOut] = []

    class Config:
        from_attributes = True


# --- NOTIFICATION SCHEMAS ---

class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
