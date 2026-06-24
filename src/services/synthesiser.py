import logging
from typing import List, Optional
from src.models.schemas import Paper
from src.services.vector_store import retrieve_relevant_papers
from src.utils.llm import load_prompt, call_aimlabs

logger = logging.getLogger("ResearchPilot.SynthesiserAgent")

class SynthesiserAgent:
    """Agent responsible for querying the vector store and writing a synthesis draft for a sub-question."""
    
    def __init__(self):
        self.system_instruction_template = load_prompt("synthesiser")
        
    def run(self, sub_question: str, feedback: Optional[str] = None) -> str:
        """
        Retrieves relevant papers from the vector store and generates a synthesis.
        Allows passing feedback from the Critic agent for iterative revisions.
        """
        logger.info(f"SynthesiserAgent starting synthesis for: '{sub_question}'")
        
        # 1. Retrieve top 5 relevant papers from ChromaDB
        papers = retrieve_relevant_papers(sub_question, top_k=5)
        
        if not papers:
            logger.warning(f"No papers retrieved for sub-question: '{sub_question}'")
            return f"No academic papers containing abstract text relevant to this sub-question ('{sub_question}') were found in the database search."
            
        # 2. Format the papers for the prompt
        formatted_papers = ""
        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join(paper.authors) if paper.authors else "Unknown Authors"
            year_str = str(paper.year) if paper.year else "Unknown Year"
            citation_info = f"{paper.authors[0] if paper.authors else 'Unknown'} et al., {year_str}"
            
            formatted_papers += (
                f"[{i}] ID/Citation Ref: [{citation_info}]\n"
                f"Title: {paper.title}\n"
                f"Authors: {authors_str} | Year: {year_str}\n"
                f"Abstract: {paper.abstract}\n\n"
            )
            
        # 3. Format the system instruction and prompt
        system_instruction = self.system_instruction_template.format(
            sub_question=sub_question,
            papers=formatted_papers
        )
        
        prompt = (
            f"Please generate the academic synthesis paragraph answering: '{sub_question}'\n"
            f"Base your answer strictly on the source papers provided in the system instruction."
        )
        
        if feedback:
            logger.info(f"Applying feedback for revision of '{sub_question}'")
            prompt += f"\n\nCRITICAL - Previous Draft Feedback for Revision:\n{feedback}\nPlease revise the draft to address the issues raised above, maintaining strict factual grounding."
        
        # 4. Call LLM
        try:
            synthesis = call_aimlabs(
                system_instruction=system_instruction,
                prompt=prompt,
                json_mode=False
            )
            logger.info(f"Successfully generated synthesis for: '{sub_question}' (length={len(synthesis)})")
            return synthesis
        except Exception as e:
            logger.error(f"Error during synthesis generation: {str(e)}")
            return f"Failed to generate literature synthesis for: '{sub_question}' due to LLM error."
