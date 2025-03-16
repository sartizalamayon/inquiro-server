from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import os
from app.services import paper_service
from typing import List


router = APIRouter(
    prefix="/paper",
    tags=["pdf"],
    responses={404: {"description": "Not found"}},
)

@router.post('/extract-pdf')
async def extract_text(pdf: UploadFile = File(...), fields: List[str] = Form([])):
    print(fields)
    extract_data = await paper_service.extract_data(pdf, fields)
    return {"data": extract_data}
    