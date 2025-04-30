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
    # 3a. Build the text blob from your summary fields
    text = (
        paper_data["title"] +
        str(paper_data["authors"]) +
        paper_data["summary"]["research_problem"] +
        paper_data["summary"]["objective"] +
        paper_data["summary"]["key_findings"] +
        paper_data["summary"]["methods"] +
        "Date published" + str(paper_data["date_published"])

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
        results = await index.search(
            namespace=namespace,
            top_k=20,
            include_metadata=True,
            text=query
        )
        print(results)
        return results
    except Exception as e:
        print("Search failed:", e)
        return None

