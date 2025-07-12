"""LLM Interaction Visualizer for Report Generation

This module provides comprehensive visualization of LLM queries and responses
during the report generation phase of GPT Researcher.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class LLMInteraction:
    """Represents a single LLM interaction with full details"""

    step_name: str
    model: str
    provider: str
    timestamp: float
    prompt_type: str
    system_message: str
    user_message: str
    response: str
    full_messages: list[dict[str, Any]]  # Complete message history
    token_count_estimate: int
    temperature: float
    max_tokens: int | None
    success: bool
    error: str | None = None
    duration: float | None = None
    retry_attempt: int = 0
    interaction_id: str = ""

    def __post_init__(self) -> None:
        """Generate unique interaction ID after initialization"""
        if not self.interaction_id:
            self.interaction_id = f"llm_{int(self.timestamp)}_{hash(self.step_name) % 10000}"


@dataclass
class ReportGenerationFlow:
    """Tracks the complete flow of report generation"""

    query: str
    report_type: str
    start_time: float = field(default_factory=time.time)
    interactions: list[LLMInteraction] = field(default_factory=list)
    flow_steps: list[str] = field(default_factory=list)
    current_step: str = ""
    errors: list[str] = field(default_factory=list)
    successful_interactions: int = 0
    failed_interactions: int = 0


class LLMInteractionVisualizer:
    """Visualizes LLM interactions during report generation with enhanced features"""

    def __init__(
        self,
        enabled: bool = True,
    ) -> None:
        self.enabled: bool = enabled
        self.current_flow: ReportGenerationFlow | None = None
        self.interaction_start_time: float | None = None
        self.is_report_generation_active: bool = False

    def start_report_flow(
        self,
        query: str,
        report_type: str,
    ) -> None:
        """Start tracking a new report generation flow"""
        if not self.enabled:
            return

        self.current_flow = ReportGenerationFlow(query=query, report_type=report_type)
        self.is_report_generation_active = True

        print("\n" + "🎬" * 25)
        print("🎬 STARTING ENHANCED LLM VISUALIZATION FOR REPORT GENERATION 🎬")
        print(f"🎯 Query: {query}")
        print(f"📋 Report Type: {report_type}")
        print("🎬" * 25)

    def start_interaction(
        self,
        step_name: str,
    ) -> None:
        """Mark the start of an LLM interaction"""
        if not self.enabled or not self.current_flow or not self.is_report_generation_active:
            return

        self.current_flow.current_step = step_name
        self.current_flow.flow_steps.append(step_name)
        self.interaction_start_time = time.time()

        print(f"\n🚀 STEP: {step_name}")
        print("─" * 60)

    def log_interaction(
        self,
        step_name: str,
        model: str,
        provider: str,
        prompt_type: str,
        system_message: str,
        user_message: str,
        response: str,
        full_messages: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        success: bool = True,
        error: str | None = None,
        retry_attempt: int = 0,
    ) -> None:
        """Log a complete LLM interaction with full details"""
        if not self.enabled or not self.current_flow or not self.is_report_generation_active:
            return

        duration: float | None = None
        if self.interaction_start_time:
            duration = time.time() - self.interaction_start_time

        # Estimate token count
        token_count: int = self._estimate_token_count(system_message, user_message, response)

        interaction = LLMInteraction(
            step_name=step_name,
            model=model,
            provider=provider,
            timestamp=time.time(),
            prompt_type=prompt_type,
            system_message=system_message,
            user_message=user_message,
            response=response,
            full_messages=full_messages or [],
            token_count_estimate=token_count,
            temperature=temperature,
            max_tokens=max_tokens,
            success=success,
            error=error,
            duration=duration,
            retry_attempt=retry_attempt,
        )

        self.current_flow.interactions.append(interaction)

        if success:
            self.current_flow.successful_interactions += 1
        else:
            self.current_flow.failed_interactions += 1
            if error:
                self.current_flow.errors.append(f"{step_name}: {error}")

        self._print_enhanced_interaction(interaction)

    def _print_enhanced_interaction(
        self,
        interaction: LLMInteraction,
    ) -> None:
        """Print a beautifully formatted interaction with full details"""
        status: str = "✅ SUCCESS" if interaction.success else "❌ FAILED"

        # Header with status
        print(f"┌{'─' * 58}┐")
        print(f"│ {status:<56} │")
        print(f"├{'─' * 58}┤")

        # Basic info
        print(f"│ 🤖 MODEL: {interaction.model} ({interaction.provider})")
        print(f"│ 🎯 TYPE: {interaction.prompt_type}")
        print(f"│ 🌡️  TEMP: {interaction.temperature} | 🔢 MAX_TOKENS: {interaction.max_tokens or 'auto'}")
        print(f"│ ⏱️  DURATION: {interaction.duration:.2f}s" if interaction.duration else "│ ⏱️  DURATION: N/A")
        print(f"│ 📊 EST_TOKENS: {interaction.token_count_estimate}")

        if interaction.retry_attempt > 0:
            print(f"│ 🔄 RETRY: Attempt #{interaction.retry_attempt}")

        if interaction.error:
            print(f"│ 💥 ERROR: {interaction.error[:50]}...")

        print(f"├{'─' * 58}┤")

        # Full system message
        print(f"│ 💬 SYSTEM MESSAGE ({len(interaction.system_message)} chars):")
        print(f"│ {self._format_multiline_text(interaction.system_message, max_lines=3)}")
        print(f"├{'─' * 58}┤")

        # Full user message
        print(f"│ 👤 USER MESSAGE ({len(interaction.user_message)} chars):")
        print(f"│ {self._format_multiline_text(interaction.user_message, max_lines=5)}")
        print(f"├{'─' * 58}┤")

        # Full response
        print(f"│ 🤖 LLM RESPONSE ({len(interaction.response)} chars):")
        print(f"│ {self._format_multiline_text(interaction.response, max_lines=5)}")

        # Full message history if available
        if interaction.full_messages:
            print(f"├{'─' * 58}┤")
            print(f"│ 📜 FULL MESSAGE HISTORY ({len(interaction.full_messages)} messages):")
            for i, msg in enumerate(interaction.full_messages[:3]):  # Show first 3
                role: str = msg.get("role", "unknown")
                content: str = str(msg.get("content", ""))[:100]
                print(f"│   {i+1}. {role}: {content}...")
            if len(interaction.full_messages) > 3:
                print(f"│   ... and {len(interaction.full_messages) - 3} more messages")

        print(f"└{'─' * 58}┘")
        print()

    def _format_multiline_text(
        self,
        text: str,
        max_lines: int = 3,
        max_width: int = 54,
    ) -> str:
        """Format text for display within the box"""
        if not text:
            return "  (empty)"

        lines: str = text.replace("\n", " ").strip()
        if len(lines) <= max_width:
            return f"  {lines}"

        # Split into multiple lines
        result_lines: list[str] = []
        words: list[str] = lines.split()
        current_line: str = ""

        for word in words:
            if len(current_line + " " + word) <= max_width:
                current_line += (" " + word) if current_line else word
            else:
                if current_line:
                    result_lines.append(f"  {current_line}")
                current_line = word
                if len(result_lines) >= max_lines - 1:
                    break

        if current_line and len(result_lines) < max_lines:
            result_lines.append(f"  {current_line}")

        if len(words) > len(current_line.split()) + sum(len(line.split()) for line in result_lines):
            result_lines.append("  ...")

        return "\n│ ".join(result_lines) if result_lines else "  (empty)"

    def generate_visual_flow(self) -> str | None:
        """Generate complete visual flow with interactive alternatives"""
        if not self.enabled or not self.current_flow:
            return None

        _flow_duration: float = time.time() - self.current_flow.start_time

        print("\n" + "🎨" * 25)
        print("🎨 GENERATING COMPREHENSIVE LLM INTERACTION VISUALIZATION 🎨")
        print("🎨" * 25)

        # Print detailed flow summary
        summary: str = self._create_enhanced_flow_summary()
        print(summary)

        # Generate Mermaid diagram (static, for visual representation)
        mermaid: str = self._create_enhanced_mermaid_diagram()
        print("\n📊 MERMAID FLOW DIAGRAM (Static Visual):")
        print("─" * 70)
        print(mermaid)

        # Generate comprehensive exports with exhaustive data
        print("\n📄 COMPREHENSIVE DATA EXPORTS (with exhaustive prompts & responses):")
        print("─" * 70)
        self._generate_comprehensive_exports()

        # Generate interactive alternatives since Mermaid clicks don't work in most environments
        print("\n🖱️  INTERACTIVE ALTERNATIVES (Since Mermaid clicks don't work everywhere):")
        print("─" * 70)
        self._display_interactive_menu()

        # Generate JSON data for programmatic access
        clickable_data: dict[str, Any] = self._generate_clickable_data()
        print("\n📄 JSON EXPORT (for programmatic access):")
        print("─" * 70)
        print(f"Flow ID: {clickable_data.get('flow_id', 'N/A')}")
        print(f"Total Interactions: {len(clickable_data.get('interactions', {}))}")
        print("Data available via: get_llm_visualizer().get_interaction_data(interaction_id)")

        return mermaid

    def _display_interactive_menu(self) -> None:
        """Display an interactive menu for exploring interactions"""
        if not self.current_flow or not self.current_flow.interactions:
            print("  No interactions to explore.")
            return

        print("  🔍 Available Interactions:")
        for i, interaction in enumerate(self.current_flow.interactions):
            status: str = "✅" if interaction.success else "❌"
            retry_info: str = f" (Retry #{interaction.retry_attempt})" if interaction.retry_attempt > 0 else ""
            duration: str = f"{interaction.duration:.1f}s" if interaction.duration else "N/A"

            print(f"    [{i+1}] {status} {interaction.step_name} ({interaction.prompt_type}) - {duration}{retry_info}")
            print(f"         ID: {interaction.interaction_id}")

        print("\n  💡 To view detailed interaction:")
        print("     Python: get_llm_visualizer().show_interaction_details(interaction_id)")
        print("     Or use the helper: show_llm_interaction(interaction_number)")

    def show_interaction_details(self, interaction_id: str) -> None:
        """Show detailed information for a specific interaction"""
        if not self.current_flow:
            print("❌ No active flow to display interactions from.")
            return

        interaction: LLMInteraction | None = None
        for inter in self.current_flow.interactions:
            if inter.interaction_id == interaction_id:
                interaction = inter
                break

        if not interaction:
            print(f"❌ Interaction with ID '{interaction_id}' not found.")
            return

        print("\n" + "🔍" * 50)
        print(f"🔍 DETAILED INTERACTION VIEW: {interaction.interaction_id}")
        print("🔍" * 50)

        status: str = "✅ SUCCESS" if interaction.success else "❌ FAILED"
        print(f"Status: {status}")
        print(f"Step: {interaction.step_name}")
        print(f"Type: {interaction.prompt_type}")
        print(f"Model: {interaction.model} ({interaction.provider})")
        print(f"Duration: {interaction.duration:.2f}s" if interaction.duration else "N/A")
        print(f"Tokens: ~{interaction.token_count_estimate}")
        print(f"Temperature: {interaction.temperature}")
        print(f"Max Tokens: {interaction.max_tokens}")

        if interaction.retry_attempt > 0:
            print(f"Retry Attempt: #{interaction.retry_attempt}")

        if interaction.error:
            print(f"Error: {interaction.error}")

        print("\n📝 SYSTEM MESSAGE:")
        print("─" * 30)
        print(interaction.system_message[:500] + "..." if len(interaction.system_message) > 500 else interaction.system_message)

        print("\n👤 USER MESSAGE:")
        print("─" * 30)
        print(interaction.user_message[:500] + "..." if len(interaction.user_message) > 500 else interaction.user_message)

        print("\n🤖 LLM RESPONSE:")
        print("─" * 30)
        print(interaction.response[:500] + "..." if len(interaction.response) > 500 else interaction.response)

        if len(interaction.full_messages) > 2:
            print(f"\n📚 FULL MESSAGE HISTORY ({len(interaction.full_messages)} messages):")
            print("─" * 30)
            for i, msg in enumerate(interaction.full_messages):
                role: str = msg.get("role", "unknown")
                content: str = str(msg.get("content", ""))
                preview: str = content[:100] + "..." if len(content) > 100 else content
                print(f"  {i+1}. {role.upper()}: {preview}")

        print("🔍" * 50)

    def get_interaction_data(self, interaction_id: str) -> dict[str, Any] | None:
        """Get complete data for a specific interaction"""
        clickable_data: dict[str, Any] = self._generate_clickable_data()
        return clickable_data.get("interactions", {}).get(interaction_id)

    def _create_enhanced_flow_summary(self) -> str:
        """Create an enhanced text summary of the flow"""
        if not self.current_flow:
            return ""

        total_time: float = time.time() - self.current_flow.start_time
        total_interactions: int = len(self.current_flow.interactions)
        successful_interactions: int = self.current_flow.successful_interactions
        failed_interactions: int = self.current_flow.failed_interactions
        total_tokens: int = sum(i.token_count_estimate for i in self.current_flow.interactions)

        models_used: list[str] = list(set(f"{i.model} ({i.provider})" for i in self.current_flow.interactions))

        # Calculate success rate
        success_rate: float = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0

        summary: str = f"""
