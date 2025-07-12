"""Demo script showing LLM visualization concept with an example Mermaid diagram."""

def create_example_diagram() -> str:
    """Create an example of what the LLM interaction visualization looks like"""

    diagram = """graph TD
    Start["🎬 Report Generation Started<br/>Query: AI in Healthcare"]

    Step1["✅ Generate Report Introduction<br/>Model: gpt-4-turbo<br/>Temperature: 0.25<br/>Duration: 2.3s"]

    Step2["✅ Generate Main Report<br/>Model: gpt-4-turbo<br/>Temperature: 0.35<br/>Duration: 8.9s"]

    Step3["✅ Generate Report Conclusion<br/>Model: gpt-4-turbo<br/>Temperature: 0.25<br/>Duration: 1.2s"]

    End["🏁 Report Generated<br/>Total: 12.4s, 4567 tokens"]

    Start --> Step1
    Step1 --> Step2
    Step2 --> Step3
    Step3 --> End

    classDef successStep fill:#d4edda,stroke:#155724,stroke-width:2px
    classDef startEnd fill:#e2e3e5,stroke:#383d41,stroke-width:2px

    class Start,End startEnd
    class Step1,Step2,Step3 successStep"""

    return diagram

if __name__ == "__main__":
    print("Example LLM Interaction Flow Visualization:")
    print("=" * 50)
    print(create_example_diagram())
    print("=" * 50)
    print("This diagram shows the complete flow of LLM interactions during report generation!")
