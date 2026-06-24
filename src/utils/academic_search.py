import urllib.parse
import logging
import time
import requests
import arxiv
from typing import List
from src.models.schemas import Paper

logger = logging.getLogger("ResearchPilot.AcademicSearch")

def search_semantic_scholar(query: str, limit: int = 5) -> List[Paper]:
    """
    Searches Semantic Scholar API for relevant papers.
    API documentation: https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_paper_search
    """
    papers = []
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,abstract,citationCount,url"
    }
    
    headers = {
        "User-Agent": "ResearchPilot/1.0 (academic research assistant agent)"
    }
    
    try:
        logger.info(f"Querying Semantic Scholar for: '{query}' (limit={limit})")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 429:
            logger.warning("Semantic Scholar rate limited (429). Retrying after 2 seconds...")
            time.sleep(2)
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            for item in results:
                paper_id = f"semantic_scholar_{item.get('paperId')}"
                authors_list = [author.get("name") for author in item.get("authors", []) if author.get("name")]
                
                papers.append(
                    Paper(
                        id=paper_id,
                        title=item.get("title", "Untitled"),
                        authors=authors_list,
                        year=item.get("year"),
                        abstract=item.get("abstract", "") or "",
                        source="semantic_scholar",
                        citation_count=item.get("citationCount", 0),
                        external_url=item.get("url")
                    )
                )
        else:
            logger.error(f"Semantic Scholar API failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"Error querying Semantic Scholar: {str(e)}")
        
    return papers

def search_arxiv(query: str, limit: int = 5) -> List[Paper]:
    """
    Searches ArXiv API for relevant papers using the official python library.
    """
    papers = []
    try:
        logger.info(f"Querying ArXiv for: '{query}' (limit={limit})")
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = client.results(search)
        for result in results:
            # Generate a clean ID from the arxiv entry ID/URL
            arxiv_raw_id = result.entry_id.split("/abs/")[-1].split("v")[0]
            paper_id = f"arxiv_{arxiv_raw_id}"
            authors_list = [author.name for author in result.authors]
            
            papers.append(
                Paper(
                    id=paper_id,
                    title=result.title,
                    authors=authors_list,
                    year=result.published.year if result.published else None,
                    abstract=result.summary or "",
                    source="arxiv",
                    citation_count=0, # ArXiv does not store citation counts
                    external_url=result.entry_id
                )
            )
    except Exception as e:
        logger.error(f"Error querying ArXiv: {str(e)}")
        
    return papers
