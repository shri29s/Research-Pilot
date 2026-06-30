import logging
import asyncio
from typing import List
from models.schemas import Paper
from utils.academic_search import search_semantic_scholar, search_arxiv
from agents.vector_store import store_paper, store_papers_async
from config import config

logger = logging.getLogger("ResearchPilot.RetrieverAgent")

class RetrieverAgent:
    """Agent responsible for querying external academic sources and loading metadata into the vector DB."""
    
    async def run_async(self, sub_question: str) -> List[Paper]:
        """
        Retrieves papers for a sub-question asynchronously, saves them in batch,
        and returns the list of retrieved papers.
        """
        logger.info(f"RetrieverAgent starting search asynchronously for sub-question: '{sub_question}'")
        
        s2_limit = config.semantic_scholar_limit
        arxiv_limit = config.arxiv_limit
        
        # Search APIs concurrently in background threads
        s2_papers, arxiv_papers = await asyncio.gather(
            asyncio.to_thread(search_semantic_scholar, sub_question, limit=s2_limit),
            asyncio.to_thread(search_arxiv, sub_question, limit=arxiv_limit)
        )
        
        # Combine lists
        raw_papers = s2_papers + arxiv_papers
        logger.info(f"Fetched {len(s2_papers)} papers from Semantic Scholar, {len(arxiv_papers)} from ArXiv.")
        
        # Deduplicate papers based on title similarity/exact match
        seen_titles = set()
        deduped_papers = []
        
        for paper in raw_papers:
            clean_title = paper.title.lower().strip()
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                deduped_papers.append(paper)
            else:
                logger.debug(f"Skipping duplicate paper title: '{paper.title}'")
                
        # Store all papers in the local vector DB in batch
        await store_papers_async(deduped_papers)
            
        logger.info(f"RetrieverAgent finished asynchronously. Verified/Stored {len(deduped_papers)} papers in vector DB for: '{sub_question}'")
        return deduped_papers

    def run(self, sub_question: str) -> List[Paper]:
        """
        Retrieves papers for a sub-question, saves them into the vector database,
        and returns the list of retrieved papers.
        """
        logger.info(f"RetrieverAgent starting search for sub-question: '{sub_question}'")
        
        # 1. Search APIs (parallel searches or sequential; we will run them sequentially)
        s2_limit = config.semantic_scholar_limit
        arxiv_limit = config.arxiv_limit
        
        s2_papers = search_semantic_scholar(sub_question, limit=s2_limit)
        arxiv_papers = search_arxiv(sub_question, limit=arxiv_limit)
        
        # Combine lists
        raw_papers = s2_papers + arxiv_papers
        logger.info(f"Fetched {len(s2_papers)} papers from Semantic Scholar, {len(arxiv_papers)} from ArXiv.")
        
        # Deduplicate papers based on title similarity/exact match
        seen_titles = set()
        deduped_papers = []
        
        for paper in raw_papers:
            clean_title = paper.title.lower().strip()
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                deduped_papers.append(paper)
            else:
                logger.debug(f"Skipping duplicate paper title: '{paper.title}'")
                
        # 2. Store all papers in the local vector DB
        stored_count = 0
        for paper in deduped_papers:
            # store_paper embeds and writes to ChromaDB if it doesn't already exist
            store_paper(paper)
            stored_count += 1
            
        logger.info(f"RetrieverAgent finished. Stored/Verified {stored_count} papers in vector DB for: '{sub_question}'")
        return deduped_papers
