from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models.models import ChatConversation, ChatMessage, User, Farm, EnvironmentalReport
from app.schemas.schemas import (
    ChatConversationOut, 
    ChatConversationCreate, 
    ChatMessageOut, 
    ChatMessageCreate
)
from app.api.deps import get_current_user
from app.services.ai_service import AIService
from app.services.environment_service import EnvironmentService

router = APIRouter()

@router.get("/conversations", response_model=List[ChatConversationOut])
def read_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    convs = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.updated_at.desc()).all()
    return convs

@router.post("/conversations", response_model=ChatConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ChatConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = ChatConversation(
        user_id=current_user.id,
        title=conv_in.title,
        farm_id=conv_in.farm_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/conversations/{conversation_id}", response_model=ChatConversationOut)
def read_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(
            status_code=404,
            detail="Conversation session not found."
        )
    return conv

@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageOut)
async def post_message(
    conversation_id: int,
    msg_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    conv = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(
            status_code=404,
            detail="Conversation session not found."
        )

    # Save User message
    user_msg = ChatMessage(
        conversation_id=conversation_id,
        sender="user",
        message_text=msg_in.message_text
    )
    db.add(user_msg)
    
    # Gather Farm details for AI context if linked
    farm_context = None
    if conv.farm_id:
        farm = db.query(Farm).filter(Farm.id == conv.farm_id).first()
        if farm:
            # Fetch most recent environmental report
            env = db.query(EnvironmentalReport).filter(
                EnvironmentalReport.farm_id == farm.id
            ).order_by(EnvironmentalReport.created_at.desc()).first()
            
            # Default mock metrics if no report exists
            if not env:
                metrics = await EnvironmentService.get_current_metrics(farm.latitude, farm.longitude)
            else:
                metrics = {
                    "temperature": env.temperature,
                    "humidity": env.humidity,
                    "rainfall": env.rainfall,
                    "soil_moisture": env.soil_moisture
                }
                
            farm_context = {
                "name": farm.name,
                "crop_type": farm.crop_type,
                "latitude": farm.latitude,
                "longitude": farm.longitude,
                "temperature": metrics.get("temperature"),
                "humidity": metrics.get("humidity"),
                "rainfall": metrics.get("rainfall"),
                "soil_moisture": metrics.get("soil_moisture"),
                "health_score": 92  # Default standard health index
            }

    # Fetch previous messages in this conversation for history
    previous_messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    history_list = []
    for m in previous_messages:
        history_list.append({
            "sender": m.sender,
            "message_text": m.message_text
        })

    # Call AI generation service
    ai_reply_text = await AIService.generate_response(
        message=msg_in.message_text,
        history=history_list,
        farm_context=farm_context
    )

    # Save AI message
    ai_msg = ChatMessage(
        conversation_id=conversation_id,
        sender="assistant",
        message_text=ai_reply_text
    )
    db.add(ai_msg)
    
    # Update conversation updated timestamp
    from datetime import datetime
    conv.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ai_msg)
    return ai_msg

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(
            status_code=404,
            detail="Conversation session not found."
        )
    db.delete(conv)
    db.commit()
    return None

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Mock endpoint for speech-to-text. In production, this can hook into OpenAI Whisper,
    Google Speech-to-Text, or local sound processing scripts.
    """
    # Simply inspect the filename or return a template transcription prompt
    filename = audio.filename.lower()
    transcription = "How can I improve the crop health on my farm today?"
    
    if "water" in filename or "irrigate" in filename:
        transcription = "Do my crops require watering right now?"
    elif "disease" in filename or "leaf" in filename:
        transcription = "I noticed some spots on my crop leaf, can you diagnose this disease?"
    elif "market" in filename or "price" in filename:
        transcription = "What are the latest maize crop prices at Eldoret Central?"
        
    return {
        "text": transcription,
        "filename": audio.filename
    }
