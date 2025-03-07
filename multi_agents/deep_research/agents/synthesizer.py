import re
from typing import Dict, List, Any
from ...agents.utils.llms import call_model
from .base import DeepResearchAgent

class DeepSynthesizerAgent(DeepResearchAgent):
    """Agent responsible for synthesizing research results"""
    
    async def process_research_results(self, query: str, context: str, num_learnings: int = 3) -> Dict[str, List[str]]:
        """Process research results to extract learnings and follow-up questions"""
        await self._stream_or_print(f"Synthesizing research results for: {query}", "SYNTHESIZER")
        
        prompt = [
            {"role": "system", "content": "You are an expert researcher analyzing search results."},
            {"role": "user",
             "content": f"Given the following research results for the query '{query}', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available. Format each learning as 'Learning [source_url]: <insight>' and each question as 'Question: <question>':\n\n{context}"}
        ]

        response = await call_model(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.4
        )

        lines = response.split('\n')
        learnings = []
        questions = []
        citations = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Learning'):
                url_match = re.search(r'\[(.*?)\]:', line)
                if url_match:
                    url = url_match.group(1)
                    learning = line.split(':', 1)[1].strip()
                    learnings.append(learning)
                    citations[learning] = url
                else:
                    # Try to find URL in the line itself
                    url_match = re.search(
                        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
                    if url_match:
                        url = url_match.group(0)
                        learning = line.replace(url, '').replace('Learning:', '').strip()
                        learnings.append(learning)
                        citations[learning] = url
                    else:
                        learnings.append(line.replace('Learning:', '').strip())
            elif line.startswith('Question:'):
                questions.append(line.replace('Question:', '').strip())

        await self._stream_or_print(f"Extracted {len(learnings)} learnings and {len(questions)} follow-up questions", "SYNTHESIZER")
        return {
            'learnings': learnings[:num_learnings],
            'followUpQuestions': questions[:num_learnings],
            'citations': citations
        } 