📋 ENHANCED REPORT GENERATION FLOW SUMMARY
════════════════════════════════════════
🎯 Query: {self.current_flow.query}
📋 Report Type: {self.current_flow.report_type}
⏱️  Total Duration: {total_time:.2f} seconds
📊 Total Interactions: {total_interactions}
✅ Successful: {successful_interactions}
❌ Failed: {failed_interactions}
📈 Success Rate: {success_rate:.1f}%
🔢 Total Tokens: {total_tokens:,}
🎭 Models Used: {', '.join(models_used)}

📊 DETAILED INTERACTION BREAKDOWN:"""

        for i, interaction in enumerate(self.current_flow.interactions, 1):
            status: str = "✅" if interaction.success else "❌"
            duration_str: str = f"{interaction.duration:.2f}s" if interaction.duration else "N/A"
            retry_info: str = f" (Retry #{interaction.retry_attempt})" if interaction.retry_attempt > 0 else ""

            summary += f"\n  {i}. {status} {interaction.step_name} ({interaction.prompt_type}) - {duration_str}{retry_info}"
            if interaction.error:
                summary += f"\n     💥 Error: {interaction.error[:100]}..."

        if self.current_flow.errors:
            summary += f"\n\n🚨 ERRORS ENCOUNTERED ({len(self.current_flow.errors)}):"
            for i, error in enumerate(self.current_flow.errors, 1):
                summary += f"\n  {i}. {error[:150]}..."

        return summary

    def _create_enhanced_mermaid_diagram(self) -> str:
        """Create enhanced Mermaid diagram with better visual organization (without clickable elements)"""
        if not self.current_flow or not self.current_flow.interactions:
            return ""

        diagram: list[str] = ["graph TB"]

        # Enhanced styling
        diagram.extend(
            [
                "    classDef startEnd fill:#e1f5fe,stroke:#0277bd,stroke-width:2px",
                "    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px",
                "    classDef failure fill:#ffebee,stroke:#c62828,stroke-width:2px",
                "    classDef retry fill:#fff3e0,stroke:#ef6c00,stroke-width:2px",
                "    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
            ]
        )

        # Start node with query info
        query_preview: str = self.current_flow.query[:50] + "..." if len(self.current_flow.query) > 50 else self.current_flow.query
        diagram.append(f'    Start["🎬 Report Generation<br/>{query_preview}<br/>📋 {self.current_flow.report_type}"]')

        prev_node: str = "Start"
        branch_nodes: list[str] = []

        # Group interactions by step type for better visualization
        step_groups: dict[str, list[LLMInteraction]] = {}
        for interaction in self.current_flow.interactions:
            step_type: str = interaction.prompt_type or "general"
            if step_type not in step_groups:
                step_groups[step_type] = []
            step_groups[step_type].append(interaction)

        # Create nodes with enhanced information (removed click events since they don't work)
        for i, interaction in enumerate(self.current_flow.interactions):
            node_id: str = f"Step{i+1}"
            status_emoji: str = "✅" if interaction.success else "❌"
            duration_text: str = f"<br/>⏱️ {interaction.duration:.1f}s" if interaction.duration else ""
            token_text: str = f"<br/>🔢 {interaction.token_count_estimate} tokens"
            model_text: str = f"<br/>🤖 {interaction.model}"

            # Add retry information
            retry_text: str = f"<br/>🔄 Retry #{interaction.retry_attempt}" if interaction.retry_attempt > 0 else ""

            # Add interaction number for reference
            reference_text: str = f"<br/>📍 #{i+1}"

            # Create enhanced node with reference number
            node_content: str = f'"{status_emoji} {interaction.step_name}<br/>{interaction.prompt_type}{model_text}{duration_text}{token_text}{retry_text}{reference_text}"'
            diagram.append(f'    {node_id}[{node_content}]')

            # Create connections with enhanced styling
            if interaction.success:
                diagram.append(f'    {prev_node} --> {node_id}')
            else:
                # Failed interactions get different styling
                diagram.append(f'    {prev_node} -.->|❌ Failed| {node_id}')

                # If there's a retry after this failure, show branching
                next_interactions: list[LLMInteraction] = self.current_flow.interactions[i+1:i+3]
                retry_interactions: list[LLMInteraction] = [inter for inter in next_interactions if inter.retry_attempt > 0]
                if retry_interactions:
                    branch_nodes.append(node_id)

            prev_node = node_id

        # End node with summary
        success_rate: float = (
            (self.current_flow.successful_interactions / len(self.current_flow.interactions) * 100)
            if self.current_flow.interactions
            else 0
        )
        end_content: str = f'"🏁 Report Complete<br/>✅ {self.current_flow.successful_interactions}/{len(self.current_flow.interactions)} Success<br/>📈 {success_rate:.0f}% Rate"'
        diagram.append(f'    End[{end_content}]')
        diagram.append(f'    {prev_node} --> End')

        # Add decision nodes for retries and branching
        if branch_nodes:
            for branch_node in branch_nodes:
                decision_id: str = f"Decision_{branch_node}"
                diagram.append(f'    {decision_id}{{"🤔 Retry?"}}')
                diagram.append(f'    {branch_node} --> {decision_id}')

        # Apply CSS classes
        diagram.append('    class Start,End startEnd')

        success_steps: list[str] = []
        fail_steps: list[str] = []
        retry_steps: list[str] = []

        for i, interaction in enumerate(self.current_flow.interactions):
            step_id: str = f"Step{i+1}"
            if interaction.retry_attempt > 0:
                retry_steps.append(step_id)
            elif interaction.success:
                success_steps.append(step_id)
            else:
                fail_steps.append(step_id)

        if success_steps:
            diagram.append(f'    class {",".join(success_steps)} success')
        if fail_steps:
            diagram.append(f'    class {",".join(fail_steps)} failure')
        if retry_steps:
            diagram.append(f'    class {",".join(retry_steps)} retry')

        return '\n'.join(diagram)

    def _generate_clickable_data(self) -> dict[str, Any]:
        """Generate data structure for clickable interactions"""
        if not self.current_flow:
            return {}

        clickable_data: dict[str, Any] = {
            "flow_id": f"flow_{int(self.current_flow.start_time)}",
            "query": self.current_flow.query,
            "report_type": self.current_flow.report_type,
            "interactions": {}
        }

        for interaction in self.current_flow.interactions:
            clickable_data["interactions"][interaction.interaction_id] = {
                "step_name": interaction.step_name,
                "model": interaction.model,
                "provider": interaction.provider,
                "prompt_type": interaction.prompt_type,
                "system_message": interaction.system_message,
                "user_message": interaction.user_message,
                "response": interaction.response,
                "full_messages": interaction.full_messages,
                "success": interaction.success,
                "error": interaction.error,
                "duration": interaction.duration,
                "token_count": interaction.token_count_estimate,
                "temperature": interaction.temperature,
                "max_tokens": interaction.max_tokens,
                "retry_attempt": interaction.retry_attempt,
                "timestamp": interaction.timestamp
            }

        return clickable_data

    def _estimate_token_count(
        self,
        system_msg: str,
        user_msg: str,
        response: str,
    ) -> int:
        """Enhanced token count estimation"""
        # More accurate estimate: ~3.5 characters per token on average
        total_chars: int = len(system_msg) + len(user_msg) + len(response)
        return int(total_chars / 3.5)

    def _truncate_text(
        self,
        text: str,
        max_length: int,
    ) -> str:
        """Truncate text with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def finish_flow(self) -> str | None:
        """Finish the flow and generate final visualization"""
        if not self.enabled or not self.current_flow:
            return None

        self.is_report_generation_active = False
        print("\n" + "🏁" * 25)
        print("🏁 FINISHING LLM VISUALIZATION - GENERATING FINAL DIAGRAM 🏁")
        print("🏁" * 25)

        diagram: str | None = self.generate_visual_flow()

        # Reset for next flow
        self.current_flow = None
        self.interaction_start_time = None

        return diagram

    def is_enabled(self) -> bool:
        """Check if visualization is enabled"""
        return self.enabled

    def is_active(self) -> bool:
        """Check if report generation visualization is currently active"""
        return self.is_report_generation_active

    def enable(self) -> None:
        """Enable visualization"""
        self.enabled = True

    def disable(self) -> None:
        """Disable visualization"""
        self.enabled = False
        self.is_report_generation_active = False

    def _generate_comprehensive_exports(self) -> None:
        """Generate comprehensive exports with exhaustive data in multiple formats"""
        if not self.current_flow or not self.current_flow.interactions:
            print("  No interactions to export.")
            return

        # Export options
        print("  📊 Available Export Formats:")
        print("    1. 📄 Detailed Text Report (exhaustive_text_export)")
        print("    2. 🗂️  JSON Export (exhaustive_json_export)")
        print("    3. 📋 CSV Export (exhaustive_csv_export)")
        print("    4. 📝 Markdown Report (exhaustive_markdown_export)")
        print("\n  💡 To generate exports:")
        print("     get_llm_visualizer().export_exhaustive_data('format')")
        print("     Available formats: 'text', 'json', 'csv', 'markdown'")

    def export_exhaustive_data(self, format_type: str = 'json') -> str:
        """Export exhaustive interaction data in specified format"""
        if not self.current_flow or not self.current_flow.interactions:
            return "No data to export."

        if format_type.lower() == 'json':
            return self._export_exhaustive_json()
        elif format_type.lower() == 'text':
            return self._export_exhaustive_text()
        elif format_type.lower() == 'csv':
            return self._export_exhaustive_csv()
        elif format_type.lower() == 'markdown':
            return self._export_exhaustive_markdown()
        else:
            return f"Unsupported format: {format_type}. Use 'json', 'text', 'csv', or 'markdown'."

    def _export_exhaustive_json(self) -> str:
        """Export complete interaction data as JSON"""
        import json

        export_data: dict[str, Any] = {
            "flow_metadata": {
                "query": self.current_flow.query,
                "report_type": self.current_flow.report_type,
                "start_time": self.current_flow.start_time,
                "total_duration": time.time() - self.current_flow.start_time,
                "total_interactions": len(self.current_flow.interactions),
                "successful_interactions": self.current_flow.successful_interactions,
                "failed_interactions": self.current_flow.failed_interactions,
                "success_rate": (self.current_flow.successful_interactions / len(self.current_flow.interactions) * 100) if self.current_flow.interactions else 0,
                "total_estimated_tokens": sum(i.token_count_estimate for i in self.current_flow.interactions),
                "errors": self.current_flow.errors
            },
            "interactions": []
        }

        for i, interaction in enumerate(self.current_flow.interactions):
            interaction_data: dict[str, Any] = {
                "sequence_number": i + 1,
                "interaction_id": interaction.interaction_id,
                "step_name": interaction.step_name,
                "model": interaction.model,
                "provider": interaction.provider,
                "timestamp": interaction.timestamp,
                "prompt_type": interaction.prompt_type,
                "temperature": interaction.temperature,
                "max_tokens": interaction.max_tokens,
                "success": interaction.success,
                "error": interaction.error,
                "duration": interaction.duration,
                "retry_attempt": interaction.retry_attempt,
                "token_count_estimate": interaction.token_count_estimate,

                # EXHAUSTIVE DATA - Full prompts and responses
                "exhaustive_system_message": interaction.system_message,
                "exhaustive_user_message": interaction.user_message,
                "exhaustive_response": interaction.response,
                "exhaustive_full_messages": interaction.full_messages,

                # Character counts for reference
                "system_message_length": len(interaction.system_message),
                "user_message_length": len(interaction.user_message),
                "response_length": len(interaction.response),
                "full_messages_count": len(interaction.full_messages)
            }
            export_data["interactions"].append(interaction_data)

        json_output: str = json.dumps(export_data, indent=2, default=str)

        # Save to file
        filename: str = f"llm_interactions_exhaustive_{int(time.time())}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"✅ Exhaustive JSON export saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON file: {e}")

        return json_output

    def _export_exhaustive_text(self) -> str:
        """Export complete interaction data as detailed text report"""
        report_lines: list[str] = []

        # Header
        report_lines.extend([
            "=" * 80,
            "EXHAUSTIVE LLM INTERACTION REPORT",
            "=" * 80,
            f"Query: {self.current_flow.query}",
            f"Report Type: {self.current_flow.report_type}",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Duration: {time.time() - self.current_flow.start_time:.2f} seconds",
            f"Total Interactions: {len(self.current_flow.interactions)}",
            f"Success Rate: {(self.current_flow.successful_interactions / len(self.current_flow.interactions) * 100):.1f}%",
            "=" * 80,
            ""
        ])

        # Detailed interactions
        for i, interaction in enumerate(self.current_flow.interactions):
            status = "✅ SUCCESS" if interaction.success else "❌ FAILED"

            report_lines.extend([
                f"INTERACTION #{i + 1}: {interaction.step_name}",
                "-" * 80,
                f"Status: {status}",
                f"ID: {interaction.interaction_id}",
                f"Model: {interaction.model} ({interaction.provider})",
                f"Type: {interaction.prompt_type}",
                f"Duration: {interaction.duration:.2f}s" if interaction.duration else "Duration: N/A",
                f"Temperature: {interaction.temperature}",
                f"Max Tokens: {interaction.max_tokens}",
                f"Estimated Tokens: {interaction.token_count_estimate}",
                f"Retry Attempt: {interaction.retry_attempt}" if interaction.retry_attempt > 0 else "",
                f"Error: {interaction.error}" if interaction.error else "",
                "",
                "EXHAUSTIVE SYSTEM MESSAGE:",
                "~" * 40,
                interaction.system_message,
                "",
                "EXHAUSTIVE USER MESSAGE:",
                "~" * 40,
                interaction.user_message,
                "",
                "EXHAUSTIVE LLM RESPONSE:",
                "~" * 40,
                interaction.response,
                ""
            ])

            if interaction.full_messages:
                report_lines.extend([
                    "EXHAUSTIVE FULL MESSAGE HISTORY:",
                    "~" * 40
                ])
                for j, msg in enumerate(interaction.full_messages):
                    role: str = msg.get("role", "unknown")
                    content: str = str(msg.get("content", ""))
                    report_lines.extend([
                        f"Message {j + 1} ({role.upper()}):",
                        content,
                        ""
                    ])

            report_lines.extend(["=" * 80, ""])

        report_text: str = "\n".join(report_lines)

        # Save to file
        filename: str = f"llm_interactions_exhaustive_{int(time.time())}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"✅ Exhaustive text report saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save text file: {e}")

        return report_text

    def _export_exhaustive_csv(self) -> str:
        """Export interaction data as CSV (with truncated content for readability)"""
        import csv
        import io

        output: io.StringIO = io.StringIO()

        fieldnames: list[str] = [
            'sequence_number', 'interaction_id', 'step_name', 'model', 'provider',
            'prompt_type', 'success', 'duration', 'temperature', 'max_tokens',
            'token_count_estimate', 'retry_attempt', 'error',
            'system_message_length', 'user_message_length', 'response_length',
            'system_message_preview', 'user_message_preview', 'response_preview',
            'exhaustive_system_message', 'exhaustive_user_message', 'exhaustive_response'
        ]

        writer: csv.DictWriter = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for i, interaction in enumerate(self.current_flow.interactions):
            row: dict[str, Any] = {
                'sequence_number': i + 1,
                'interaction_id': interaction.interaction_id,
                'step_name': interaction.step_name,
                'model': interaction.model,
                'provider': interaction.provider,
                'prompt_type': interaction.prompt_type,
                'success': interaction.success,
                'duration': interaction.duration,
                'temperature': interaction.temperature,
                'max_tokens': interaction.max_tokens,
                'token_count_estimate': interaction.token_count_estimate,
                'retry_attempt': interaction.retry_attempt,
                'error': interaction.error or '',
                'system_message_length': len(interaction.system_message),
                'user_message_length': len(interaction.user_message),
                'response_length': len(interaction.response),
                'system_message_preview': interaction.system_message[:100] + '...' if len(interaction.system_message) > 100 else interaction.system_message,
                'user_message_preview': interaction.user_message[:100] + '...' if len(interaction.user_message) > 100 else interaction.user_message,
                'response_preview': interaction.response[:100] + '...' if len(interaction.response) > 100 else interaction.response,

                # EXHAUSTIVE DATA - Full content
                'exhaustive_system_message': interaction.system_message,
                'exhaustive_user_message': interaction.user_message,
                'exhaustive_response': interaction.response
            }
            writer.writerow(row)

        csv_content: str = output.getvalue()
        output.close()

        # Save to file
        filename: str = f"llm_interactions_exhaustive_{int(time.time())}.csv"
        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)
            print(f"✅ Exhaustive CSV export saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save CSV file: {e}")

        return csv_content

    def _export_exhaustive_markdown(self) -> str:
        """Export complete interaction data as Markdown report"""
        md_lines: list[str] = []

        # Header
        md_lines.extend([
            "# Exhaustive LLM Interaction Report",
            "",
            f"**Query:** {self.current_flow.query}",
            f"**Report Type:** {self.current_flow.report_type}",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Duration:** {time.time() - self.current_flow.start_time:.2f} seconds",
            f"**Total Interactions:** {len(self.current_flow.interactions)}",
            f"**Success Rate:** {(self.current_flow.successful_interactions / len(self.current_flow.interactions) * 100):.1f}%",
            "",
            "---",
            ""
        ])

        # Table of Contents
        md_lines.extend([
            "## Table of Contents",
            ""
        ])
        for i, interaction in enumerate(self.current_flow.interactions):
            status_emoji: str = "✅" if interaction.success else "❌"
            md_lines.append(f"{i + 1}. [{status_emoji} {interaction.step_name}](#interaction-{i + 1})")
        md_lines.extend(["", "---", ""])

        # Detailed interactions
        for i, interaction in enumerate(self.current_flow.interactions):
            status_emoji = "✅" if interaction.success else "❌"

            md_lines.extend([
                f"## Interaction #{i + 1}: {interaction.step_name}",
                "",
                f"**Status:** {status_emoji} {'SUCCESS' if interaction.success else 'FAILED'}",
                f"**ID:** `{interaction.interaction_id}`",
                f"**Model:** {interaction.model} ({interaction.provider})",
                f"**Type:** {interaction.prompt_type}",
                f"**Duration:** {interaction.duration:.2f}s" if interaction.duration else "**Duration:** N/A",
                f"**Temperature:** {interaction.temperature}",
                f"**Max Tokens:** {interaction.max_tokens}",
                f"**Estimated Tokens:** {interaction.token_count_estimate:,}",
            ])

            if interaction.retry_attempt > 0:
                md_lines.append(f"**Retry Attempt:** #{interaction.retry_attempt}")

            if interaction.error:
                md_lines.extend([
                    f"**Error:** {interaction.error}",
                    ""
                ])

            md_lines.extend(
                [
                    "",
                    "### Exhaustive System Message",
                    "",
                    "```",
                    interaction.system_message,
                    "```",
                    "",
                    "### Exhaustive User Message",
                    "",
                    "```",
                    interaction.user_message,
                    "```",
                    "",
                    "### Exhaustive LLM Response",
                    "",
                    "```",
                    interaction.response,
                    "```",
                    "",
                ]
            )

            if interaction.full_messages:
                md_lines.extend([
                    "### Full Message History",
                    ""
                ])
                for j, msg in enumerate(interaction.full_messages):
                    role: str = msg.get("role", "unknown")
                    content: str = str(msg.get("content", ""))
                    md_lines.extend([
                        f"#### Message {j + 1} ({role.upper()})",
                        "",
                        "```",
                        content,
                        "```",
                        ""
                    ])

            md_lines.extend(["---", ""])

        markdown_content: str = "\n".join(md_lines)

        # Save to file
        filename: str = f"llm_interactions_exhaustive_{int(time.time())}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"✅ Exhaustive Markdown report saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save Markdown file: {e}")

        return markdown_content


