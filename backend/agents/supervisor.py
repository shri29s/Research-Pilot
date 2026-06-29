import time
import logging
import asyncio
from typing import Dict, Tuple, Any, AsyncGenerator
from config import config
from models.schemas import SessionState, CritiqueReport
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
        sub_questions = self.decomposer.run(query)
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
        
        total_retriever_ms = 0.0
        total_synthesiser_ms = 0.0
        total_critic_ms = 0.0
        
        # Process each sub-question
        for index, sub_q in enumerate(sub_questions, 1):
            yield {"type": "token", "content": f"### Sub-Question {index}: *{sub_q}*\n"}
            await asyncio.sleep(0.01)
            
            # 3a. Retrieve and store papers
            yield {"type": "agent_start", "agent": "retriever"}
            yield {"type": "token", "content": "**RetrieverAgent**: Querying Semantic Scholar & ArXiv databases...\n"}
            await asyncio.sleep(0.05)
            
            start_time = time.time()
            retrieved_papers = self.retriever.run(sub_q)
            step_duration = (time.time() - start_time) * 1000
            total_retriever_ms += step_duration
            
            tracer.trace_step(
                f"RetrieverAgent_SubQ{index}", 
                {"sub_question": sub_q}, 
                [p.id for p in retrieved_papers], 
                step_duration
            )
            
            session_state.retrieved_papers[sub_q] = retrieved_papers
            tracer.increment_metric("total_papers_retrieved", len(retrieved_papers))
            
            yield {"type": "agent_done", "agent": "retriever", "elapsed_ms": int(total_retriever_ms)}
            yield {"type": "token", "content": f"  * Retrieved and cached **{len(retrieved_papers)}** papers in ChromaDB.\n"}
            await asyncio.sleep(0.05)
            
            # 3b. Synthesize & Critique loop
            iteration = 0
            feedback = None
            synthesis = ""
            critique = None
            
            while iteration <= config.max_critique_loops:
                iteration += 1
                
                # Run Synthesiser
                yield {"type": "agent_start", "agent": "synthesiser"}
                yield {"type": "token", "content": f"**SynthesiserAgent**: Drafting synthesis block (Iteration {iteration})...\n"}
                await asyncio.sleep(0.05)
                
                start_time = time.time()
                synthesis = self.synthesiser.run(sub_q, feedback=feedback)
                step_duration = (time.time() - start_time) * 1000
                total_synthesiser_ms += step_duration
                
                tracer.trace_step(
                    f"SynthesiserAgent_SubQ{index}_Iter{iteration}", 
                    {"sub_question": sub_q, "feedback": feedback}, 
                    synthesis, 
                    step_duration
                )
                yield {"type": "agent_done", "agent": "synthesiser", "elapsed_ms": int(total_synthesiser_ms)}
                await asyncio.sleep(0.05)
                
                # Run Critic
                yield {"type": "agent_start", "agent": "critic"}
                yield {"type": "token", "content": "**CriticAgent (LLM-as-Judge)**: Auditing synthesis draft quality...\n"}
                await asyncio.sleep(0.05)
                
                start_time = time.time()
                critique = self.critic.run(sub_q, retrieved_papers, synthesis)
                step_duration = (time.time() - start_time) * 1000
                total_critic_ms += step_duration
                
                tracer.trace_step(
                    f"CriticAgent_SubQ{index}_Iter{iteration}", 
                    {"sub_question": sub_q, "synthesis": synthesis}, 
                    critique, 
                    step_duration
                )
                yield {"type": "agent_done", "agent": "critic", "elapsed_ms": int(total_critic_ms)}
                
                # Stream quality scores
                yield {"type": "token", "content": f"  * Quality audit scores: Coverage **{critique.coverage}/10** | Grounding **{critique.grounding}/10** | Citations **{critique.citations}/10**\n"}
                await asyncio.sleep(0.05)
                
                # Check if scores are passing (>= 7 for all metrics)
                is_passing = (
                    critique.coverage >= 7 and 
                    critique.grounding >= 7 and 
                    critique.citations >= 7
                )
                
                if is_passing:
                    yield {"type": "token", "content": "  * Review PASSED!\n\n"}
                    await asyncio.sleep(0.05)
                    break
                elif iteration <= config.max_critique_loops:
                    yield {"type": "token", "content": f"  * Review FAILED. Revision Notes: {critique.revision_notes}\n"}
                    await asyncio.sleep(0.05)
                    feedback = critique.revision_notes
                else:
                    yield {"type": "token", "content": "  * Review FAILED. Max revision attempts reached. Proceeding with current draft.\n\n"}
                    await asyncio.sleep(0.05)
            
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
        yield {"type": "agent_start", "agent": "writer"}
        yield {"type": "token", "content": "**WriterAgent**: Integrating syntheses and compiling final cited report...\n"}
        await asyncio.sleep(0.05)
        
        start_time = time.time()
        final_report = self.writer.run(
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
