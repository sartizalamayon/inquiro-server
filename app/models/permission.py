from datetime import datetime
from pydantic import BaseModel, Field


class PermissionDoc(BaseModel):
    id: str = Field(..., alias="_id")
    collection_id: str
    user_email: str
    access_level: str      # "scan" | "modify" | "control"
    granted_by: str
    granted_at: datetime


class PermissionCreate(BaseModel):
    collection_id: str
    user_email: str
    access_level: str     # must be "scan"/"modify"/"control"
    granted_by: str
