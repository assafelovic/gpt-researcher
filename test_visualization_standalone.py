#!/usr/bin/env python3
"""Standalone LLM Visualization Test

This demonstrates the practical alternatives to clickable Mermaid diagrams.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def demo_visualization():
    """Demonstrate the enhanced visualization system without circular imports"""

    print("🚀 STANDALONE LLM VISUALIZATION DEMO")
    print("=" * 60)
    print("✅ Mermaid diagrams are NOT clickable in most environments")
    print("✅ Our solution provides practical alternatives that work everywhere!")
    print("=" * 60)

    # Import directly to avoid circular imports
    from gpt_researcher.skills.llm_visualizer import (
        LLMInteractionVisualizer,
        enable_llm_visualization,
        finish_report_visualization,
        get_llm_flow_summary,
        list_llm_interactions,
        show_llm_interaction,
        start_report_visualization,
    )

    # Enable visualization
    enable_llm_visualization()

    # Start a mock report flow
    start_report_visualization(
        query="The future of AI and its impact on software development",
        report_type="research_report"
    )

    # Get the visualizer instance
    visualizer = LLMInteractionVisualizer()

    print("\n📝 Simulating report generation with multiple LLM interactions...")

    # Simulate interactions
    interactions_data: list[dict[str, Any]] = [
        {
            "step_name": "Generate Report Introduction",
            "model": "gpt-4-turbo",
            "provider": "openai",
            "prompt_type": "introduction_prompt",
            "system_message": "You are an expert technical writer. Create compelling introductions for research reports.",
            "user_message": "Write an introduction for a report about 'The future of AI and its impact on software development'",
            "response": "Artificial Intelligence is revolutionizing software development at an unprecedented pace. From automated code generation to intelligent debugging systems, AI is transforming how developers write, test, and maintain software.",
            "success": True,
            "duration": 2.3
        },
        {
            "step_name": "Generate Section: Current AI Tools",
            "model": "gpt-4-turbo",
            "provider": "openai",
            "prompt_type": "section_generation",
            "system_message": "You are researching AI development tools. Provide comprehensive analysis.",
            "user_message": "Analyze current AI tools in software development including GitHub Copilot, Tabnine, and CodeT5",
            "response": "Error: Token limit exceeded",
            "success": False,
            "error": "maximum context length is 4096 tokens, however the messages resulted in 4200 tokens",
            "duration": 1.1,
            "retry_attempt": 0
        },
        {
            "step_name": "Generate Section: Current AI Tools (Retry)",
            "model": "gpt-4-turbo",
            "provider": "openai",
            "prompt_type": "section_generation",
            "system_message": "You are researching AI development tools. Provide concise analysis.",
            "user_message": "Analyze current AI tools: GitHub Copilot, Tabnine, CodeT5 (be concise)",
            "response": "Current AI development tools are transforming coding workflows:\n\n1. **GitHub Copilot**: AI pair programmer\n2. **Tabnine**: Code completion tool\n3. **CodeT5**: Google's code generation model",
            "success": True,
            "duration": 2.8,
            "retry_attempt": 1
        },
        {
            "step_name": "Generate Report Conclusion",
            "model": "gpt-4-turbo",
            "provider": "openai",
            "prompt_type": "conclusion_prompt",
            "system_message": "You write compelling conclusions that synthesize research findings.",
            "user_message": "Write a conclusion summarizing the impact of AI on software development",
            "response": "AI is not replacing software developers—it's amplifying their capabilities. The future belongs to developers who embrace AI as a collaborative partner.",
            "success": True,
            "duration": 1.8
        }
    ]

    # Log each interaction
    for i, data in enumerate(interactions_data):
        print(f"  📍 Logging interaction {i+1}: {data['step_name']}")

        visualizer.log_interaction(
            step_name=data["step_name"],
            model=data["model"],
            provider=data["provider"],
            prompt_type=data["prompt_type"],
            system_message=data["system_message"],
            user_message=data["user_message"],
            response=data["response"],
            full_messages=[
                {"role": "system", "content": data["system_message"]},
                {"role": "user", "content": data["user_message"]},
                {"role": "assistant", "content": data["response"]}
            ],
            temperature=0.7,
            max_tokens=2000,
            success=data["success"],
            error=data.get("error"),
            retry_attempt=data.get("retry_attempt", 0)
        )

        # Add small delay to simulate real processing
        time.sleep(0.1)

    # Finish the flow and generate visualization
    print("\n🎨 Generating comprehensive visualization...")
    finish_report_visualization()

    # Demo the interactive features that work everywhere!
    print("\n" + "🎮" * 30)
    print("🎮 INTERACTIVE FEATURES DEMO (WORKS EVERYWHERE!)")
    print("🎮" * 30)

    print("\n1️⃣ List all interactions:")
    list_llm_interactions()

    print("\n2️⃣ Show detailed view of interaction #2 (the failed one):")
    show_llm_interaction(2)

    print("\n3️⃣ Show detailed view of interaction #3 (the retry):")
    show_llm_interaction(3)

    print("\n4️⃣ Get flow summary:")
    summary: dict[str, Any] | None = get_llm_flow_summary()
    if summary:
        print("📊 Flow Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

    # Show why this is better than clickable Mermaid
    print("\n" + "💡" * 40)
    print("💡 WHY THIS IS BETTER THAN CLICKABLE MERMAID")
    print("💡" * 40)

    print("\n🔍 Comparison:")
    print("  ❌ Clickable Mermaid: Only works in specific web environments")
    print("  ✅ Our Solution: Works in console, Jupyter, web, anywhere!")
    print("  ❌ Clickable Mermaid: Limited to visual clicks")
    print("  ✅ Our Solution: Complete programmatic access + visual")
    print("  ❌ Clickable Mermaid: No easy data export")
    print("  ✅ Our Solution: JSON export + helper functions")

    print("\n📋 Practical Usage:")
    print("  1. Run your GPT-Researcher report generation")
    print("  2. Visualization automatically captures all LLM interactions")
    print("  3. Use helper functions to explore:")
    print("     • list_llm_interactions() - See all interactions")
    print("     • show_llm_interaction(number) - View detailed interaction")
    print("     • get_llm_flow_summary() - Get flow statistics")

    print("\n🎯 MISSION ACCOMPLISHED!")
    print("✅ Complete LLM interaction capture without clickable Mermaid")
    print("✅ Beautiful visual representation that works everywhere")
    print("✅ Practical interactive exploration via commands")
    print("✅ No dependency on specific rendering environments")
    print("✅ Programmatic access to all data")

if __name__ == "__main__":
    try:
        demo_visualization()
        print("\n🎬 Demo completed successfully!")
    except Exception as e:
        print(f"❌ Demo failed: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
