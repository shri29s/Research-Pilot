import logging
import datetime
from typing import Dict, List
from models.schemas import CritiqueReport, Paper
from utils.llm import load_prompt, call_aimlabs, call_aimlabs_async

logger = logging.getLogger("ResearchPilot.WriterAgent")

class WriterAgent:
    """Agent responsible for compiling the structured research review from draft segments."""
    
    def __init__(self):
        self.system_instruction_template = load_prompt("writer")
        
    async def run_async(self, query: str, syntheses: Dict[str, str], critiques: Dict[str, CritiqueReport], papers_by_subq: Dict[str, List[Paper]]) -> str:
        """
        Assembles and edits the drafts into a publication-ready literature review report.
        """
        logger.info(f"WriterAgent compiling final report asynchronously for query: '{query}'")
        import datetime
        import re
        
        # 1. Format date
        today_str = datetime.date.today().strftime("%B %d, %Y")
        
        # 2. Build detailed sections block for themes generation
        sections_data = ""
        for i, sub_q in enumerate(syntheses.keys(), 1):
            synthesis_text = syntheses[sub_q]
            critique = critiques.get(sub_q)
            papers = papers_by_subq.get(sub_q, [])
            
            coverage = critique.coverage if critique else 0
            grounding = critique.grounding if critique else 0
            citations = critique.citations if critique else 0
            
            sources_text = ""
            if papers:
                sources_text = "\nAvailable Sources:\n"
                for p in papers:
                    url = p.external_url or f"https://arxiv.org/abs/{p.id.replace('arxiv_', '')}"
                    sources_text += f"- {p.title} — {', '.join(p.authors[:3])}{' et al.' if len(p.authors) > 3 else ''} ({p.year}) — {url}\n"
            
            sections_data += (
                f"--- SECTION {i} ---\n"
                f"Sub-question: {sub_q}\n"
                f"Synthesis Draft:\n{synthesis_text}\n"
                f"{sources_text}"
                f"Quality Scores: Coverage {coverage}/10 | Grounding {grounding}/10 | Citations {citations}/10\n\n"
            )
            
        # 3. Call LLM for themes synthesis
        system_instruction = (
            "You are the Writer Agent for ResearchPilot.\n"
            "Your role is to analyze a set of literature synthesis sections and write a 'Cross-cutting Themes' section.\n"
            "Identify 2-3 key overarching themes, gaps, or trends that appear across multiple sub-questions in the literature.\n"
            "Keep the tone professional and academic. Do not include any title or header in your response, just start writing the themes directly."
        )
        
        prompt = (
            f"Original Query: {query}\n\n"
            f"Section Drafts and Scores:\n"
            f"{sections_data}\n\n"
            f"Please write 2-3 paragraphs of Cross-cutting Themes based on the sections above."
        )
        
        try:
            themes_text = await call_aimlabs_async(
                system_instruction=system_instruction,
                prompt=prompt,
                json_mode=False
            )
        except Exception as e:
            logger.error(f"Error generating cross-cutting themes: {str(e)}")
            themes_text = "Error generating cross-cutting themes."
            
        # Helper function to add citation links
        def add_citation_links(text: str, papers: List[Paper]) -> str:
            if not papers:
                return text
                
            paper_map = {}
            for p in papers:
                if not p.authors:
                    continue
                first_author = p.authors[0]
                parts = first_author.split()
                last_name = parts[-1].lower() if parts else ""
                year = str(p.year) if p.year else ""
                url = p.external_url or f"https://arxiv.org/abs/{p.id.replace('arxiv_', '')}"
                
                if last_name and year:
                    paper_map[(last_name, year)] = url
                    # Also register all capitalized parts of first author name
                    for part in parts:
                        paper_map[(part.lower(), year)] = url

            def replace_citation(match):
                full_match = match.group(0)
                author_part = match.group(1)
                year_part = match.group(2)
                
                author_words = [w.lower() for w in re.findall(r'[A-Za-z]+', author_part)]
                for word in author_words:
                    if word != "et" and word != "al":
                        url = paper_map.get((word, year_part))
                        if url:
                            return f"[{author_part}, {year_part}]({url})"
                return full_match

            # Match patterns like [Author et al., 2025] or [Author, 2025]
            pattern = r'\[([A-Za-z\s\.\-]+),\s*(\d{4})\]'
            return re.sub(pattern, replace_citation, text)

        # 4. Programmatically assemble the final document
        sections = []
        sections.append(f"# Literature Review: {query}")
        sections.append(f"**Generated by ResearchPilot | Date: {today_str}**\n")
        
        for sub_q, synthesis_text in syntheses.items():
            sections.append("---")
            sections.append(f"## Sub-question: {sub_q}")
            
            papers = papers_by_subq.get(sub_q, [])
            linked_synthesis = add_citation_links(synthesis_text, papers)
            sections.append(linked_synthesis)
            sections.append("")
            
            if papers:
                sections.append("**Sources:**")
                for p in papers:
                    url = p.external_url or f"https://arxiv.org/abs/{p.id.replace('arxiv_', '')}"
                    authors_str = ", ".join(p.authors[:3]) + (" et al." if len(p.authors) > 3 else "")
                    sections.append(f"- [{p.title} — {authors_str} ({p.year})]({url})")
                sections.append("")
                
            critique = critiques.get(sub_q)
            if critique:
                sections.append(f"*Quality Metrics: Coverage {critique.coverage}/10 | Grounding {critique.grounding}/10 | Citations {critique.citations}/10*")
                if critique.revision_notes:
                    sections.append(f"*Reviewer Notes: {critique.revision_notes}*")
            sections.append("")
            
        sections.append("---")
        sections.append("## Cross-cutting Themes")
        # Strip header if LLM generated it
        themes_clean = themes_text.replace("## Cross-cutting Themes", "").strip()
        sections.append(themes_clean)
        sections.append("")
        
        sections.append("## Search Audit Trail")
        sections.append(f"- Total sub-questions analyzed: {len(syntheses)}")
        sections.append("- Data sources: Semantic Scholar API & ArXiv API")
        sections.append("- Synthesis quality validation: Critic Agent LLM-as-judge loop")
        
        final_report = "\n".join(sections)
        logger.info("Successfully compiled final literature review programmatically.")
        return final_report

    def run(self, query: str, syntheses: Dict[str, str], critiques: Dict[str, CritiqueReport], papers_by_subq: Dict[str, List[Paper]]) -> str:
        """
        Assembles and edits the drafts into a publication-ready literature review report.
        """
        logger.info(f"WriterAgent compiling final report for query: '{query}'")
        
        # 1. Format date
        today_str = datetime.date.today().strftime("%B %d, %Y")
        
        # 2. Build detailed sections block for LLM context (including paper URLs for citations)
        sections_data = ""
        for i, sub_q in enumerate(syntheses.keys(), 1):
            synthesis_text = syntheses[sub_q]
            critique = critiques.get(sub_q)
            papers = papers_by_subq.get(sub_q, [])
            
            coverage = critique.coverage if critique else 0
            grounding = critique.grounding if critique else 0
            citations = critique.citations if critique else 0
            revision_notes = critique.revision_notes if critique else ""
            
            # Build sources list with links
            sources_text = ""
            if papers:
                sources_text = "\nAvailable Sources:\n"
                for p in papers:
                    url = p.external_url or f"https://arxiv.org/abs/{p.id.replace('arxiv_', '')}"
                    sources_text += f"- {p.title} — {', '.join(p.authors[:3])}{' et al.' if len(p.authors) > 3 else ''} ({p.year}) — {url}\n"
            
            sections_data += (
                f"--- SECTION {i} ---\n"
                f"Sub-question: {sub_q}\n"
                f"Synthesis Draft:\n{synthesis_text}\n"
                f"{sources_text}"
                f"Quality Scores: Coverage {coverage}/10 | Grounding {grounding}/10 | Citations {citations}/10\n"
                f"Reviewer Notes: {revision_notes}\n\n"
            )
            
        system_instruction = (
            self.system_instruction_template
            .replace("{query}", query)
            .replace("{date}", today_str)
            .replace("{num_sub_questions}", str(len(syntheses)))
        )
        
        prompt = (
            f"Original Query: {query}\n"
            f"Date: {today_str}\n\n"
            f"Section Drafts and Scores:\n"
            f"{sections_data}\n\n"
            f"Please generate the complete, cohesive, and cited Markdown document with a 'Sources' subsection under each sub-question containing the clickable links."
        )
        
        # 4. Call LLM
        try:
            final_report = call_aimlabs(
                system_instruction=system_instruction,
                prompt=prompt,
                json_mode=False
            )
            logger.info("Successfully compiled final literature review.")
            return final_report
        except Exception as e:
            logger.error(f"Error compiling final report: {str(e)}")
            return (
                f"# Literature Review: {query}\n"
                f"Generated by ResearchPilot | Date: {today_str}\n\n"
                f"Error: The Writer Agent failed to compile the complete report due to an LLM error.\n"
            )
