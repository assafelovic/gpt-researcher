"""
Enhanced batch research manager for multiple research iterations with improved error handling and parallel processing
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResearchIteration:
    """Data class for research iteration results"""
    instruction: str
    context: Any
    urls: set
    iteration: int
    timestamp: datetime
    duration: float
    error: Optional[str] = None
    success: bool = True


class BatchResearchManager:
    """Enhanced manager for multiple research iterations with improved concurrency and error handling."""

    def __init__(self, researcher, max_concurrent: int = 3):
        """
        Initialize the batch research manager.
        
        Args:
            researcher: The GPTResearcher instance
            max_concurrent: Maximum number of concurrent research iterations
        """
        self.researcher = researcher
        self.research_results: List[ResearchIteration] = []
        self.all_contexts = []
        self.all_urls = set()
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.progress_callback: Optional[Callable] = None

    async def conduct_batch_research(
        self,
        research_instructions: List[str],
        parallel: bool = False,
        on_progress: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Conduct multiple research iterations with enhanced features.
        
        Args:
            research_instructions: List of research queries/instructions
            parallel: Whether to run iterations in parallel (respecting max_concurrent)
            on_progress: Optional callback for progress updates
            
        Returns:
            Enhanced combined research results with metadata
        """
        self.progress_callback = on_progress

        if not research_instructions:
            # Fall back to single research with enhanced tracking
            start_time = datetime.now()
            await self.researcher.research_conductor.conduct_research()
            duration = (datetime.now() - start_time).total_seconds()

            iteration = ResearchIteration(
                instruction=self.researcher.query,
                context=self.researcher.context,
                urls=set(self.researcher.visited_urls),
                iteration=1,
                timestamp=datetime.now(),
                duration=duration
            )

            return self._format_results([iteration], 1)

        if self.researcher.verbose:
            await self._stream_output(
                "batch_research_start",
                f"🔄 Starting {'parallel' if parallel else 'sequential'} batch research with {len(research_instructions)} iterations"
            )

        if parallel:
            results = await self._conduct_parallel_research(research_instructions)
        else:
            results = await self._conduct_sequential_research(research_instructions)

        # Process and combine results
        combined_context = self._combine_contexts_intelligently(results)

        # Update researcher with combined results
        self.researcher.context = combined_context
        self.researcher.visited_urls = self.all_urls

        if self.researcher.verbose:
            successful = sum(1 for r in results if r.success)
            await self._stream_output(
                "batch_research_complete",
                f"🎯 Batch research complete. Successful: {successful}/{len(results)}, "
                f"Total URLs: {len(self.all_urls)}, Combined context: {len(str(combined_context))} chars"
            )

        return self._format_results(results, len(research_instructions))

    async def _conduct_sequential_research(self, instructions: List[str]) -> List[ResearchIteration]:
        """Conduct research iterations sequentially."""
        results = []

        for i, instruction in enumerate(instructions, 1):
            result = await self._execute_single_research(instruction, i, len(instructions))
            results.append(result)

            if self.progress_callback:
                await self.progress_callback(i, len(instructions), result)

        return results

    async def _conduct_parallel_research(self, instructions: List[str]) -> List[ResearchIteration]:
        """Conduct research iterations in parallel with concurrency control."""
        tasks = []

        for i, instruction in enumerate(instructions, 1):
            task = self._execute_with_semaphore(instruction, i, len(instructions))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ResearchIteration(
                    instruction=instructions[i],
                    context="",
                    urls=set(),
                    iteration=i + 1,
                    timestamp=datetime.now(),
                    duration=0,
                    error=str(result),
                    success=False
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_with_semaphore(self, instruction: str, iteration: int, total: int) -> ResearchIteration:
        """Execute research with semaphore for concurrency control."""
        async with self.semaphore:
            return await self._execute_single_research(instruction, iteration, total)

    async def _execute_single_research(self, instruction: str, iteration: int, total: int) -> ResearchIteration:
        """Execute a single research iteration with comprehensive error handling."""
        start_time = datetime.now()

        if self.researcher.verbose:
            await self._stream_output(
                "batch_iteration",
                f"📚 Research iteration {iteration}/{total}: {instruction[:100]}..."
            )

        # Save original state
        original_query = self.researcher.query
        original_context = self.researcher.context

        try:
            # Update query for this iteration
            self.researcher.query = instruction

            # Conduct research with timeout
            timeout = getattr(self.researcher.cfg, 'research_timeout', 120)
            await asyncio.wait_for(
                self.researcher.research_conductor.conduct_research(),
                timeout=timeout
            )

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Create successful iteration result
            result = ResearchIteration(
                instruction=instruction,
                context=self.researcher.context,
                urls=set(self.researcher.visited_urls),
                iteration=iteration,
                timestamp=datetime.now(),
                duration=duration
            )

            # Update aggregated data
            self.all_contexts.append(self.researcher.context)
            self.all_urls.update(self.researcher.visited_urls)

            if self.researcher.verbose:
                await self._stream_output(
                    "iteration_complete",
                    f"✅ Iteration {iteration} complete in {duration:.1f}s. "
                    f"Context: {len(str(self.researcher.context))} chars, URLs: {len(self.researcher.visited_urls)}"
                )

            return result

        except asyncio.TimeoutError:
            error_msg = f"Timeout after {timeout}s"
            logger.error(f"Research iteration {iteration} timed out: {error_msg}")

            return ResearchIteration(
                instruction=instruction,
                context=original_context,
                urls=set(),
                iteration=iteration,
                timestamp=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                error=error_msg,
                success=False
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in research iteration {iteration}: {error_msg}")

            if self.researcher.verbose:
                await self._stream_output(
                    "iteration_error",
                    f"⚠️ Error in iteration {iteration}: {error_msg[:100]}"
                )

            return ResearchIteration(
                instruction=instruction,
                context=original_context,
                urls=set(),
                iteration=iteration,
                timestamp=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                error=error_msg,
                success=False
            )

        finally:
            # Always restore original query
            self.researcher.query = original_query

    def _combine_contexts_intelligently(self, results: List[ResearchIteration]) -> str:
        """
        Combine contexts with intelligent deduplication and organization.
        
        Args:
            results: List of research iteration results
            
        Returns:
            Combined and deduplicated context string
        """
        if not results:
            return ""

        # Extract successful contexts
        successful_contexts = [r.context for r in results if r.success and r.context]

        if not successful_contexts:
            return ""

        # Handle different context types
        if all(isinstance(ctx, str) for ctx in successful_contexts):
            # Deduplicate paragraphs/sections
            seen_paragraphs = set()
            combined_parts = []

            for ctx in successful_contexts:
                paragraphs = ctx.split('\n\n')
                for para in paragraphs:
                    para_clean = para.strip()
                    if para_clean and para_clean not in seen_paragraphs:
                        seen_paragraphs.add(para_clean)
                        combined_parts.append(para_clean)

            return "\n\n".join(combined_parts)

        # Handle list contexts
        combined = []
        seen_items = set()

        for ctx in successful_contexts:
            if isinstance(ctx, list):
                for item in ctx:
                    item_str = str(item).strip()
                    if item_str and item_str not in seen_items:
                        seen_items.add(item_str)
                        combined.append(item_str)
            else:
                ctx_str = str(ctx).strip()
                if ctx_str and ctx_str not in seen_items:
                    seen_items.add(ctx_str)
                    combined.append(ctx_str)

        return "\n\n".join(combined)

    def _format_results(self, results: List[ResearchIteration], total_planned: int) -> Dict[str, Any]:
        """Format results with comprehensive metadata."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        total_duration = sum(r.duration for r in results)
        avg_duration = total_duration / len(results) if results else 0

        return {
            "contexts": [r.context for r in successful_results],
            "urls": self.all_urls,
            "iterations_planned": total_planned,
            "iterations_completed": len(results),
            "iterations_successful": len(successful_results),
            "iterations_failed": len(failed_results),
            "instruction_results": [
                {
                    "instruction": r.instruction,
                    "context": r.context,
                    "urls": list(r.urls),
                    "iteration": r.iteration,
                    "timestamp": r.timestamp.isoformat(),
                    "duration": r.duration,
                    "success": r.success,
                    "error": r.error
                }
                for r in results
            ],
            "combined_context": self._combine_contexts_intelligently(results),
            "metadata": {
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "total_unique_urls": len(self.all_urls),
                "failed_instructions": [r.instruction for r in failed_results],
                "timestamp": datetime.now().isoformat()
            }
        }

    async def _stream_output(self, event_type: str, message: str):
        """Helper method to stream output."""
        try:
            from ..actions.utils import stream_output
            await stream_output(
                "logs",
                event_type,
                message,
                self.researcher.websocket,
            )
        except ImportError:
            # Fallback if stream_output is not available
            logger.info(f"{event_type}: {message}")

    def get_iteration_result(self, iteration: int) -> Optional[ResearchIteration]:
        """Get results from a specific iteration."""
        for result in self.research_results:
            if result.iteration == iteration:
                return result
        return None

    def get_successful_results(self) -> List[ResearchIteration]:
        """Get only successful research iterations."""
        return [r for r in self.research_results if r.success]

    def get_failed_results(self) -> List[ResearchIteration]:
        """Get only failed research iterations."""
        return [r for r in self.research_results if not r.success]

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the batch research."""
        if not self.research_results:
            return {}

        successful = self.get_successful_results()
        failed = self.get_failed_results()

        return {
            "total_iterations": len(self.research_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.research_results) if self.research_results else 0,
            "total_urls_discovered": len(self.all_urls),
            "average_urls_per_iteration": len(self.all_urls) / len(successful) if successful else 0,
            "total_context_size": sum(len(str(r.context)) for r in successful),
            "average_context_size": sum(len(str(r.context)) for r in successful) / len(successful) if successful else 0,
            "total_duration": sum(r.duration for r in self.research_results),
            "average_duration": sum(r.duration for r in self.research_results) / len(self.research_results)
        }