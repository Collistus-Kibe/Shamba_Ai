from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    google_id = Column(String(255), nullable=True)
    firebase_uid = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    crop_type = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    boundary = Column(JSON, nullable=True)  # Stores GeoJSON boundary polygons: {"type": "Polygon", "coordinates": [...]}
    area_hectares = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="farms")
    crop_profiles = relationship("CropProfile", back_populates="farm", cascade="all, delete-orphan")
    disease_reports = relationship("DiseaseReport", back_populates="farm", cascade="all, delete-orphan")
    environmental_reports = relationship("EnvironmentalReport", back_populates="farm", cascade="all, delete-orphan")
    conversations = relationship("ChatConversation", back_populates="farm")


class CropProfile(Base):
    __tablename__ = "crop_profiles"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)
    planting_date = Column(Date, nullable=True)
    status = Column(String(50), default="healthy")  # healthy, stressed, diseased, harvested
    health_score = Column(Integer, default=100)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    farm = relationship("Farm", back_populates="crop_profiles")


class DiseaseReport(Base):
    __tablename__ = "disease_reports"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=True)
    image_url = Column(String(512), nullable=True)
    crop_type = Column(String(255), nullable=True)
    disease_name = Column(String(255), nullable=False)
    confidence = Column(Float, default=0.0)
    severity = Column(String(50), default="Low")  # Low, Medium, High
    symptoms = Column(Text, nullable=True)
    causes = Column(Text, nullable=True)
    treatment_commercial = Column(Text, nullable=True)
    treatment_local = Column(Text, nullable=True)
    treatment_traditional = Column(Text, nullable=True)
    prevention = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    farm = relationship("Farm", back_populates="disease_reports")


class EnvironmentalReport(Base):
    __tablename__ = "environmental_reports"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rainfall = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=True)
    risk_score = Column(Float, default=0.0)     # Computed value (e.g. 0 to 100)
    stress_score = Column(Float, default=0.0)   # Computed value (e.g. 0 to 100)
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    farm = relationship("Farm", back_populates="environmental_reports")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(255), nullable=False)
    region = Column(String(255), nullable=False)
    market_name = Column(String(255), nullable=False)
    current_price = Column(Float, nullable=False)
    currency = Column(String(10), default="KES")
    price_unit = Column(String(50), default="90kg Bag")
    trend_percentage = Column(Float, default=0.0)
    forecast_info = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conversations")
    farm = relationship("Farm", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(50), nullable=False)  # "user" or "assistant"
    message_text = Column(Text, nullable=False)
    media_url = Column(String(512), nullable=True)
    audio_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # "disease", "weather", "market", "health"
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
