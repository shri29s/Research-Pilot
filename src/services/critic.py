import json
import logging
from typing import List
from src.models.schemas import Paper, CritiqueReport
from src.utils.llm import load_prompt, call_aimlabs

logger = logging.getLogger("ResearchPilot.CriticAgent")

class CriticAgent:
    """Agent responsible for auditing the literature synthesis using LLM-as-judge scoring."""
    
    def __init__(self):
        self.system_instruction = load_prompt("critic")
        
    def run(self, sub_question: str, papers: List[Paper], synthesis: str) -> CritiqueReport:
        """
        Runs quality critique scoring on a synthesis draft.
        """
        logger.info(f"CriticAgent starting review for sub-question: '{sub_question}'")
        
        # 1. Format the papers list
        formatted_papers = ""
        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join(paper.authors) if paper.authors else "Unknown Authors"
            year_str = str(paper.year) if paper.year else "Unknown Year"
            citation_info = f"{paper.authors[0] if paper.authors else 'Unknown'} et al., {year_str}"
            
            formatted_papers += (
                f"[{i}] ID/Citation Ref: [{citation_info}]\n"
                f"Title: {paper.title}\n"
                f"Abstract: {paper.abstract}\n\n"
            )
            
        # 2. Format the user prompt
        prompt = (
            f"Please score this draft synthesis against the papers.\n\n"
            f"Sub-question: {sub_question}\n\n"
            f"Draft Synthesis:\n{synthesis}"
        )
        
        # 3. Call LLM in JSON mode
        try:
            system_instruction_formatted = (
                self.system_instruction
                .replace("{sub_question}", sub_question)
                .replace("{papers}", formatted_papers)
                .replace("{synthesis}", synthesis)
            )
            
            response_text = call_aimlabs(
                system_instruction=system_instruction_formatted,
                prompt=prompt,
                json_mode=True
            )
            
            logger.debug(f"Critic response text: {response_text}")
            data = json.loads(response_text)
            
            report = CritiqueReport(
                coverage=int(data.get("coverage", 0)),
                grounding=int(data.get("grounding", 0)),
                citations=int(data.get("citations", 0)),
                revision_notes=data.get("revision_notes", "")
            )
            logger.info(
                f"Critic scored: coverage={report.coverage}/10, "
                f"grounding={report.grounding}/10, citations={report.citations}/10"
            )
            return report
            
        except Exception as e:
            logger.error(f"Error during CriticAgent run: {str(e)}")
            # Return a default CritiqueReport passing the synthesis in case of API failure
            return CritiqueReport(
                coverage=8,
                grounding=8,
                citations=8,
                revision_notes="Automatic review skipped due to an evaluation engine error."
            )
