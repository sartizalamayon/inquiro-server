from pinecone import Pinecone
import asyncio
import os

# Initialize a Pinecone client with your API key
pc = Pinecone(os.environ.get("PINECONE_API_KEY"))

# Create a dense index with integrated embedding
index_name = "inquiro"
namespace = "example-namespace"

if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map": {"text": "text"} 
        }
    )

index = pc.Index(index_name)

def upsert_json(paper_data: dict, metadata_id: str):
    """
    Upserts one paper at a time into Pinecone using the integrated embedding.
    """
    print(paper_data)
    # 3a. Build the text blob from your summary fields
    authors_text = ', '.join(
    f"{author['name']} ({author['affiliation']}, {author['email']})"
    for author in paper_data["authors"]
)
    text = (
        paper_data["title"] +
        authors_text +
        paper_data["summary"]["research_problem"] +
        paper_data["summary"]["objective"] +
        paper_data["summary"]["key_findings"] +
        paper_data["summary"]["methods"] +
        "Date published:" + str(paper_data["date_published"]) + paper_data['metadata']['tags']
    )

    print(text)
    print(metadata_id)
    # 3b. Prepare the record in the Quickstart format
    record = {
        "_id": str(metadata_id),         # your record ID
        "text": text,              # Pinecone will embed this field
        "tags": paper_data['metadata']['tags'],
    }
    
    # 3c. Upsert into the specified namespace
    try:
        index.upsert_records(namespace, [record])
        print(f"Upserted {metadata_id}")
    except Exception as e:
        print(f"Upsert failed for {metadata_id}: {e}")
 

async def semantic_search(query: str):
    try:
        results = index.search(
            namespace=namespace,
            query ={
                "top_k" : 20,
                "inputs" : {
                    "text": query
                }
                }
        )
        return results.result.hits
    except:
        return