# Global instance
_global_visualizer: LLMInteractionVisualizer | None = None


def get_llm_visualizer() -> LLMInteractionVisualizer:
    """Get the global LLM visualizer instance"""
    global _global_visualizer
    if _global_visualizer is None:
        _global_visualizer = LLMInteractionVisualizer()
    return _global_visualizer


def enable_llm_visualization() -> None:
    """Enable LLM visualization globally"""
    get_llm_visualizer().enable()


def disable_llm_visualization() -> None:
    """Disable LLM visualization globally"""
    get_llm_visualizer().disable()


def start_report_visualization(query: str, report_type: str) -> None:
    """Start report visualization"""
    get_llm_visualizer().start_report_flow(query, report_type)


def finish_report_visualization() -> str | None:
    """Finish report visualization and return diagram"""
    return get_llm_visualizer().finish_flow()


def show_llm_interaction(interaction_number: int) -> None:
    """Helper function to show interaction details by number (1-indexed)"""
    visualizer: LLMInteractionVisualizer = get_llm_visualizer()
    if not visualizer.current_flow or not visualizer.current_flow.interactions:
        print("❌ No active flow or interactions available.")
        return

    if interaction_number < 1 or interaction_number > len(visualizer.current_flow.interactions):
        print(f"❌ Invalid interaction number. Available: 1-{len(visualizer.current_flow.interactions)}")
        return

    interaction: LLMInteraction = visualizer.current_flow.interactions[interaction_number - 1]
    visualizer.show_interaction_details(interaction.interaction_id)


