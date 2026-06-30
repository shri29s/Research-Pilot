import time
import logging
import asyncio
from typing import Dict, Tuple, Any, List
from config import config
from models.schemas import SessionState, CritiqueReport, Paper
from agents.decomposer import DecomposerAgent
from agents.retriever import RetrieverAgent
from agents.synthesiser import SynthesiserAgent
from agents.critic import CriticAgent
from agents.writer import WriterAgent
from utils.observability import Tracer

logger = logging.getLogger("ResearchPilot.Supervisor")

class SupervisorAgent:
    """The orchestrator agent managing the execution state, critique loop, and metrics compilation."""
    
    def __init__(self):
        self.decomposer = DecomposerAgent()
        self.retriever = RetrieverAgent()
        self.synthesiser = SynthesiserAgent()
        self.critic = CriticAgent()
        self.writer = WriterAgent()

    async def run(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Runs the full ResearchPilot multi-agent literature synthesis loop for a query asynchronously.
        Returns a tuple of (final_markdown_report, trace_summary_dict).
        """
        # 1. Start execution tracer
        tracer = Tracer(query)
        session_state = SessionState(query=query)
        
        # 2. Decompose query into sub-questions
        start_time = time.time()
        sub_questions = await self.decomposer.run_async(query)
        duration_ms = (time.time() - start_time) * 1000
        tracer.trace_step("DecomposerAgent", {"query": query}, sub_questions, duration_ms)
        
        session_state.sub_questions = sub_questions
        
        # Define concurrent sub-question process helper
        async def process_single_sub_question(index: int, sub_q: str) -> Tuple[List[Paper], str, CritiqueReport, int, float, float, float]:
            logger.info(f"--- Starting Sub-question {index}/{len(sub_questions)} asynchronously: '{sub_q}' ---")
            
            # 3a. Retrieve and store papers
            start_retriever = time.time()
            retrieved_papers = await self.retriever.run_async(sub_q)
            retriever_duration = (time.time() - start_retriever) * 1000
            
            # 3b. Synthesize & Critique loop
            iteration = 0
            feedback = None
            synthesis = ""
            critique = None
            
            sub_q_synthesiser_ms = 0.0
            sub_q_critic_ms = 0.0
            
            while iteration <= config.max_critique_loops:
                iteration += 1
                logger.info(f"Sub-question {index} - Synthesis Loop iteration {iteration}")
                
                # Run Synthesiser
                start_synth = time.time()
                synthesis = await self.synthesiser.run_async(sub_q, feedback=feedback)
                synth_duration = (time.time() - start_synth) * 1000
                sub_q_synthesiser_ms += synth_duration
                
                # Run Critic
                start_crit = time.time()
                critique = await self.critic.run_async(sub_q, retrieved_papers, synthesis)
                crit_duration = (time.time() - start_crit) * 1000
                sub_q_critic_ms += crit_duration
                
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
            
            return (
                retrieved_papers,
                synthesis,
                critique,
                iteration,
                retriever_duration,
                sub_q_synthesiser_ms,
                sub_q_critic_ms
            )

        # Run all sub-questions concurrently
        tasks = [process_single_sub_question(i, sub_q) for i, sub_q in enumerate(sub_questions, 1)]
        results = await asyncio.gather(*tasks)
        
        # Populate session state and trace metrics
        for index, (retrieved_papers, synthesis, critique, iterations_run, ret_dur, synth_dur, crit_dur) in enumerate(results, 1):
            sub_q = sub_questions[index - 1]
            
            # Store in session state
            session_state.retrieved_papers[sub_q] = retrieved_papers
            session_state.synthesis_drafts[sub_q] = synthesis
            session_state.critiques[sub_q] = critique
            
            # Record tracer metrics
            tracer.trace_step(
                f"RetrieverAgent_SubQ{index}",
                {"sub_question": sub_q},
                [p.id for p in retrieved_papers],
                ret_dur
            )
            tracer.increment_metric("total_papers_retrieved", len(retrieved_papers))
            
            tracer.trace_step(
                f"SynthesiserAgent_SubQ{index}",
                {"sub_question": sub_q},
                synthesis,
                synth_dur
            )
            tracer.trace_step(
                f"CriticAgent_SubQ{index}",
                {"sub_question": sub_q, "synthesis": synthesis},
                critique,
                crit_dur
            )
            
            tracer.set_sub_metric("synthesis_iterations", sub_q, iterations_run)
            tracer.set_sub_metric(
                "critic_scores", 
                sub_q, 
                {"coverage": critique.coverage, "grounding": critique.grounding, "citations": critique.citations}
            )
            
        # 4. Compile final report
        logger.info("--- Compiling Final Research Report ---")
        start_time = time.time()
        final_report = await self.writer.run_async(
            query=query, 
            syntheses=session_state.synthesis_drafts, 
            critiques=session_state.critiques,
            papers_by_subq=session_state.retrieved_papers
        )
        duration_ms = (time.time() - start_time) * 1000
        tracer.trace_step("WriterAgent", {"query": query}, final_report, duration_ms)
        
        session_state.final_report = final_report
        
        # 5. Finalize trace & metrics
        trace_summary = tracer.finalize()
        return final_report, trace_summary

