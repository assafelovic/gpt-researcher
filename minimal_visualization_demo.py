#!/usr/bin/env python3
"""Minimal LLM Visualization Demo

This demonstrates the core functionality without any circular import issues.
Shows why practical text-based interaction is better than clickable Mermaid.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMInteraction:
    """Minimal version of LLM interaction for demo"""

    step_name: str
    model: str
    prompt_type: str
    system_message: str
    user_message: str
    response: str
    success: bool
    error: str | None = None
    duration: float = 0.0
    retry_attempt: int = 0
    interaction_id: str = ""

    def __post_init__(self):
        if not self.interaction_id:
            self.interaction_id = (
                f"llm_{int(time.time())}_{hash(self.step_name) % 10000}"
            )


@dataclass
class ReportFlow:
    """Minimal version of report flow for demo"""

    query: str
    report_type: str
    interactions: list[LLMInteraction] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)


class MinimalVisualizer:
    """Minimal visualizer to demonstrate the concept"""

    def __init__(self):
        self.current_flow: ReportFlow | None = None

    def start_flow(self, query: str, report_type: str):
        """Start a new flow"""
        self.current_flow = ReportFlow(query=query, report_type=report_type)
        print(f"🎬 Started flow: {query}")

    def log_interaction(self, **kwargs):
        """Log an LLM interaction"""
        if not self.current_flow:
            return

        interaction = LLMInteraction(**kwargs)
        self.current_flow.interactions.append(interaction)

        # Beautiful real-time output
        status: str = "✅" if interaction.success else "❌"
        print(f"  {status} {interaction.step_name} ({interaction.duration:.1f}s)")
        if interaction.error:
            print(f"    Error: {interaction.error}")

    def list_interactions(self):
        """List all interactions - this WORKS EVERYWHERE!"""
        if not self.current_flow:
            print("❌ No active flow")
            return

        print("\n🔍 Available LLM Interactions:")
        print("─" * 50)
        for i, interaction in enumerate(self.current_flow.interactions):
            status: str = "✅" if interaction.success else "❌"
            retry_info: str = (
                f" (Retry #{interaction.retry_attempt})"
                if interaction.retry_attempt > 0
                else ""
            )

            print(f"  [{i + 1}] {status} {interaction.step_name}")
            print(f"      Type: {interaction.prompt_type}")
            print(f"      Duration: {interaction.duration:.1f}s{retry_info}")
            print(f"      ID: {interaction.interaction_id}")
            print()

        print("💡 Use show_interaction(number) to view details")

    def show_interaction(self, number: int):
        """Show detailed interaction - this WORKS EVERYWHERE!"""
        if not self.current_flow or not self.current_flow.interactions:
            print("❌ No interactions available")
            return

        if number < 1 or number > len(self.current_flow.interactions):
            print(
                f"❌ Invalid number. Available: 1-{len(self.current_flow.interactions)}"
            )
            return

        interaction: LLMInteraction = self.current_flow.interactions[number - 1]

        print("\n" + "🔍" * 50)
        print(f"🔍 DETAILED INTERACTION VIEW: {interaction.interaction_id}")
        print("🔍" * 50)

        status: str = "✅ SUCCESS" if interaction.success else "❌ FAILED"
        print(f"Status: {status}")
        print(f"Step: {interaction.step_name}")
        print(f"Type: {interaction.prompt_type}")
        print(f"Model: {interaction.model}")
        print(f"Duration: {interaction.duration:.1f}s")

        if interaction.retry_attempt > 0:
            print(f"Retry Attempt: #{interaction.retry_attempt}")

        if interaction.error:
            print(f"Error: {interaction.error}")

        print("\n📝 SYSTEM MESSAGE:")
        print("─" * 30)
        print(
            interaction.system_message[:200] + "..."
            if len(interaction.system_message) > 200
            else interaction.system_message
        )

        print("\n👤 USER MESSAGE:")
        print("─" * 30)
        print(
            interaction.user_message[:200] + "..."
            if len(interaction.user_message) > 200
            else interaction.user_message
        )

        print("\n🤖 LLM RESPONSE:")
        print("─" * 30)
        print(
            interaction.response[:200] + "..."
            if len(interaction.response) > 200
            else interaction.response
        )

        print("🔍" * 50)

    def generate_mermaid(self) -> str:
        """Generate static Mermaid diagram - for visual reference only"""
        if not self.current_flow:
            return ""

        diagram: list[str] = ["graph TB"]
        diagram.extend(
            [
                "    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px",
                "    classDef failure fill:#ffebee,stroke:#c62828,stroke-width:2px",
            ]
        )

        query_preview: str = (
            self.current_flow.query[:30] + "..."
            if len(self.current_flow.query) > 30
            else self.current_flow.query
        )
        diagram.append(f'    Start["🎬 Report Generation<br/>{query_preview}"]')

        prev_node = "Start"
        success_steps: list[str] = []
        fail_steps: list[str] = []

        for i, interaction in enumerate(self.current_flow.interactions):
            node_id: str = f"Step{i + 1}"
            status_emoji: str = "✅" if interaction.success else "❌"

            node_content: str = f'"{status_emoji} {interaction.step_name}<br/>{interaction.prompt_type}<br/>📍 #{i + 1}"'
            diagram.append(f"    {node_id}[{node_content}]")
            diagram.append(f"    {prev_node} --> {node_id}")

            if interaction.success:
                success_steps.append(node_id)
            else:
                fail_steps.append(node_id)

            prev_node: str = node_id

        diagram.append('    End["🏁 Complete"]')
        diagram.append(f"    {prev_node} --> End")

        if success_steps:
            diagram.append(f"    class {','.join(success_steps)} success")
        if fail_steps:
            diagram.append(f"    class {','.join(fail_steps)} failure")

        return "\n".join(diagram)


def main():
    """Demonstrate the visualization system"""

    print("🚀 MINIMAL LLM VISUALIZATION DEMO")
    print("=" * 60)
    print("❗ IMPORTANT: Mermaid diagrams are NOT clickable in most environments!")
    print("✅ Our solution provides practical alternatives that work EVERYWHERE!")
    print("=" * 60)

    # Create visualizer
    viz = MinimalVisualizer()

    # Start flow
    viz.start_flow(
        query="The future of AI and its impact on software development",
        report_type="research_report",
    )

    print("\n📝 Simulating report generation...")

    # Simulate interactions
    interactions: list[dict[str, Any]] = [
        {
            "step_name": "Generate Introduction",
            "model": "gpt-4-turbo",
            "prompt_type": "introduction_prompt",
            "system_message": "You are an expert technical writer. Create compelling introductions.",
            "user_message": "Write an introduction about AI's impact on software development",
            "response": "AI is revolutionizing software development through automation and intelligence.",
            "success": True,
            "duration": 2.3,
        },
        {
            "step_name": "Generate Section: AI Tools",
            "model": "gpt-4-turbo",
            "prompt_type": "section_generation",
            "system_message": "Research AI development tools comprehensively.",
            "user_message": "Analyze GitHub Copilot, Tabnine, and CodeT5 with detailed examples",
            "response": "Error: Token limit exceeded",
            "success": False,
            "error": "maximum context length is 4096 tokens, messages resulted in 4200 tokens",
            "duration": 1.1,
            "retry_attempt": 0,
        },
        {
            "step_name": "Generate Section: AI Tools (Retry)",
            "model": "gpt-4-turbo",
            "prompt_type": "section_generation",
            "system_message": "Research AI development tools concisely.",
            "user_message": "Analyze GitHub Copilot, Tabnine, CodeT5 (be concise)",
            "response": "GitHub Copilot provides AI-powered code completion. Tabnine offers intelligent suggestions. CodeT5 enables code generation across languages.",
            "success": True,
            "duration": 2.8,
            "retry_attempt": 1,
        },
        {
            "step_name": "Generate Conclusion",
            "model": "gpt-4-turbo",
            "prompt_type": "conclusion_prompt",
            "system_message": "Write compelling conclusions synthesizing findings.",
            "user_message": "Conclude the AI impact on software development",
            "response": "AI amplifies developer capabilities rather than replacing them. Success depends on embracing AI as a collaborative partner.",
            "success": True,
            "duration": 1.8,
        },
    ]

    # Log interactions
    for interaction in interactions:
        viz.log_interaction(**interaction)
        time.sleep(0.1)  # Simulate processing time

    # Generate static Mermaid for visual reference
    print("\n📊 STATIC MERMAID DIAGRAM (Visual Reference Only):")
    print("─" * 70)
    mermaid: str = viz.generate_mermaid()
    print(mermaid)
    print("─" * 70)
    print("⚠️  This diagram is STATIC - no clicking works in most environments!")
    print("✅ Use the interactive commands below instead!")

    # Demo the interactive features that WORK EVERYWHERE
    print("\n" + "🎮" * 30)
    print("🎮 INTERACTIVE FEATURES (WORK EVERYWHERE!)")
    print("🎮" * 30)

    print("\n1️⃣ List all interactions:")
    viz.list_interactions()

    print("\n2️⃣ Show detailed view of failed interaction (#2):")
    viz.show_interaction(2)

    print("\n3️⃣ Show detailed view of retry interaction (#3):")
    viz.show_interaction(3)

    # Summary
    print("\n" + "💡" * 40)
    print("💡 WHY THIS APPROACH IS SUPERIOR")
    print("💡" * 40)

    comparison: list[tuple[str, str, str]] = [
        (
            "Environment Support",
            "❌ Clickable Mermaid: Web apps only",
            "✅ Our Solution: Console, Jupyter, web, anywhere!",
        ),
        (
            "Data Access",
            "❌ Clickable Mermaid: Visual clicks only",
            "✅ Our Solution: Complete programmatic access",
        ),
        (
            "Setup Required",
            "❌ Clickable Mermaid: Special renderer needed",
            "✅ Our Solution: Zero setup, works out of box",
        ),
        (
            "Error Details",
            "❌ Clickable Mermaid: Limited error display",
            "✅ Our Solution: Complete error tracking",
        ),
        (
            "Developer UX",
            "❌ Clickable Mermaid: Click-dependent",
            "✅ Our Solution: Command-line friendly",
        ),
        (
            "Data Export",
            "❌ Clickable Mermaid: No easy export",
            "✅ Our Solution: Full data access",
        ),
    ]

    for category, bad, good in comparison:
        print(f"\n🔍 {category}:")
        print(f"  {bad}")
        print(f"  {good}")

    print("\n🎯 PRACTICAL USAGE IN GPT-RESEARCHER:")
    print("  1. Enable visualization: enable_llm_visualization()")
    print("  2. Run report generation - interactions are captured automatically")
    print("  3. Explore with commands:")
    print("     • list_llm_interactions() - See all interactions")
    print("     • show_llm_interaction(number) - View detailed interaction")
    print("     • get_llm_flow_summary() - Get statistics")

    print("\n✅ MISSION ACCOMPLISHED:")
    print("  ✅ Complete LLM interaction visualization without clickable Mermaid")
    print("  ✅ Works in ANY environment (console, Jupyter, web)")
    print("  ✅ Beautiful visual output + practical exploration")
    print("  ✅ No dependency on specific rendering environments")
    print("  ✅ Full error tracking and retry visualization")
    print("  ✅ Programmatic access to all data")

    print(
        "\n🎬 Demo Complete! No clickable Mermaid needed - we have better alternatives! 🎯"
    )


if __name__ == "__main__":
    main()
