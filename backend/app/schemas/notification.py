from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    count: int
    unread_count: Optional[int] = None


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str  # attendance, low_attendance, enrollment, system, reminder
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
