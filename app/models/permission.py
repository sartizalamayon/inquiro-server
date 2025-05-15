from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


AccessLevel = Literal["scan", "modify", "control"]

class PermissionDoc(BaseModel):
    id: str = Field(..., alias="_id")
    collection_id: str
    user_email: str
    access_level: AccessLevel
    granted_by: str
    granted_at: datetime


class PermissionCreate(BaseModel):
    collection_id: str
    user_email: str
    access_level: AccessLevel
    granted_by: str

class PermissionUpdate(BaseModel):
    access_level: AccessLevel
    granted_by: str       # email of user making the change

class UserSummary(BaseModel):
    name: str
    email: str
    access_level: AccessLevel
