import json
import logging
import chromadb
from openai import OpenAI
from typing import List, Dict, Any, Optional
from config import config
from models.schemas import Paper

logger = logging.getLogger("ResearchPilot.VectorStore")

# Initialize OpenAI client for AIMALabs embeddings
embedding_client = OpenAI(
    api_key=config.aimlabs_api_key,
    base_url=config.aimlabs_base_url
)

# Initialize ChromaDB persistent client and collection
try:
    chroma_client = chromadb.PersistentClient(path=config.chroma_db_path)
    collection = chroma_client.get_or_create_collection(name="research_papers")
    logger.info(f"Initialized ChromaDB persistent client at: {config.chroma_db_path}")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB: {str(e)}")
    raise e

def get_text_embedding(text: str, is_query: bool = False) -> List[float]:
    """
    Computes text embedding using AIMALabs embedding model (text-embedding-3-small by default).
    """
    try:
        response = embedding_client.embeddings.create(
            model=config.embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error calling AIMALabs Embedding API: {str(e)}")
        # Return dummy embedding of size 1536 (text-embedding-3-small) on error
        return [0.0] * 1536

def store_paper(paper: Paper, embedding: Optional[List[float]] = None) -> str:
    """
    Stores a paper abstract and its metadata in ChromaDB.
    If embedding is not provided, computes it using Gemini Embedding API.
    """
    try:
        # Check if already exists in database
        existing = collection.get(ids=[paper.id])
        if existing and existing.get("ids"):
            logger.info(f"Paper '{paper.id}' already exists in ChromaDB. Skipping insert.")
            return paper.id

        if not embedding:
            logger.info(f"Generating embedding for paper: {paper.id}")
            # If abstract is empty, embed title instead
            embed_text = paper.abstract if paper.abstract.strip() else paper.title
            embedding = get_text_embedding(embed_text, is_query=False)

        # ChromaDB metadata must have primitive types (str, int, float, bool)
        metadata = {
            "title": paper.title,
            "authors": json.dumps(paper.authors),
            "year": paper.year if paper.year is not None else -1,
            "source": paper.source,
            "citation_count": paper.citation_count,
            "external_url": paper.external_url or ""
        }

        collection.add(
            ids=[paper.id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[paper.abstract or paper.title]
        )
        logger.info(f"Successfully stored paper '{paper.id}' in ChromaDB.")
        return paper.id
    except Exception as e:
        logger.error(f"Error storing paper '{paper.id}' in ChromaDB: {str(e)}")
        return paper.id

def retrieve_relevant_papers(sub_question: str, top_k: int = 5) -> List[Paper]:
    """
    Performs semantic search over ChromaDB for relevant papers based on a sub-question.
    """
    papers = []
    try:
        logger.info(f"Querying vector store for: '{sub_question}' (top_k={top_k})")
        
        # Check if collection is empty
        if collection.count() == 0:
            logger.warning("Vector store collection is empty. Cannot retrieve papers.")
            return papers

        query_embedding = get_text_embedding(sub_question, is_query=True)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count())
        )
        
        if results and results.get("ids"):
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            documents = results["documents"][0]
            
            for i in range(len(ids)):
                meta = metadatas[i]
                try:
                    authors_list = json.loads(meta.get("authors", "[]"))
                except Exception:
                    authors_list = []
                    
                year_val = meta.get("year", -1)
                
                papers.append(
                    Paper(
                        id=ids[i],
                        title=meta.get("title", "Untitled"),
                        authors=authors_list,
                        year=year_val if year_val != -1 else None,
                        abstract=documents[i] or "",
                        source=meta.get("source", "unknown"),
                        citation_count=meta.get("citation_count", 0),
                        external_url=meta.get("external_url", None) or None
                    )
                )
                
    except Exception as e:
        logger.error(f"Error retrieving papers from ChromaDB: {str(e)}")
        
    return papers