def list_llm_interactions() -> None:
    """Helper function to list all available interactions"""
    visualizer: LLMInteractionVisualizer = get_llm_visualizer()
    if not visualizer.current_flow or not visualizer.current_flow.interactions:
        print("❌ No active flow or interactions available.")
        return

    print("\n🔍 Available LLM Interactions:")
    print("─" * 50)
    for i, interaction in enumerate(visualizer.current_flow.interactions):
        status: str = "✅" if interaction.success else "❌"
        retry_info: str = f" (Retry #{interaction.retry_attempt})" if interaction.retry_attempt > 0 else ""
        duration: str = f"{interaction.duration:.1f}s" if interaction.duration else "N/A"

        print(f"  [{i+1}] {status} {interaction.step_name}")
        print(f"      Type: {interaction.prompt_type}")
        print(f"      Duration: {duration}{retry_info}")
        print(f"      Model: {interaction.model}")
        print(f"      ID: {interaction.interaction_id}")
        print()

    print("💡 Use show_llm_interaction(number) to view details")


def get_llm_flow_summary() -> dict[str, Any] | None:
    """Get summary of current LLM flow"""
    visualizer: LLMInteractionVisualizer = get_llm_visualizer()
    if not visualizer.current_flow:
        return None

    return {
        "query": visualizer.current_flow.query,
        "report_type": visualizer.current_flow.report_type,
        "total_interactions": len(visualizer.current_flow.interactions),
        "successful_interactions": visualizer.current_flow.successful_interactions,
        "failed_interactions": visualizer.current_flow.failed_interactions,
        "success_rate": (
            visualizer.current_flow.successful_interactions / len(visualizer.current_flow.interactions) * 100
            if visualizer.current_flow.interactions
            else 0
        ),
        "total_duration": time.time() - visualizer.current_flow.start_time,
        "interactions": [
            {
                "id": interaction.interaction_id,
                "step_name": interaction.step_name,
                "success": interaction.success,
                "duration": interaction.duration,
            }
            for interaction in visualizer.current_flow.interactions
        ],
    }


