import time
import logging
import asyncio
from typing import Dict, Tuple, Any, AsyncGenerator, List
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

    async def run(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs the full ResearchPilot multi-agent literature synthesis loop for a query
        as an async generator yielding trace events.
        """
        # Start Supervisor agent
        yield {"type": "agent_start", "agent": "supervisor"}
        await asyncio.sleep(0.05)
        
        start_time_total = time.time()
        tracer = Tracer(query)
        session_state = SessionState(query=query)
        
        # Finished Supervisor initialization
        duration_ms = (time.time() - start_time_total) * 1000
        yield {"type": "agent_done", "agent": "supervisor", "elapsed_ms": int(duration_ms)}
        await asyncio.sleep(0.05)
        
        # Yield initial live trace header
        yield {"type": "token", "content": f"# ResearchPilot Live Agent Logs\n**Query:** *\"{query}\"*\n\n"}
        await asyncio.sleep(0.01)
        
        # Start Decomposer agent
        yield {"type": "agent_start", "agent": "decomposer"}
        yield {"type": "token", "content": "**DecomposerAgent**: Decomposing research topic into sub-questions...\n"}
        await asyncio.sleep(0.05)
        
        start_time = time.time()
        sub_questions = await self.decomposer.run_async(query)
        duration_ms = (time.time() - start_time) * 1000
        tracer.trace_step("DecomposerAgent", {"query": query}, sub_questions, duration_ms)
        
        session_state.sub_questions = sub_questions
        yield {"type": "agent_done", "agent": "decomposer", "elapsed_ms": int(duration_ms)}
        
        # Stream the decomposed sub-questions
        yield {"type": "token", "content": f"  * Topic broken down into **{len(sub_questions)}** target questions:\n"}
        for sq in sub_questions:
            yield {"type": "token", "content": f"    - *{sq}*\n"}
        yield {"type": "token", "content": "\n"}
        await asyncio.sleep(0.05)
        
        # Define concurrent sub-question process helper
        async def process_single_sub_question(index: int, sub_q: str) -> Tuple[List[Dict[str, Any]], List[Paper], str, CritiqueReport, int, float, float, float]:
            sub_q_events = []
            
            # Helper to append token events
            def log_token(content: str):
                sub_q_events.append({"type": "token", "content": content})
                
            log_token(f"### Sub-Question {index}: *{sub_q}*\n")
            
            # 3a. Retrieve and store papers
            sub_q_events.append({"type": "agent_start", "agent": "retriever"})
            log_token("**RetrieverAgent**: Querying Semantic Scholar & ArXiv databases...\n")
            
            start_retriever = time.time()
            retrieved_papers = await self.retriever.run_async(sub_q)
            retriever_duration = (time.time() - start_retriever) * 1000
            
            sub_q_events.append({"type": "agent_done", "agent": "retriever", "elapsed_ms": int(retriever_duration)})
            log_token(f"  * Retrieved and cached **{len(retrieved_papers)}** papers in ChromaDB.\n")
            
            # 3b. Synthesize & Critique loop
            iteration = 0
            feedback = None
            synthesis = ""
            critique = None
            
            sub_q_synthesiser_ms = 0.0
            sub_q_critic_ms = 0.0
            
            while iteration <= config.max_critique_loops:
                iteration += 1
                
                # Run Synthesiser
                sub_q_events.append({"type": "agent_start", "agent": "synthesiser"})
                log_token(f"**SynthesiserAgent**: Drafting synthesis block (Iteration {iteration})...\n")
                
                start_synth = time.time()
                synthesis = await self.synthesiser.run_async(sub_q, feedback=feedback)
                synth_duration = (time.time() - start_synth) * 1000
                sub_q_synthesiser_ms += synth_duration
                
                sub_q_events.append({"type": "agent_done", "agent": "synthesiser", "elapsed_ms": int(sub_q_synthesiser_ms)})
                
                # Run Critic
                sub_q_events.append({"type": "agent_start", "agent": "critic"})
                log_token("**CriticAgent (LLM-as-Judge)**: Auditing synthesis draft quality...\n")
                
                start_crit = time.time()
                critique = await self.critic.run_async(sub_q, retrieved_papers, synthesis)
                crit_duration = (time.time() - start_crit) * 1000
                sub_q_critic_ms += crit_duration
                
                sub_q_events.append({"type": "agent_done", "agent": "critic", "elapsed_ms": int(sub_q_critic_ms)})
                log_token(f"  * Quality audit scores: Coverage **{critique.coverage}/10** | Grounding **{critique.grounding}/10** | Citations **{critique.citations}/10**\n")
                
                # Check if scores are passing (>= 7 for all metrics)
                is_passing = (
                    critique.coverage >= 7 and 
                    critique.grounding >= 7 and 
                    critique.citations >= 7
                )
                
                if is_passing:
                    log_token("  * Review PASSED!\n\n")
                    break
                elif iteration <= config.max_critique_loops:
                    log_token(f"  * Review FAILED. Revision Notes: {critique.revision_notes}\n")
                    feedback = critique.revision_notes
                else:
                    log_token("  * Review FAILED. Max revision attempts reached. Proceeding with current draft.\n\n")
            
            return (
                sub_q_events,
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
        
        # Populate session state and trace metrics, and yield events in order
        for index, (sub_q_events, retrieved_papers, synthesis, critique, iterations_run, ret_dur, synth_dur, crit_dur) in enumerate(results, 1):
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
            
            # Yield events to UI sequentially
            for event in sub_q_events:
                yield event
                if event["type"] == "token":
                    await asyncio.sleep(0.01)
                else:
                    await asyncio.sleep(0.05)
            
        # 4. Compile final report
        logger.info("--- Compiling Final Research Report ---")
        yield {"type": "agent_start", "agent": "writer"}
        yield {"type": "token", "content": "**WriterAgent**: Integrating syntheses and compiling final cited report...\n"}
        await asyncio.sleep(0.05)
        
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
        
        # Clear the progress logs buffer to stream the clean final document
        yield {"type": "clear_buffer"}
        await asyncio.sleep(0.05)
        
        # Stream the markdown report in chunks to simulate streaming tokens
        chunk_size = 40
        for i in range(0, len(final_report), chunk_size):
            yield {"type": "token", "content": final_report[i:i+chunk_size]}
            await asyncio.sleep(0.01)
            
        yield {"type": "agent_done", "agent": "writer", "elapsed_ms": int(duration_ms)}
        await asyncio.sleep(0.05)
        
        # 5. Finalize trace & metrics
        tracer.finalize()
        yield {"type": "done"}

# Singleton instance
supervisor = SupervisorAgent()

