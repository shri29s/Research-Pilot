import time
import logging
from typing import Dict, Tuple, Any
from config import config
from src.models.schemas import SessionState, CritiqueReport
from src.services.decomposer import DecomposerAgent
from src.services.retriever import RetrieverAgent
from src.services.synthesiser import SynthesiserAgent
from src.services.critic import CriticAgent
from src.services.writer import WriterAgent
from src.utils.observability import Tracer

logger = logging.getLogger("ResearchPilot.Supervisor")

class SupervisorAgent:
    """The orchestrator agent managing the execution state, critique loop, and metrics compilation."""
    
    def __init__(self):
        self.decomposer = DecomposerAgent()
        self.retriever = RetrieverAgent()
        self.synthesiser = SynthesiserAgent()
        self.critic = CriticAgent()
        self.writer = WriterAgent()

    def run(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Runs the full ResearchPilot multi-agent literature synthesis loop for a query.
        Returns a tuple of (final_markdown_report, trace_summary_dict).
        """
        # 1. Start execution tracer
        tracer = Tracer(query)
        session_state = SessionState(query=query)
        
        # 2. Decompose query into sub-questions
        start_time = time.time()
        sub_questions = self.decomposer.run(query)
        duration_ms = (time.time() - start_time) * 1000
        tracer.trace_step("DecomposerAgent", {"query": query}, sub_questions, duration_ms)
        
        session_state.sub_questions = sub_questions
        
        # 3. Process each sub-question
        for index, sub_q in enumerate(sub_questions, 1):
            logger.info(f"--- Processing Sub-question {index}/{len(sub_questions)}: '{sub_q}' ---")
            
            # 3a. Retrieve and store papers
            start_time = time.time()
            retrieved_papers = self.retriever.run(sub_q)
            duration_ms = (time.time() - start_time) * 1000
            tracer.trace_step(
                f"RetrieverAgent_SubQ{index}", 
                {"sub_question": sub_q}, 
                [p.id for p in retrieved_papers], 
                duration_ms
            )
            
            session_state.retrieved_papers[sub_q] = retrieved_papers
            tracer.increment_metric("total_papers_retrieved", len(retrieved_papers))
            
            # 3b. Synthesize & Critique loop
            iteration = 0
            feedback = None
            synthesis = ""
            critique = None
            
            while iteration <= config.max_critique_loops:
                iteration += 1
                logger.info(f"Sub-question {index} - Synthesis Loop iteration {iteration}")
                
                # Run Synthesiser
                start_time = time.time()
                synthesis = self.synthesiser.run(sub_q, feedback=feedback)
                duration_ms = (time.time() - start_time) * 1000
                tracer.trace_step(
                    f"SynthesiserAgent_SubQ{index}_Iter{iteration}", 
                    {"sub_question": sub_q, "feedback": feedback}, 
                    synthesis, 
                    duration_ms
                )
                
                # Run Critic
                start_time = time.time()
                critique = self.critic.run(sub_q, retrieved_papers, synthesis)
                duration_ms = (time.time() - start_time) * 1000
                tracer.trace_step(
                    f"CriticAgent_SubQ{index}_Iter{iteration}", 
                    {"sub_question": sub_q, "synthesis": synthesis}, 
                    critique, 
                    duration_ms
                )
                
                # Check if scores are passing (>= 7 for all metrics)
                is_passing = (
                    critique.coverage >= 7 and 
                    critique.grounding >= 7 and 
                    critique.citations >= 7
                )
                
                if is_passing:
                    logger.info(f"Sub-question {index} - Synthesis PASSED review on iteration {iteration}.")
                    break
                elif iteration <= config.max_critique_loops:
                    logger.warning(
                        f"Sub-question {index} - Synthesis FAILED review (Scores: C={critique.coverage}, "
                        f"G={critique.grounding}, Ci={critique.citations}). Initiating revision loop..."
                    )
                    feedback = critique.revision_notes
                else:
                    logger.warning(
                        f"Sub-question {index} - Max critique loops ({config.max_critique_loops}) reached. "
                        f"Proceeding with current synthesis."
                    )
            
            # Save final synthesis and critique for this sub-question
            session_state.synthesis_drafts[sub_q] = synthesis
            session_state.critiques[sub_q] = critique
            
            # Track metrics
            tracer.set_sub_metric("synthesis_iterations", sub_q, iteration)
            tracer.set_sub_metric(
                "critic_scores", 
                sub_q, 
                {"coverage": critique.coverage, "grounding": critique.grounding, "citations": critique.citations}
            )
            
        # 4. Compile final report
        logger.info("--- Compiling Final Research Report ---")
        start_time = time.time()
        final_report = self.writer.run(
            query=query, 
            syntheses=session_state.synthesis_drafts, 
            critiques=session_state.critiques
        )
        duration_ms = (time.time() - start_time) * 1000
        tracer.trace_step("WriterAgent", {"query": query}, final_report, duration_ms)
        
        session_state.final_report = final_report
        
        # 5. Finalize trace & metrics
        trace_summary = tracer.finalize()
        return final_report, trace_summary