def export_exhaustive_llm_data(format_type: str = 'json') -> str:
    """Export exhaustive LLM interaction data with full prompts and responses

    Args:
        format_type: Export format - 'json', 'text', 'csv', or 'markdown'

    Returns:
        Exported data as string, also saves to file

    Example:
        # Export all data as JSON with full prompts/responses
        json_data = export_exhaustive_llm_data('json')

        # Export as detailed text report
        text_report = export_exhaustive_llm_data('text')

        # Export as CSV for analysis
        csv_data = export_exhaustive_llm_data('csv')

        # Export as Markdown for documentation
        md_report = export_exhaustive_llm_data('markdown')
    """
    visualizer: LLMInteractionVisualizer = get_llm_visualizer()
    return visualizer.export_exhaustive_data(format_type)


def get_exhaustive_interaction_data(interaction_id: str) -> dict[str, Any] | None:
    """Get complete exhaustive data for a specific interaction including full prompts and responses

    Args:
        interaction_id: The interaction ID to retrieve

    Returns:
        Complete interaction data with exhaustive prompts and responses
    """
    visualizer: LLMInteractionVisualizer = get_llm_visualizer()
    if not visualizer.current_flow:
        return None

    for interaction in visualizer.current_flow.interactions:
        if interaction.interaction_id == interaction_id:
            return {
                "interaction_id": interaction.interaction_id,
                "step_name": interaction.step_name,
                "model": interaction.model,
                "provider": interaction.provider,
                "prompt_type": interaction.prompt_type,
                "success": interaction.success,
                "duration": interaction.duration,
                "temperature": interaction.temperature,
                "max_tokens": interaction.max_tokens,
                "token_count_estimate": interaction.token_count_estimate,
                "retry_attempt": interaction.retry_attempt,
                "error": interaction.error,

                # EXHAUSTIVE DATA - Full prompts and responses
                "exhaustive_system_message": interaction.system_message,
                "exhaustive_user_message": interaction.user_message,
                "exhaustive_response": interaction.response,
                "exhaustive_full_messages": interaction.full_messages,

                # Metadata
                "system_message_length": len(interaction.system_message),
                "user_message_length": len(interaction.user_message),
                "response_length": len(interaction.response),
                "timestamp": interaction.timestamp
            }

    return None


def print_exhaustive_interaction(interaction_id: str) -> None:
    """Print complete exhaustive data for a specific interaction

    Args:
        interaction_id: The interaction ID to display
    """
    data: dict[str, Any] | None = get_exhaustive_interaction_data(interaction_id)
    if not data:
        print(f"❌ Interaction '{interaction_id}' not found.")
        return

    print("\n" + "🔍" * 60)
    print(f"🔍 EXHAUSTIVE INTERACTION DATA: {interaction_id}")
    print("🔍" * 60)

    # Metadata
    status: str = "✅ SUCCESS" if data["success"] else "❌ FAILED"
    print(f"Status: {status}")
    print(f"Step: {data['step_name']}")
    print(f"Model: {data['model']} ({data['provider']})")
    print(f"Type: {data['prompt_type']}")
    print(f"Duration: {data['duration']:.2f}s" if data['duration'] else "N/A")
    print(f"Temperature: {data['temperature']}")
    print(f"Max Tokens: {data['max_tokens']}")
    print(f"Estimated Tokens: {data['token_count_estimate']:,}")

    if data['retry_attempt'] > 0:
        print(f"Retry Attempt: #{data['retry_attempt']}")

    if data['error']:
        print(f"Error: {data['error']}")

    # Exhaustive data
    print("\n📊 DATA SIZES:")
    print(f"System Message: {data['system_message_length']:,} characters")
    print(f"User Message: {data['user_message_length']:,} characters")
    print(f"Response: {data['response_length']:,} characters")
    print(f"Full Messages: {len(data['exhaustive_full_messages'])} messages")

    print("\n📝 EXHAUSTIVE SYSTEM MESSAGE:")
    print("─" * 50)
    print(data['exhaustive_system_message'])

    print("\n👤 EXHAUSTIVE USER MESSAGE:")
    print("─" * 50)
    print(data['exhaustive_user_message'])

    print("\n🤖 EXHAUSTIVE LLM RESPONSE:")
    print("─" * 50)
    print(data['exhaustive_response'])

    if data['exhaustive_full_messages']:
        print("\n📚 EXHAUSTIVE FULL MESSAGE HISTORY:")
        print("─" * 50)
        for i, msg in enumerate(data['exhaustive_full_messages']):
            role: str = msg.get("role", "unknown")
            content: str = str(msg.get("content", ""))
            print(f"\nMessage {i + 1} ({role.upper()}):")
            print(content)

    print("🔍" * 60)


# Convenience aliases for easier access
export_llm_json: Callable[[], str] = lambda: export_exhaustive_llm_data("json")  # noqa: E731
export_llm_text: Callable[[], str] = lambda: export_exhaustive_llm_data("text")  # noqa: E731
export_llm_csv: Callable[[], str] = lambda: export_exhaustive_llm_data("csv")  # noqa: E731
export_llm_markdown: Callable[[], str] = lambda: export_exhaustive_llm_data("markdown")  # noqa: E731
