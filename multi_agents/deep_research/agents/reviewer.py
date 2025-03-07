from typing import Dict, List, Any
from ...agents.utils.llms import call_model
from .base import DeepResearchAgent

class DeepReviewerAgent(DeepResearchAgent):
    """Agent responsible for reviewing and validating research results"""
    
    async def review_research(self, query: str, learnings: List[str], citations: Dict[str, str]) -> Dict[str, Any]:
        """Review research results for quality and completeness"""
        await self._stream_or_print(f"Reviewing research results for: {query}", "REVIEWER")
        
        # Format learnings with citations for review
        formatted_learnings = []
        for learning in learnings:
            citation = citations.get(learning, '')
            if citation:
                formatted_learnings.append(f"{learning} [Source: {citation}]")
            else:
                formatted_learnings.append(learning)
                
        learnings_text = "\n".join(formatted_learnings)
        
        prompt = [
            {"role": "system", "content": "You are an expert research reviewer. Your task is to evaluate research findings for quality, accuracy, and completeness."},
            {"role": "user",
             "content": f"""Please review the following research findings for the query: '{query}'

Research Findings:
{learnings_text}

Evaluate these findings on:
1. Accuracy - Are the findings factually correct?
2. Completeness - Do they address the query comprehensively?
3. Quality of sources - Are the sources reliable and diverse?
4. Gaps - What important aspects are missing?

Format your response as:
Quality Score (1-10): <score>
Strengths: <list strengths>
Weaknesses: <list weaknesses>
Gaps: <list gaps>
Recommendations: <list recommendations>"""}
        ]

        response = await call_model(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.3
        )
        
        # Parse the review results
        lines = response.split('\n')
        review_results = {
            'score': 0,
            'strengths': [],
            'weaknesses': [],
            'gaps': [],
            'recommendations': []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'Quality Score' in line:
                try:
                    score = int(line.split(':')[1].strip().split('/')[0])
                    review_results['score'] = score
                except:
                    pass
            elif line.startswith('Strengths:'):
                current_section = 'strengths'
            elif line.startswith('Weaknesses:'):
                current_section = 'weaknesses'
            elif line.startswith('Gaps:'):
                current_section = 'gaps'
            elif line.startswith('Recommendations:'):
                current_section = 'recommendations'
            elif line and current_section:
                if line.startswith('- '):
                    review_results[current_section].append(line[2:])
                else:
                    review_results[current_section].append(line)
        
        await self._stream_or_print(f"Review complete. Quality score: {review_results['score']}/10", "REVIEWER")
        return review_results 