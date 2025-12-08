from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """User domain model for MongoDB storage."""
    id: str
    email_address: str
    hashed_password: str
    authority: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )