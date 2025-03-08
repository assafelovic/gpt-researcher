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
        
        # Calculate metrics for informational purposes only
        citation_ratio = sum(1 for l in learnings if l in citations) / max(1, len(learnings))
        learning_count = len(learnings)
        
        prompt = [
            {"role": "system", "content": """You are an expert research reviewer with high standards. Your task is to evaluate research findings for quality, accuracy, and completeness.

IMPORTANT INSTRUCTION: Do NOT default to a score of 6/10. Be critical and honest in your assessment. Evaluate the actual quality of the research and provide a score that genuinely reflects it.

Research quality varies widely, and your score should reflect this variation:
- Excellent research (8-10): Comprehensive, accurate, well-cited, addresses all aspects
- Good research (6-7): Solid but with some gaps or limitations
- Mediocre research (4-5): Significant gaps, limited citations, or superficial analysis
- Poor research (1-3): Major issues, inaccuracies, or very incomplete

Your evaluation should be thorough and your score should be a true reflection of quality."""},
            {"role": "user",
             "content": f"""Please review the following research findings for the query: '{query}'

Research Findings:
{learnings_text}

Research Statistics:
- Total findings: {learning_count}
- Percentage with citations: {int(citation_ratio * 100)}%

Evaluate these findings on:
1. Accuracy - Are the findings factually correct?
2. Completeness - Do they address the query comprehensively?
3. Quality of sources - Are the sources reliable and diverse?
4. Depth - How in-depth is the analysis?
5. Gaps - What important aspects are missing?

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
            temperature=0.8  # Higher temperature for more variability
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
                    # Extract score more robustly
                    score_text = line.split(':')[1].strip()
                    # Handle different formats like "7/10" or just "7"
                    if '/' in score_text:
                        score = int(score_text.split('/')[0])
                    else:
                        score = int(score_text)
                    review_results['score'] = score
                except Exception as e:
                    # If we can't parse the score, make another call specifically for the score
                    score_prompt = [
                        {"role": "system", "content": "You are a research quality evaluator. Your only task is to provide a numerical score from 1-10."},
                        {"role": "user", "content": f"Based on the research for '{query}', with {learning_count} findings and {int(citation_ratio * 100)}% citation rate, provide a single number from 1-10 representing the quality. Only respond with the number, nothing else."}
                    ]
                    score_response = await call_model(
                        prompt=score_prompt,
                        model="gpt-4o",
                        temperature=0.5
                    )
                    try:
                        review_results['score'] = int(score_response.strip())
                    except:
                        # Last resort fallback
                        review_results['score'] = 5
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
        
        # If we still don't have a score, make a dedicated call for just the score
        if review_results['score'] == 0:
            score_prompt = [
                {"role": "system", "content": "You are a research quality evaluator. Provide a numerical score from 1-10 based on the quality of research."},
                {"role": "user", "content": f"Based on the research for '{query}', with {learning_count} findings and {int(citation_ratio * 100)}% citation rate, provide a single number from 1-10 representing the quality. Only respond with the number, nothing else."}
            ]
            score_response = await call_model(
                prompt=score_prompt,
                model="gpt-4o",
                temperature=0.5
            )
            try:
                review_results['score'] = int(score_response.strip())
            except:
                # Last resort fallback
                review_results['score'] = 5
        
        await self._stream_or_print(f"Review complete. Quality score: {review_results['score']}/10", "REVIEWER")
        return review_results 