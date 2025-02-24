#!/usr/bin/env python3
"""Benchmark the Eleven Audiobooks pipeline performance."""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from eleven_audiobooks.pipeline_manager import PipelineManager
from eleven_audiobooks.pipeline_state import ProcessingStage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    total_time: float
    stage_times: Dict[str, float]
    error: Optional[str] = None
    success: bool = True


async def run_benchmark(
    pdf_path: Path,
    output_dir: Path,
    translate: bool = False
) -> BenchmarkResult:
    """
    Run a benchmark of the pipeline.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory
        translate: Whether to include translation
        
    Returns:
        BenchmarkResult containing timing information
    """
    # Initialize timing dictionary
    stage_times: Dict[str, float] = {}
    start_time = time.time()
    
    try:
        # Initialize pipeline
        pipeline = PipelineManager(
            pdf_path=pdf_path,
            output_dir=output_dir,
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
            config={
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
                "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
                "DEEPL_API_KEY": os.getenv("DEEPL_API_KEY")
            }
        )
        
        # Process book and track stage times
        stage_start = time.time()
        last_stage = ProcessingStage.INITIALIZED
        
        async def track_progress() -> None:
            """Track progress and stage timing."""
            nonlocal stage_start, last_stage
            
            while pipeline.state.state.stage != ProcessingStage.COMPLETED:
                if pipeline.state.state.stage == ProcessingStage.FAILED:
                    break
                
                current_stage = pipeline.state.state.stage
                if current_stage != last_stage:
                    # Record time for previous stage
                    if last_stage != ProcessingStage.INITIALIZED:
                        stage_times[last_stage.value] = time.time() - stage_start
                    
                    # Start timing new stage
                    stage_start = time.time()
                    last_stage = current_stage
                
                await asyncio.sleep(0.1)
        
        # Start progress tracking
        progress_task = asyncio.create_task(track_progress())
        
        # Process book
        url = await pipeline.process(translate=translate)
        
        # Wait for progress tracking to complete
        await progress_task
        
        # Record final stage time
        if last_stage != ProcessingStage.INITIALIZED:
            stage_times[last_stage.value] = time.time() - stage_start
        
        if not url:
            return BenchmarkResult(
                total_time=time.time() - start_time,
                stage_times=stage_times,
                error="Pipeline failed to produce URL",
                success=False
            )
        
        return BenchmarkResult(
            total_time=time.time() - start_time,
            stage_times=stage_times
        )
        
    except Exception as e:
        return BenchmarkResult(
            total_time=time.time() - start_time,
            stage_times=stage_times,
            error=str(e),
            success=False
        )


def format_results(results: List[BenchmarkResult]) -> str:
    """Format benchmark results as a string."""
    output = []
    
    # Calculate averages
    total_times = [r.total_time for r in results if r.success]
    avg_total = sum(total_times) / len(total_times) if total_times else 0
    
    # Get all stages
    all_stages = set()
    for result in results:
        all_stages.update(result.stage_times.keys())
    
    # Calculate stage averages
    stage_averages = {}
    for stage in all_stages:
        times = [
            r.stage_times.get(stage, 0)
            for r in results
            if r.success and stage in r.stage_times
        ]
        stage_averages[stage] = sum(times) / len(times) if times else 0
    
    # Format output
    output.append("Benchmark Results")
    output.append("=================")
    output.append(f"\nTotal runs: {len(results)}")
    output.append(f"Successful runs: {len([r for r in results if r.success])}")
    output.append(f"\nAverage total time: {avg_total:.2f}s")
    
    output.append("\nAverage stage times:")
    for stage, avg_time in sorted(stage_averages.items()):
        output.append(f"  {stage}: {avg_time:.2f}s")
    
    if any(not r.success for r in results):
        output.append("\nErrors:")
        for i, result in enumerate(results):
            if not result.success:
                output.append(f"  Run {i+1}: {result.error}")
    
    return "\n".join(output)


async def main() -> None:
    """Run benchmarks."""
    # Load environment variables
    load_dotenv()
    
    # Setup paths
    test_data_dir = Path(__file__).parent.parent / "tests" / "data"
    pdf_path = test_data_dir / "sample.pdf"
    output_base = test_data_dir / "benchmark_output"
    
    # Benchmark parameters
    num_runs = 3
    translate = True
    
    # Run benchmarks
    results = []
    for i in range(num_runs):
        logger.info(f"Starting benchmark run {i+1}/{num_runs}")
        
        # Create unique output directory for this run
        output_dir = output_base / f"run_{i+1}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run benchmark
        result = await run_benchmark(pdf_path, output_dir, translate)
        results.append(result)
        
        logger.info(
            f"Run {i+1} completed in {result.total_time:.2f}s "
            f"({'success' if result.success else 'failure'})"
        )
    
    # Format and save results
    formatted_results = format_results(results)
    print("\n" + formatted_results)
    
    # Save results to file
    results_file = output_base / "benchmark_results.txt"
    results_file.write_text(formatted_results)
    
    # Save raw results as JSON
    raw_results = [
        {
            "total_time": r.total_time,
            "stage_times": r.stage_times,
            "error": r.error,
            "success": r.success
        }
        for r in results
    ]
    json_file = output_base / "benchmark_results.json"
    json_file.write_text(json.dumps(raw_results, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 