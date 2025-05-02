import os
import pymupdf4llm
import tempfile
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv
load_dotenv()
import asyncio
from google import genai
from google.genai import types
from app.utils.prompt import PAPER_EXTRACTION_INSTRUCTIONS
from motor.motor_asyncio import AsyncIOMotorDatabase
import json
from datetime import datetime
from bson.objectid import ObjectId
import re
from app.services.pinecone_service import upsert_json
# Cloudinary Configuration       
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


def parse_json(possibly_cut_json: str) -> dict:
    try:
        return json.loads(possibly_cut_json)
    except json.JSONDecodeError:
        # truncate and repair if cut off at the end of references
        print("Initial JSON parsing failed, attempting to repair...")
        try:
            # Find the start of the "references" array
            references_start = possibly_cut_json.rfind('"references": [')
            if references_start == -1:
                raise ValueError("Could not find 'references' field to recover from.")

            # Keep only up to that point
            references_part = possibly_cut_json[references_start:]
            
            # Find the last complete quoted string in the references
            matches = list(re.finditer(r'"(.*?)"', references_part))
            if not matches:
                raise ValueError("No valid reference entries found.")

            last_valid_ref = matches[-1].group(0)  # e.g. "Author, A. Title..."
            cut_index = possibly_cut_json.rfind(last_valid_ref) + len(last_valid_ref)

            # Build a recovered version
            repaired_json = possibly_cut_json[:cut_index] + "\n    ]\n}\n"

            return json.loads(repaired_json)
        except Exception as e:
            raise ValueError(f"JSON parsing failed and recovery also failed: {e}")
        

# Extract insight from the paper using GEMINI Flash Lite
def extract_insight(file_path: str, fields: list):

     client = genai.Client(
         api_key=os.environ.get("GEMINI_API_KEY"),
     )
     
     print(f"Attempting to upload file: {file_path}")
     uploaded_file = None
     try:
        # Make the file available in local system working directory
        uploaded_file = client.files.upload(file = file_path)
        print(f"File uploaded successfully")
     except Exception as e:
         print(f"Error during file upload: {e}")
         raise

     # Check if upload was successful and returned expected object
     if not uploaded_file or not hasattr(uploaded_file, 'uri') or not hasattr(uploaded_file, 'mime_type'):
         print(f"File upload failed or returned unexpected result: {uploaded_file}")
         raise ValueError("Gemini file upload failed or did not return URI/mime_type.")

     files = [uploaded_file]

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
         ),
        ]
        
     generate_content_config = types.GenerateContentConfig(
         temperature=1.1,
         max_output_tokens=8192,
         response_mime_type="application/json",
         response_schema=genai.types.Schema(
             type = genai.types.Type.OBJECT,
             required = ["title", "authors", "date_published", "metadata", "summary", "references"],
             property_ordering=["title", "authors", "date_published", "metadata", "summary", "references"],
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
         system_instruction=types.Content(
             parts=[types.Part.from_text(text=PAPER_EXTRACTION_INSTRUCTIONS)]
         ),
     )
 
     response = client.models.generate_content(model=model, contents=contents, config=generate_content_config)
     result = response.candidates[0].content.parts[0].text
    
    # parse the result into a json object
     result = parse_json(result)
     return result


# Helper function to create default JSON response when extraction fails
def create_default_json_response(error_message):
    default_response = {
        "title": "Error Processing Document",
        "authors": [{"name": "Unknown", "affiliation": "Unknown", "email": ""}],
        "date_published": "",
        "metadata": {"doi": "", "conference": "", "tags": ["error", "processing_failed"]},
        "summary": {
            "research_problem": f"Error processing this document: {error_message}",
            "objective": "Please try again or upload a different document.",
            "key_findings": "",
            "methods": "",
            "numbers": "",
            "dataset": "",
            "baseline_comparisons": "",
            "limitations": "",
            "future_work": "",
            "novelty_statement": "",
            "user_given_fields": []
        },
        "references": [],
        "image_urls": []  # Empty array for image URLs
    }
    
    return json.dumps(default_response)


# Extract data from the PDF file
async def extract_data(email, file: UploadFile, fields: list, db: AsyncIOMotorDatabase):
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf:
        pdf.write(await file.read())
        pdf_path = pdf.name

    # Process the custom fields from the frontend
    print(f"Processing PDF with custom fields: {fields}")

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
    paper_data = extract_insight(pdf_path, fields)
    
    
    
    # Cleanup
    os.remove(pdf_path)
    
    # Upload the data to MongoDB with the user_email
 
    paper_data["user_email"] = email
    paper_data["created_at"] = datetime.now()
    paper_data["image_urls"] = uploaded_urls  # Store the Cloudinary image URLs

    result = await db["papers"].insert_one(paper_data)

    paper_data["_id"] = str(result.inserted_id)

    # upload the paper data to pinecone
    upsert_json(paper_data, paper_data["_id"])


    return paper_data

async def get_paper(paper_id: str, db: AsyncIOMotorDatabase):
    if not ObjectId.is_valid(paper_id):
        return None
    paper = await db["papers"].find_one({"_id": ObjectId(paper_id)})
    if paper is None:
        return None
    paper["_id"] = str(paper["_id"])
    return paper

async def update_paper_sections(db: AsyncIOMotorDatabase, paper_id: str, sections: dict):
    """
    Update specific sections of a paper in the database.
    
    Args:
        db: Database connection
        paper_id: ID of the paper to update
        sections: Dictionary with section IDs as keys and content as values
    
    Returns:
        Result of the update operation
    """
    if not ObjectId.is_valid(paper_id):
        raise ValueError(f"Invalid paper ID: {paper_id}")
    
    # Process updates
    updates = {}
    user_field_updates = []
    
    for key, content in sections.items():
        if key.startswith("user_field_"):
            # Handle user-given fields updates
            field_name = key.replace("user_field_", "")
            
            # Find if this field exists in user_given_fields array
            paper = await get_paper(paper_id, db)
            if not paper:
                raise ValueError(f"Paper with ID {paper_id} not found")
                
            found = False
            for i, field in enumerate(paper.get("summary", {}).get("user_given_fields", [])):
                if field.get("field_name") == field_name:
                    # Update in user_given_fields array
                    updates[f"summary.user_given_fields.{i}.value"] = content
                    found = True
                    break
            
            if not found:
                # If field doesn't exist, it will be added
                user_field_updates.append({"field_name": field_name, "value": content})
            
        else:
            # Handle standard summary fields
            updates[f"summary.{key}"] = content
    
    # Apply updates
    result = {"acknowledged": False}
    
    if updates:
        result = await db["papers"].update_one(
            {"_id": ObjectId(paper_id)},
            {"$set": updates}
        )
    
    # Add any new user fields
    if user_field_updates:
        await db["papers"].update_one(
            {"_id": ObjectId(paper_id)},
            {"$push": {"summary.user_given_fields": {"$each": user_field_updates}}}
        )
        result["acknowledged"] = True
    
    return result

