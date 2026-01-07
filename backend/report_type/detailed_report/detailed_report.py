import asyncio
import logging
from typing import List, Dict, Set, Optional, Any
from fastapi import WebSocket

from gpt_researcher import GPTResearcher

logger = logging.getLogger(__name__)


class DetailedReport:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls: List[str] = [],
        document_urls: List[str] = [],
        query_domains: List[str] = [],
        config_path: str = None,
        tone: Any = "",
        websocket: WebSocket = None,
        subtopics: List[Dict] = [],
        headers: Optional[Dict] = None,
        complement_source_urls: bool = False,
        mcp_configs=None,
        mcp_strategy=None,
    ):
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.document_urls = document_urls
        self.query_domains = query_domains
        self.config_path = config_path
        self.tone = tone
        self.websocket = websocket
        self.subtopics = subtopics
        self.headers = headers or {}
        self.complement_source_urls = complement_source_urls
        
        # Initialize researcher with optional MCP parameters
        gpt_researcher_params = {
            "query": self.query,
            "query_domains": self.query_domains,
            "report_type": "research_report",
            "report_source": self.report_source,
            "source_urls": self.source_urls,
            "document_urls": self.document_urls,
            "config_path": self.config_path,
            "tone": self.tone,
            "websocket": self.websocket,
            "headers": self.headers,
            "complement_source_urls": self.complement_source_urls,
        }

        # Add MCP parameters if provided
        if mcp_configs is not None:
            gpt_researcher_params["mcp_configs"] = mcp_configs
        if mcp_strategy is not None:
            gpt_researcher_params["mcp_strategy"] = mcp_strategy

        self.gpt_researcher = GPTResearcher(**gpt_researcher_params)
        self.existing_headers: List[Dict] = []
        self.global_context: List[str] = []
        self.global_written_sections: List[str] = []
        self.global_urls: Set[str] = set(
            self.source_urls) if self.source_urls else set()

    async def run(self) -> str:
        logger.info("=" * 80)
        logger.info("Starting detailed report generation with structure planning")
        logger.info("=" * 80)
        
        # Step 1: Initial research
        logger.info("[Step 1] Conducting initial research...")
        await self._initial_research()
        logger.info(f"[Step 1] Completed. Context length: {len(self.global_context)}, URLs: {len(self.global_urls)}")
        
        # Step 2: Get initial subtopics
        logger.info("[Step 2] Generating initial subtopics...")
        initial_subtopics = await self._get_all_subtopics()
        logger.info(f"[Step 2] Generated {len(initial_subtopics)} initial subtopics")
        logger.info(f"[Step 2] Initial subtopics (BEFORE planning): {[s.get('task', '') for s in initial_subtopics]}")
        
        # Step 3: Collect subtopics and their headers (without writing full reports)
        logger.info("[Step 3] Collecting subtopics and draft headers (without writing full reports)...")
        collected_subtopics_info = await self._collect_subtopics_and_headers(initial_subtopics)
        logger.info(f"[Step 3] Collected {len(collected_subtopics_info)} subtopics with headers")
        for idx, item in enumerate(collected_subtopics_info):
            headers_text = ", ".join([h.get('text', '')[:30] for h in item.get('headers', [])[:3]])
            logger.info(f"[Step 3] Subtopic {idx+1}: {item.get('task', '')[:50]}... | Headers: {headers_text}...")
        
        # Step 4: Reorganize subtopics and headers based on logical structure
        logger.info("[Step 4] Reorganizing subtopics and headers based on logical structure...")
        reorganized_subtopics = await self._reorganize_subtopics_and_headers(collected_subtopics_info)
        logger.info(f"[Step 4] Reorganized {len(reorganized_subtopics)} subtopics")
        logger.info(f"[Step 4] Reorganized subtopics (AFTER planning): {[s.get('task', '') for s in reorganized_subtopics]}")
        
        # Log comparison
        logger.info("-" * 80)
        logger.info("COMPARISON: Before vs After Reorganization")
        logger.info("-" * 80)
        logger.info("BEFORE (Initial order):")
        for idx, subtopic in enumerate(initial_subtopics, 1):
            logger.info(f"  {idx}. {subtopic.get('task', '')}")
        logger.info("AFTER (Reorganized order):")
        for idx, subtopic in enumerate(reorganized_subtopics, 1):
            logger.info(f"  {idx}. {subtopic.get('task', '')}")
        logger.info("-" * 80)
        
        # Step 5: Generate Research Gap
        logger.info("[Step 5] Identifying Research Gap...")
        research_gap_content = await self.gpt_researcher.write_research_gap()
        logger.info(f"[Step 5] Research Gap identified: {len(research_gap_content)} chars")

        # Step 6: Generate introduction
        logger.info("[Step 6] Writing introduction...")
        report_introduction = await self.gpt_researcher.write_introduction(research_gap=research_gap_content)
        logger.info("[Step 6] Introduction completed")
        
        # Step 7: Generate full reports for reorganized subtopics
        logger.info("[Step 7] Generating full reports for reorganized subtopics...")
        _, report_body = await self._generate_subtopic_reports(reorganized_subtopics)
        logger.info(f"[Step 7] Generated reports for {len(reorganized_subtopics)} subtopics")
        
        # Step 8: Construct final report
        logger.info("[Step 8] Constructing final detailed report...")
        self.gpt_researcher.visited_urls.update(self.global_urls)
        report = await self._construct_detailed_report(report_introduction, report_body, research_gap_content)
        logger.info("[Step 8] Final report constructed")
        logger.info("=" * 80)
        logger.info("Detailed report generation completed successfully")
        logger.info("=" * 80)
        
        return report

    async def _initial_research(self) -> None:
        await self.gpt_researcher.conduct_research()
        self.global_context = self.gpt_researcher.context
        self.global_urls = self.gpt_researcher.visited_urls

    async def _get_all_subtopics(self) -> List[Dict]:
        subtopics_data = await self.gpt_researcher.get_subtopics()

        all_subtopics = []
        if subtopics_data and subtopics_data.subtopics:
            for subtopic in subtopics_data.subtopics:
                all_subtopics.append({"task": subtopic.task})
        else:
            logger.warning(f"Unexpected subtopics data format: {subtopics_data}")

        return all_subtopics

    async def _collect_subtopics_and_headers(self, subtopics: List[Dict]) -> List[Dict]:
        """
        For each subtopic, conduct research and extract draft headers without writing full report.
        This collects information needed for structure planning.
        
        Args:
            subtopics: List of subtopic tasks
            
        Returns:
            List of subtopics with their headers and context
        """
        subtopics_with_headers = []
        total_subtopics = len(subtopics)

        for i, subtopic in enumerate(subtopics):
            current_subtopic_task = subtopic.get("task")
            logger.info(f"[Step 3.{i+1}/{total_subtopics}] Collecting headers for: {current_subtopic_task[:50]}...")

            try:
                # Create researcher for this subtopic
                subtopic_assistant = GPTResearcher(
                    query=current_subtopic_task,
                    query_domains=self.query_domains,
                    report_type="subtopic_report",
                    report_source=self.report_source,
                    websocket=self.websocket,
                    headers=self.headers,
                    parent_query=self.query,
                    subtopics=self.subtopics,
                    visited_urls=self.global_urls,
                    agent=self.gpt_researcher.agent,
                    role=self.gpt_researcher.role,
                    tone=self.tone,
                    complement_source_urls=self.complement_source_urls,
                    source_urls=self.source_urls,
                    mcp_configs=self.gpt_researcher.mcp_configs,
                    mcp_strategy=self.gpt_researcher.mcp_strategy
                )

                # Conduct research with timeout
                subtopic_assistant.context = list(set(self.global_context))

                # Add timeout to prevent hanging (3 minutes per subtopic)
                try:
                    await asyncio.wait_for(
                        subtopic_assistant.conduct_research(),
                        timeout=180.0  # 3 minutes timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Subtopic research timed out after 3 minutes: {current_subtopic_task}")
                    # Continue with empty headers for this subtopic
                    parse_draft_section_titles = []
                    draft_section_titles = ""
                else:
                    # Extract draft section titles (headers) without writing full report
                    try:
                        draft_section_titles = await asyncio.wait_for(
                            subtopic_assistant.get_draft_section_titles(current_subtopic_task),
                            timeout=60.0  # 1 minute timeout for header extraction
                        )

                        if not isinstance(draft_section_titles, str):
                            draft_section_titles = str(draft_section_titles)

                        # Parse headers
                        parse_draft_section_titles = self.gpt_researcher.extract_headers(draft_section_titles)
                    except asyncio.TimeoutError:
                        logger.warning(f"Header extraction timed out for subtopic: {current_subtopic_task}")
                        parse_draft_section_titles = []
                        draft_section_titles = ""
                    except Exception as e:
                        logger.error(f"Error extracting headers for subtopic {current_subtopic_task}: {e}")
                        parse_draft_section_titles = []
                        draft_section_titles = ""

                # Update global context and URLs
                self.global_context = list(set(subtopic_assistant.context))
                self.global_urls.update(subtopic_assistant.visited_urls)

                # Aggregate costs and tokens from subtopic assistant
                self.gpt_researcher.add_costs(subtopic_assistant.get_costs())
                sub_token_usage = subtopic_assistant.get_token_usage()
                self.gpt_researcher.add_token_usage(
                    prompt_tokens=sub_token_usage.get("prompt_tokens", 0),
                    completion_tokens=sub_token_usage.get("completion_tokens", 0)
                )

                # Store subtopic with its headers and context
                subtopics_with_headers.append({
                    "task": current_subtopic_task,
                    "headers": parse_draft_section_titles,
                    "context": subtopic_assistant.context,
                    "draft_titles": draft_section_titles
                })

                logger.info(f"[Step 3.{i+1}/{total_subtopics}] Collected {len(parse_draft_section_titles)} headers")

            except Exception as e:
                logger.error(f"Error processing subtopic {current_subtopic_task}: {e}")
                # Add empty entry for failed subtopic
                subtopics_with_headers.append({
                    "task": current_subtopic_task,
                    "headers": [],
                    "context": [],
                    "draft_titles": ""
                })

        return subtopics_with_headers

    async def _reorganize_subtopics_and_headers(self, subtopics_with_headers: List[Dict]) -> List[Dict]:
        """
        Reorganize subtopics and headers into a logical structure.
        Directly generates the final subtopics list with reorganized tasks and headers.
        
        Args:
            subtopics_with_headers: List of subtopics with their headers and context
            
        Returns:
            Reorganized list of subtopics with task and headers (ready for writer)
        """
        if not subtopics_with_headers:
            return subtopics_with_headers
        
        # Combine context from all subtopics
        combined_context = "\n\n".join(self.global_context[:10])  # Use first 10 context items
        
        # Prepare subtopics information for LLM
        subtopics_info = []
        for idx, item in enumerate(subtopics_with_headers):
            headers_text = "\n".join([f"- {h.get('text', '')}" for h in item.get("headers", [])])
            subtopics_info.append(
                f"Subtopic {idx + 1}: {item['task']}\n"
                f"Headers:\n{headers_text}"
            )
        
        combined_subtopics_info = "\n\n".join(subtopics_info)
        
        # Use LLM to reorganize subtopics and headers directly
        try:
            from gpt_researcher.utils.llm import create_chat_completion
            import json
            import json_repair
            
            # Use the prompt from PromptFamily
            prompt = self.gpt_researcher.prompt_family.generate_reorganize_subtopics_prompt(
                main_topic=self.query,
                research_context=combined_context[:2000],
                subtopics_with_headers=combined_subtopics_info
            )
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # CRITICAL: Use LOGICAL_LLM (or SMART_LLM as fallback) for logical reasoning
            # This step requires the best model as it needs to:
            # - Understand relationships between subtopics
            # - Merge related concepts logically
            # - Order subtopics in a coherent flow
            # - Ensure headers don't overlap across subtopics
            
            # Use LOGICAL_LLM if configured, otherwise fall back to SMART_LLM
            logical_model = getattr(self.gpt_researcher.cfg, 'logical_llm_model', None) or self.gpt_researcher.cfg.smart_llm_model
            logical_provider = getattr(self.gpt_researcher.cfg, 'logical_llm_provider', None) or self.gpt_researcher.cfg.smart_llm_provider
            # Use SMART_TOKEN_LIMIT for logical_llm (no separate token limit needed)
            logical_token_limit = self.gpt_researcher.cfg.smart_token_limit
            
            logger.info(f"[CRITICAL] Reorganizing subtopics and headers using LOGICAL model: {logical_model}")
            logger.info("This step requires advanced logical reasoning to ensure coherent report structure")
            
            # Some models (e.g., gpt-5.2-chat) don't support custom temperature, only default (1)
            # Remove temperature from llm_kwargs if model doesn't support it
            llm_kwargs = self.gpt_researcher.cfg.llm_kwargs.copy() if self.gpt_researcher.cfg.llm_kwargs else {}
            if "gpt-5.2" in logical_model.lower():
                # Remove temperature from kwargs for gpt-5.2-chat (only supports default value 1)
                llm_kwargs.pop("temperature", None)
            
            completion_kwargs = {
                "model": logical_model,  # Use LOGICAL_LLM if configured, otherwise SMART_LLM
                "messages": messages,
                "max_tokens": logical_token_limit,
                "llm_provider": logical_provider,
                "llm_kwargs": llm_kwargs,
                "cost_callback": self.gpt_researcher.add_costs,
                **self.gpt_researcher.kwargs
            }
            
            # Only add temperature if model supports it (gpt-5.2-chat doesn't)
            if "gpt-5.2" not in logical_model.lower():
                completion_kwargs["temperature"] = 0.3  # Lower temperature for more consistent and logical reorganization
            
            response = await create_chat_completion(**completion_kwargs)
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                reorganization_result = json_repair.loads(response)
            except:
                # If direct parsing fails, try to extract JSON block
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    reorganization_result = json_repair.loads(json_match.group())
                else:
                    logger.warning("Failed to parse reorganization result, returning subtopics as-is")
                    return subtopics_with_headers
            
            # Extract reorganized subtopics
            reorganized_items = reorganization_result.get("reorganized_subtopics", [])
            
            if not reorganized_items:
                logger.warning("No reorganized subtopics in response, returning original")
                return subtopics_with_headers
            
            # Convert to our format and preserve context from original subtopics
            # Create mapping from original task to context
            task_to_context = {item["task"]: item.get("context", []) for item in subtopics_with_headers}
            
            reorganized_subtopics = []
            for item in sorted(reorganized_items, key=lambda x: x.get("order", 999)):
                # Get context from original subtopics if task matches
                # If merged, combine contexts from multiple original subtopics
                context = []
                task_text = item.get("task", "")
                
                # Try to find matching original subtopic(s) for context
                for orig_subtopic in subtopics_with_headers:
                    if orig_subtopic["task"] in task_text or task_text in orig_subtopic["task"]:
                        context.extend(orig_subtopic.get("context", []))
                
                # If no match found, use empty context (will be filled during report generation)
                if not context:
                    context = []
                
                reorganized_subtopics.append({
                    "task": task_text,
                    "headers": item.get("headers", []),
                    "context": list(set(context)),  # Remove duplicates
                    "order": item.get("order", 999)
                })
            
            # Sort by order
            reorganized_subtopics.sort(key=lambda x: x.get("order", 999))
            
            logger.info(f"Reorganized {len(reorganized_subtopics)} subtopics with headers")
            for idx, subtopic in enumerate(reorganized_subtopics, 1):
                headers_count = len(subtopic.get("headers", []))
                logger.info(f"  {idx}. {subtopic.get('task', '')[:50]}... ({headers_count} headers)")
            
            return reorganized_subtopics
            
        except Exception as e:
            logger.error(f"Error reorganizing subtopics and headers: {e}", exc_info=True)
            # Fallback: return original subtopics
            return subtopics_with_headers

    async def _generate_subtopic_reports(self, reorganized_subtopics: List[Dict]) -> tuple:
        """
        Generate full reports for each reorganized subtopic.
        This happens AFTER structure is planned and subtopics are reorganized.
        
        Args:
            reorganized_subtopics: List of reorganized subtopics with headers and context
            
        Returns:
            Tuple of (subtopic_reports, report_body)
        """
        subtopic_reports = []
        subtopics_report_body = ""
        total_subtopics = len(reorganized_subtopics)

        for i, subtopic_data in enumerate(reorganized_subtopics):
            current_task = subtopic_data.get("task", "")
            logger.info(f"[Step 7.{i+1}/{total_subtopics}] Generating full report for: {current_task[:50]}...")
            
            result = await self._get_subtopic_report(subtopic_data)
            if result["report"]:
                subtopic_reports.append(result)
                # Ensure report is a string (not a list)
                report_content = result['report']
                if isinstance(report_content, list):
                    report_content = "\n\n".join(str(item) for item in report_content)
                elif not isinstance(report_content, str):
                    report_content = str(report_content)
                subtopics_report_body += f"\n\n\n{report_content}"
                logger.info(f"[Step 7.{i+1}/{total_subtopics}] Report generated successfully")

        return subtopic_reports, subtopics_report_body

    async def _get_subtopic_report(self, subtopic_data: Dict) -> Dict[str, str]:
        """
        Generate full report for a subtopic.
        This is called AFTER structure planning and reorganization.
        The subtopic_data may already contain headers and context from the collection phase.
        
        Args:
            subtopic_data: Subtopic data with task, headers, and context
            
        Returns:
            Dict with topic and report
        """
        current_subtopic_task = subtopic_data.get("task")
        existing_headers_for_subtopic = subtopic_data.get("headers", [])
        subtopic_context = subtopic_data.get("context", [])

        try:
            # Create researcher for this subtopic
            subtopic_assistant = GPTResearcher(
                query=current_subtopic_task,
                query_domains=self.query_domains,
                report_type="subtopic_report",
                report_source=self.report_source,
                websocket=self.websocket,
                headers=self.headers,
                parent_query=self.query,
                subtopics=self.subtopics,
                visited_urls=self.global_urls,
                agent=self.gpt_researcher.agent,
                role=self.gpt_researcher.role,
                tone=self.tone,
                complement_source_urls=self.complement_source_urls,
                source_urls=self.source_urls,
                mcp_configs=self.gpt_researcher.mcp_configs,
                mcp_strategy=self.gpt_researcher.mcp_strategy
            )

            # Use the context collected earlier (if available)
            if subtopic_context:
                subtopic_assistant.context = list(set(subtopic_context + self.global_context))
            else:
                subtopic_assistant.context = list(set(self.global_context))

            # Use the headers extracted earlier (if available)
            if existing_headers_for_subtopic:
                parse_draft_section_titles_text = [header.get("text", "") for header in existing_headers_for_subtopic]
            else:
                # Fallback: extract headers again if not available
                try:
                    draft_section_titles = await asyncio.wait_for(
                        subtopic_assistant.get_draft_section_titles(current_subtopic_task),
                        timeout=60.0
                    )
                    if not isinstance(draft_section_titles, str):
                        draft_section_titles = str(draft_section_titles)
                    parse_draft_section_titles = self.gpt_researcher.extract_headers(draft_section_titles)
                    parse_draft_section_titles_text = [header.get("text", "") for header in parse_draft_section_titles]
                except asyncio.TimeoutError:
                    logger.warning(f"Draft section titles extraction timed out for subtopic: {current_subtopic_task}")
                    parse_draft_section_titles_text = []

            # Get relevant contents to avoid duplication
            try:
                relevant_contents = await asyncio.wait_for(
                    subtopic_assistant.get_similar_written_contents_by_draft_section_titles(
                        current_subtopic_task, parse_draft_section_titles_text, self.global_written_sections
                    ),
                    timeout=60.0  # 1 minute timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Relevant contents retrieval timed out for subtopic: {current_subtopic_task}")
                relevant_contents = []

            # Write the full report
            try:
                subtopic_report = await asyncio.wait_for(
                    subtopic_assistant.write_report(self.existing_headers, relevant_contents),
                    timeout=300.0  # 5 minutes timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Report writing timed out for subtopic: {current_subtopic_task}")
                subtopic_report = f"# {current_subtopic_task}\n\n*Report generation timed out after 5 minutes*"

            # Update tracking
            self.global_written_sections.extend(self.gpt_researcher.extract_sections(subtopic_report))
            self.global_context = list(set(subtopic_assistant.context))
            self.global_urls.update(subtopic_assistant.visited_urls)

            # Aggregate costs and tokens from subtopic assistant
            self.gpt_researcher.add_costs(subtopic_assistant.get_costs())
            sub_token_usage = subtopic_assistant.get_token_usage()
            self.gpt_researcher.add_token_usage(
                prompt_tokens=sub_token_usage.get("prompt_tokens", 0),
                completion_tokens=sub_token_usage.get("completion_tokens", 0)
            )

            self.existing_headers.append({
                "subtopic task": current_subtopic_task,
                "headers": self.gpt_researcher.extract_headers(subtopic_report),
            })

            return {"topic": {"task": current_subtopic_task}, "report": subtopic_report}

        except Exception as e:
            logger.error(f"Error generating subtopic report for {current_subtopic_task}: {e}")
            return {"topic": {"task": current_subtopic_task}, "report": f"# {current_subtopic_task}\n\n*Error: {str(e)}*"}

    async def _construct_detailed_report(self, introduction: str, report_body: str, research_gap: str = "") -> str:
        toc = self.gpt_researcher.table_of_contents(report_body)
        conclusion = await self.gpt_researcher.write_report_conclusion(report_body, research_gap)
        
        # User requested to remove references as this is an intermediate report
        # conclusion_with_references = self.gpt_researcher.add_references(conclusion, self.gpt_researcher.visited_urls)
        
        # Research Gap is integrated into Introduction and Conclusion, not shown as a separate section
        report = f"{introduction}\n\n{toc}\n\n{report_body}\n\n{conclusion}"
        return report
