import os
import pymupdf4llm
import tempfile
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv
load_dotenv()
import pathlib
import pymupdf
import asyncio
import re
import base64
from google import genai
from google.genai import types
from app.utils.prompt import PAPER_EXTRACTION_INSTRUCTIONS

# Cloudinary Configuration       
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Extract insight from the paper using GEMINI Flash Lite
def extract_insight(file_path: str, fields: list):
    print(fields)
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
    files = [
        # Make the file available in local system working directory
        client.files.upload(file = file_path), 
    ]
    model = "gemini-2.0-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text=f"User_given_fields = {fields}"),
            ],
        ),]
    generate_content_config = types.GenerateContentConfig(
        temperature=1.1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["title", "authors", "date_published", "metadata", "summary", "references"],
            properties = {
                "title": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "authors": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["name", "affiliation", "email"],
                        properties = {
                            "name": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "affiliation": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "email": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
                "date_published": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "metadata": genai.types.Schema(
                    type = genai.types.Type.OBJECT,
                    required = ["doi", "conference", "tags"],
                    properties = {
                        "doi": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "conference": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "tags": genai.types.Schema(
                            type = genai.types.Type.ARRAY,
                            items = genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        ),
                    },
                ),
                "summary": genai.types.Schema(
                    type = genai.types.Type.OBJECT,
                    required = ["research_problem", "objective", "key_findings", "methods", "numbers", "dataset", "baseline_comparisons", "limitations", "future_work", "novelty_statement", "user_given_fields"],
                    properties = {
                        "research_problem": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "objective": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "key_findings": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "methods": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "numbers": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "dataset": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "baseline_comparisons": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "limitations": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "future_work": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "novelty_statement": genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                        "user_given_fields": genai.types.Schema(
                            type = genai.types.Type.ARRAY,
                            items = genai.types.Schema(
                                type = genai.types.Type.OBJECT,
                                properties = {
                                    "filed_name": genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                    "value": genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                },
                            ),
                        ),
                    },
                ),
                "references": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text=PAPER_EXTRACTION_INSTRUCTIONS),
        ],
        )

    response = client.models.generate_content(model=model, contents=contents, config=generate_content_config)
    result = response.candidates[0].content.parts[0].text

    return result


# Extract data from the PDF file
async def extract_data(file: UploadFile, fields: list):
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf:
        pdf.write(await file.read())
        pdf_path = pdf.name

    # Create temporary directory for images
    with tempfile.TemporaryDirectory() as temp_dir:

        # Extract markdown with images
        md_text = pymupdf4llm.to_markdown(pdf_path, write_images=True, image_path=temp_dir)

        # Upload images asynchronously
        image_paths = [os.path.join(temp_dir, img) for img in os.listdir(temp_dir)]
        upload_tasks = [asyncio.to_thread(cloudinary.uploader.upload, img) for img in image_paths]
        uploaded_images = await asyncio.gather(*upload_tasks)
        uploaded_urls = [img["secure_url"] for img in uploaded_images]


    # Extract the references
    print(pdf_path)
    data = extract_insight(pdf_path, fields)
    
   
    # Cleanup
    os.remove(pdf_path)
    
    return data

