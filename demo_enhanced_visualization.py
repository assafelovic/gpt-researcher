#!/usr/bin/env python3
"""Enhanced LLM Visualization Demo

This script demonstrates the enhanced LLM interaction visualization system
with practical alternatives to clickable Mermaid diagrams.

The system captures ALL LLM interactions during report generation and provides:
1. Beautiful console output with full interaction details
2. Static Mermaid diagrams for visual flow representation
3. Interactive text-based menu for exploring interactions
4. Helper functions for easy interaction viewing
5. JSON export for programmatic access
"""
from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from gpt_researcher.skills.llm_visualizer import (
    enable_llm_visualization,
    finish_report_visualization,
    get_llm_flow_summary,
    list_llm_interactions,
    show_llm_interaction,
    start_report_visualization,
)


async def demo_enhanced_visualization() -> None:
    """Demonstrate the enhanced visualization system"""

    print("🚀 GPT-RESEARCHER LLM VISUALIZATION DEMO")
    print("=" * 60)
    print("This demo shows practical alternatives to clickable Mermaid diagrams")
    print("=" * 60)

    # Enable visualization
    enable_llm_visualization()

    # Start a mock report flow
    start_report_visualization(
        query="The future of AI and its impact on software development",
        report_type="research_report",
    )

    # Import here to avoid circular imports
    from gpt_researcher.skills.llm_visualizer import get_llm_visualizer

    visualizer = get_llm_visualizer()

    # Simulate multiple LLM interactions with different scenarios
    print("\n📝 Simulating report generation with multiple LLM interactions...")

    # Introduction generation
    visualizer.log_interaction(
        step_name="Generate Report Introduction",
        model="gpt-4-turbo",
        provider="openai",
        prompt_type="introduction_prompt",
        system_message="You are an expert technical writer. Create compelling introductions for research reports.",
        user_message="Write an introduction for a report about 'The future of AI and its impact on software development'",
        response="Artificial Intelligence is revolutionizing software development at an unprecedented pace. From automated code generation to intelligent debugging systems, AI is transforming how developers write, test, and maintain software. This report examines the current state of AI in software development and projects future trends that will shape the industry.",
        full_messages=[
            {"role": "system", "content": "You are an expert technical writer..."},
            {"role": "user", "content": "Write an introduction for..."},
            {"role": "assistant", "content": "Artificial Intelligence is revolutionizing..."}
        ],
        temperature=0.7,
        max_tokens=2000,
        success=True
    )

    # Section generation with retry
    visualizer.log_interaction(
        step_name="Generate Section: Current AI Tools",
        model="gpt-4-turbo",
        provider="openai",
        prompt_type="section_generation",
        system_message="You are researching AI development tools. Provide comprehensive analysis.",
        user_message="Analyze current AI tools in software development including GitHub Copilot, Tabnine, and CodeT5",
        response="Error: Token limit exceeded",
        success=False,
        error="maximum context length is 4096 tokens, however the messages resulted in 4200 tokens",
        retry_attempt=0
    )

    # Retry with shorter context
    visualizer.log_interaction(
        step_name="Generate Section: Current AI Tools (Retry)",
        model="gpt-4-turbo",
        provider="openai",
        prompt_type="section_generation",
        system_message="You are researching AI development tools. Provide concise analysis.",
        user_message="Analyze current AI tools: GitHub Copilot, Tabnine, CodeT5 (be concise)",
        response="Current AI development tools are transforming coding workflows:\n\n1. **GitHub Copilot**: AI pair programmer that suggests code completions and entire functions based on context.\n2. **Tabnine**: Code completion tool using deep learning to predict and suggest code.\n3. **CodeT5**: Google's code generation model for multiple programming languages.\n\nThese tools increase developer productivity by 20-40% according to recent studies.",
        full_messages=[
            {"role": "system", "content": "You are researching AI development tools..."},
            {"role": "user", "content": "Analyze current AI tools..."},
            {"role": "assistant", "content": "Current AI development tools are transforming..."}
        ],
        temperature=0.5,
        max_tokens=1500,
        success=True,
        retry_attempt=1
    )

    # Future predictions section
    visualizer.log_interaction(
        step_name="Generate Section: Future Predictions",
        model="gpt-4-turbo",
        provider="openai",
        prompt_type="section_generation",
        system_message="You are a technology futurist specializing in AI and software development.",
        user_message="Predict the future of AI in software development for the next 5-10 years",
        response="The next decade will see AI become deeply integrated into every aspect of software development:\n\n**2024-2026**: Mainstream adoption of AI coding assistants, automated testing generation\n**2026-2029**: AI-driven architecture design, autonomous debugging systems\n**2029-2034**: Full-stack AI development teams, natural language to production code\n\nBy 2034, we expect 80% of routine coding tasks to be automated, allowing developers to focus on high-level design and creative problem-solving.",
        success=True,
        temperature=0.8,
        max_tokens=2500
    )

    # Conclusion generation
    visualizer.log_interaction(
        step_name="Generate Report Conclusion",
        model="gpt-4-turbo",
        provider="openai",
        prompt_type="conclusion_prompt",
        system_message="You write compelling conclusions that synthesize research findings.",
        user_message="Write a conclusion summarizing the impact of AI on software development",
        response="AI is not replacing software developers—it's amplifying their capabilities. The future belongs to developers who embrace AI as a collaborative partner, leveraging its strengths in automation and pattern recognition while contributing human creativity, critical thinking, and domain expertise. Organizations that adapt to this AI-augmented development paradigm will gain significant competitive advantages in speed, quality, and innovation.",
        success=True,
        temperature=0.6,
        max_tokens=1800
    )

    # Finish the flow and generate visualization
    print("\n🎨 Generating comprehensive visualization...")
    finish_report_visualization()

    # Demo the interactive features
    print("\n" + "🎮" * 30)
    print("🎮 INTERACTIVE FEATURES DEMO")
    print("🎮" * 30)

    print("\n1️⃣ List all interactions:")
    list_llm_interactions()

    print("\n2️⃣ Show detailed view of interaction #2 (the failed one):")
    show_llm_interaction(2)

    print("\n3️⃣ Show detailed view of interaction #3 (the retry):")
    show_llm_interaction(3)

    print("\n4️⃣ Get flow summary:")
    summary = get_llm_flow_summary()
    if summary:
        print("📊 Flow Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

    # Show practical usage
    print("\n" + "💡" * 40)
    print("💡 PRACTICAL USAGE")
    print("💡" * 40)

    print("\n🔍 How to use this in practice:")
    print("  1. Run your GPT-Researcher report generation")
    print("  2. The visualization automatically captures all LLM interactions")
    print("  3. Use these commands to explore:")
    print("     • list_llm_interactions() - See all interactions")
    print("     • show_llm_interaction(number) - View detailed interaction")
    print("     • get_llm_flow_summary() - Get flow statistics")
    print("     • Mermaid diagram is generated for visual flow representation")

    print("\n📋 Why this is better than clickable Mermaid:")
    print("  ✅ Works in ANY environment (console, Jupyter, web)")
    print("  ✅ Shows complete query/response data")
    print("  ✅ Interactive exploration without needing special rendering")
    print("  ✅ Programmatic access to all data")
    print("  ✅ Clear error visualization with retry tracking")

    # Example of programmatic access
    print("\n🔧 Programmatic access example:")
    visualizer = get_llm_visualizer()
    if visualizer.current_flow:
        failed_interactions = [
            i for i in visualizer.current_flow.interactions
            if not i.success
        ]
        retry_interactions = [
            i for i in visualizer.current_flow.interactions
            if i.retry_attempt > 0
        ]

        print(f"  • Total interactions: {len(visualizer.current_flow.interactions)}")
        print(f"  • Failed interactions: {len(failed_interactions)}")
        print(f"  • Retry interactions: {len(retry_interactions)}")

        if failed_interactions:
            print(f"  • First failure reason: {failed_interactions[0].error}")

    print("\n🎯 MISSION ACCOMPLISHED!")
    print("✅ Complete LLM interaction capture")
    print("✅ Beautiful visual representation")
    print("✅ Practical interactive exploration")
    print("✅ No dependency on clickable Mermaid")
    print("✅ Works everywhere GPT-Researcher runs")


if __name__ == "__main__":
    load_dotenv()

    print("Starting enhanced LLM visualization demo...")
    try:
        asyncio.run(demo_enhanced_visualization())
        print("\n🎬 Demo completed successfully!")
        print("🔍 The visualization now captures EVERYTHING during report generation!")
        print("🎨 No more need for clickable Mermaid - interactive alternatives provided!")
        print("💪 Practical, works-everywhere solution implemented!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
