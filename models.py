from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class EventCreate(BaseModel):
    name: str
    event_date: str
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Le nom de l\'événement est requis')
        return v.strip()

class GuestAdd(BaseModel):
    first_name: str
    last_name: str
    table_number: str
    notes: Optional[str] = ""
    
    @validator('first_name', 'last_name')
    def name_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Le nom et prénom sont requis')
        return v.strip().upper()

class GuestBatch(BaseModel):
    guests: List[GuestAdd]

class CheckinRequest(BaseModel):
    guest_id: int