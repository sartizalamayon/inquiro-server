from fastapi import APIRouter, File, UploadFile, HTTPException
import os
from app.services import paper_service


router = APIRouter(
    prefix="/paper",
    tags=["pdf"],
    responses={404: {"description": "Not found"}},
)

@router.post('/extract-pdf')
async def extract_text(pdf: UploadFile = File(...)):
    extract_data = await paper_service.extract_data(pdf)
    return {"data": extract_data}
    