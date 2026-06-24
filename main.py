import argparse
import sys
import os
import logging
from config import config
from src.utils.observability import setup_logger
from src.services.supervisor import SupervisorAgent

# Set up logging early
setup_logger(config.log_level)
logger = logging.getLogger("ResearchPilot.Main")

def main():
    parser = argparse.ArgumentParser(
        description="ResearchPilot: An AI Multi-Agent Academic Literature Synthesis Tool."
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="The research query or topic to compile a literature review for."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="literature_review.md",
        help="Path to save the generated Markdown report (default: literature_review.md)"
    )
    
    args = parser.parse_args()
    
    # Prompt user for input if positional query argument is not provided
    query = args.query
    if not query:
        print("\n=== Welcome to ResearchPilot ===")
        try:
            query = input("Enter your research topic/query: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting ResearchPilot. Goodbye!")
            sys.exit(0)
            
    if not query:
        print("Error: A research query is required.", file=sys.stderr)
        sys.exit(1)
        
    logger.info("Initializing ResearchPilot Multi-Agent System...")
    
    try:
        supervisor = SupervisorAgent()
        
        print(f"\nStarting multi-agent lit review compilation for: '{query}'")
        print("This may take 1-2 minutes. Processing academic APIs and auditing synthesis...")
        
        report, trace_summary = supervisor.run(query)
        
        # Save output markdown report
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n[Success] Literature review saved successfully to: {os.path.abspath(args.output)}")
        except Exception as e:
            logger.error(f"Failed to write output report to disk: {str(e)}")
            print(f"\n[Warning] Could not write report to file. Printing output instead:\n\n{report}")
            
        # Print high-level telemetry summary
        print("\n=== Run Telemetry Summary ===")
        metrics = trace_summary.get("metrics", {})
        print(f"- Total latencies: {metrics.get('total_latency_ms', 0) / 1000:.2f} seconds")
        print(f"- Academic papers retrieved & cached: {metrics.get('total_papers_retrieved', 0)}")
        print("- Synthesis quality validations completed:")
        
        synthesis_iterations = metrics.get("synthesis_iterations", {})
        critic_scores = metrics.get("critic_scores", {})
        for sub_q, iterations in synthesis_iterations.items():
            scores = critic_scores.get(sub_q, {})
            c_score = scores.get("coverage", 0)
            g_score = scores.get("grounding", 0)
            ci_score = scores.get("citations", 0)
            print(f"  * SubQ: \"{sub_q[:50]}...\"")
            print(f"    Iterations: {iterations} | Quality scores: Coverage {c_score}/10, Grounding {g_score}/10, Citations {ci_score}/10")
            
        print("\nTelemetry logs stored in logs/ directory.")
        
    except Exception as e:
        logger.error(f"Critical execution failure: {str(e)}", exc_info=True)
        print(f"\n[Error] The compilation failed due to a critical error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
