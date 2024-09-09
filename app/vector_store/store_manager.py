import os
import json
import uuid
import faiss
import numpy as np
from typing import List, Dict, Any
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from app.utils.logger import logger

# Initialize embeddings and FAISS index
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
VECTOR_DIM = 1536  # OpenAI embeddings dimension (adjust if different)
FAISS_INDEX_FILE = "faiss_index.index"
METADATA_FILE = "metadata.json"

# Initialize FAISS index and metadata storage
if os.path.exists(FAISS_INDEX_FILE):
    # Load existing index
    index = faiss.read_index(FAISS_INDEX_FILE)
else:
    # Create a new FAISS index
    index = faiss.IndexFlatL2(VECTOR_DIM)

# Metadata dictionary to store document metadata
if os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "r") as f:
        metadata_store = json.load(f)
else:
    metadata_store = {}

def save_faiss_index():
    """Saves the FAISS index and metadata to disk."""
    faiss.write_index(index, FAISS_INDEX_FILE)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata_store, f)

def add_query_to_vector_store(query: str, response: str, metadata: Dict[str, Any]):
    try:
        query_embedding = embeddings.embed_query(query)
        query_embedding = np.array(query_embedding).astype("float32")

        # Generate a unique ID for the query
        query_id = str(uuid.uuid4())

        # Add query to the FAISS index
        index.add(np.array([query_embedding]))

        # Store metadata with the query ID
        metadata_store[query_id] = {
            "query": query,
            "response": response,
            **filter_complex_metadata(metadata)
        }

        # Save the FAISS index and metadata
        save_faiss_index()

        logger.info("Successfully added query and response to vector store.")
    except Exception as e:
        logger.error(f"Error adding query to vector store: {str(e)}")
        raise

def search_similar_queries(query: str, k: int = 1):
    try:
        query_embedding = embeddings.embed_query(query)
        query_embedding = np.array(query_embedding).astype("float32")

        # Perform similarity search
        D, I = index.search(np.array([query_embedding]), k)

        # Retrieve corresponding queries and metadata
        similar_queries = []
        for idx in I[0]:
            if idx < len(metadata_store):
                query_id = list(metadata_store.keys())[idx]
                similar_queries.append(metadata_store[query_id])
        logger.info(f"Successfully found {len(similar_queries)} similar queries.")
        return similar_queries
    except Exception as e:
        logger.error(f"Error searching similar queries: {str(e)}")
        return None

def delete_query_from_vector_store(request_id: str):
    """
    Deletes the query from FAISS and metadata store based on the request_id.
    """
    try:
        if request_id in metadata_store:
            del metadata_store[request_id]

            # Rebuild the FAISS index (FAISS doesn't support dynamic deletion)
            rebuild_faiss_index()

            save_faiss_index()
            logger.info(f"Successfully deleted query with request ID: {request_id}")
        else:
            logger.warning(f"Request ID {request_id} not found in metadata store.")
    except Exception as e:
        logger.error(f"Error deleting query from vector store: {str(e)}")
        raise

def rebuild_faiss_index():
    """Rebuilds the FAISS index after deletion."""
    global index
    index = faiss.IndexFlatL2(VECTOR_DIM)
    for query_id, data in metadata_store.items():
        query_embedding = embeddings.embed_query(data['query'])
        query_embedding = np.array(query_embedding).astype("float32")
        index.add(np.array([query_embedding]))

def delete_all_queries():
    """
    Deletes all queries and resets the FAISS index and metadata.
    """
    try:
        global index, metadata_store
        index.reset()
        metadata_store = {}
        save_faiss_index()
        logger.info("Successfully deleted all queries from vector store.")
    except Exception as e:
        logger.error(f"Error deleting all queries from vector store: {str(e)}")
        raise

def filter_complex_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively filter out metadata types that are not supported for a vector store.
    If metadata contains unsupported types (like dicts or lists), serialize them into JSON strings.
    """
    if isinstance(metadata, dict):
        filtered_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, bool, int, float)):
                filtered_metadata[k] = v
            elif isinstance(v, (dict, list)):
                filtered_metadata[k] = json.dumps(v)  # Serialize dicts and lists as JSON strings
        return filtered_metadata
    return metadata
