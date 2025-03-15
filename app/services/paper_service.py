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


# Configuration       
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


def extract_references(text):
    # Find the References Section
    reference_keywords = r"(References|REFERENCES|Bibliography|Citations)"
    match = re.search(reference_keywords, text, re.IGNORECASE)
    
    if not match:
        return []  # No references section found

    # Extract text after the found reference heading
    ref_section_start = match.end()  # Start after "References"
    ref_text = text[ref_section_start:].strip()

    return ref_text



PROMPT = """
You are an expert researcher tasked with analyzing a research paper and distilling its key insights into a structured JSON format. Your goal is to provide an expert-level synthesis that goes beyond simple text extraction. You will receive an input JSON containing the extracted research paper and additional field hints. Analyze the paper thoroughly and output a JSON that exactly follows the schema below. For each field, extract or infer the most relevant information. If any field or section is missing or empty, use the appropriate empty value as specified.

Input Format:
The input will be a JSON object with the following keys:
{
    "data": "Extracted research paper",
    "Fileds": "Use given fields, e.g., 'Goal of the Research', 'Overall Summary', etc."
}
- The `data` key contains the full text of the research paper.
- The `Fileds` key provides guidance on specific fields or aspects to pay attention to.

Schema:
{
    "title": "string",
    "authors": [{
        "name": "string",
        "affiliation": "string",
        "email": "string"
    }],
    "date_published": "Date",
    "metadata": {
      "doi": "string",                   // Unique identifier; if not found, use an empty string ""
      "conference": "string",            // Conference name; if not applicable, use an empty string ""
      "tags": ["string"]                 // Keywords or tags; if none, return an empty array []
    },
    "summary": {
      "research_problem": "string",      // Summarize the core research problem
      "objective": "string",             // Outline the main objective or goal of the study
      "key_findings": "string",          // Highlight the most critical results and insights
      "methods": "string",               // Describe the methodologies or approaches used
      "numbers": "string",               // Include key numerical or statistical results
      "dataset": "string",               // Identify the dataset(s) used or referenced
      "baseline_comparisons": "string",  // Detail any comparisons with baseline methods
      "limitations": "string",           // Summarize any limitations mentioned in the study
      "future_work": "string",           // Outline suggestions for future research
      "novelty_statement": "string",     // Explain what is novel about the work and how it advances the field
      "Others": [{
        "filed": "string",               // Additional field name for insights that do not fit the above categories
        "value": "string"                // Corresponding markdown-formatted value
      }]
    },
    "references": ["string"]             // List all cited references; if none, return an empty array []
}

Formatting Requirements for Summary Fields:
- Every value in the summary object must be output in markdown format using only the following markdown elements:
    1. Headings (using `#`)
    2. Bullet lists (using `-` only)
    3. Tables
    4. Code blocks (using triple backticks)
    5. Inline code (using single backticks)
- Ensure that the markdown formatting is concise, clear, and relevant to the research paper.

Instructions for Extraction:
1. **Title:** Identify the research paper's title. If not found, return an empty string "".
2. **Authors:** Extract a list of authors along with their affiliation and email. For any missing details, use an empty string "".
3. **Date Published:** Determine the publication date. If missing or unclear, return an empty string "".
4. **Metadata:** 
   - **DOI:** Provide the DOI if available; otherwise, return an empty string "".
   - **Conference:** If applicable, note the conference name; if not, return an empty string "".
   - **Tags:** Extract keywords or tags that summarize the content; if none exist, return an empty array [].
5. **Summary:** 
   - **Research Problem:** Identify and summarize the core research problem.
   - **Objective:** Clearly outline the goal or purpose of the study.
   - **Key Findings:** Distill the main results and insights that the research delivers.
   - **Methods:** Summarize the experimental or analytical methodologies used.
   - **Numbers:** Highlight any important numerical results, such as performance metrics or statistical significance.
   - **Dataset:** Specify the dataset(s) referenced or used in the research.
   - **Baseline Comparisons:** Describe any comparisons made with baseline or previous methods.
   - **Limitations:** Note any limitations or weaknesses acknowledged in the study.
   - **Future Work:** Extract any proposals or recommendations for future research directions.
   - **Novelty Statement:** Articulate the novel contributions of the research and how it advances the field.
   - **Others:** For any additional insights or relevant details that do not neatly fit into the above categories, include them here as objects with "filed" and "value". If there are no additional insights, return an empty array [].
   - **Note:** Every text under these fields must be provided in markdown format using only the allowed markdown elements.
6. **References:** List all reference entries from the paper. If no references are present, return an empty array [].

Edge Cases and Error Handling:
- **Missing or Empty Fields:** For any key or section not found in the paper, return the appropriate empty value: an empty string "" for text fields, an empty array [] for lists, or an empty object {} for objects.
- **Ambiguity:** If information is ambiguous or conflicting, select the option that is most clearly supported by the text.
- **Expert Synthesis:** Avoid simple text extraction. Instead, interpret and synthesize the content as an expert researcher, ensuring that the final output is insightful and well-organized.
- **Output Format:** Ensure that the final output is valid JSON strictly following the provided schema.


"""

async def extract_data(file: UploadFile):
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf:
        pdf.write(await file.read())
        pdf_path = pdf.name

    # Create temporary directory for images
    with tempfile.TemporaryDirectory() as temp_dir:

        # Extract markdown with images
        md_text = pymupdf4llm.to_markdown(pdf_path, write_images=True, image_path=temp_dir)

        doc = pymupdf.open(pdf_path)
        md_text = ""
        for page in doc:
            md_text += page.get_text()
        doc.close()

        # Upload images asynchronously
        image_paths = [os.path.join(temp_dir, img) for img in os.listdir(temp_dir)]
        upload_tasks = [asyncio.to_thread(cloudinary.uploader.upload, img) for img in image_paths]
        uploaded_images = await asyncio.gather(*upload_tasks)
        uploaded_urls = [img["secure_url"] for img in uploaded_images]


    # We now have the image urls, now we need to start with text
    # Extract the references

   
    # Cleanup
    os.remove(pdf_path)
    

    return {"text": md_text, "images": uploaded_urls}

