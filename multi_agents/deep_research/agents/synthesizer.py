import re
from typing import Dict, List, Any
from ...agents.utils.llms import call_model
from ...agents.utils.views import print_agent_output
from .base import DeepResearchAgent

class DeepSynthesizerAgent(DeepResearchAgent):
    """Agent responsible for synthesizing research results"""
    
    async def process_research_results(self, query: str, context: str, num_learnings: int = 3) -> tuple:
        """Process research results to extract learnings and follow-up questions"""
        await self._stream_or_print(f"Synthesizing research results for: {query}", "SYNTHESIZER")
        
        # If context is too long, truncate it
        max_context_length = 100000  # Increased from 15000 to 100000
        if len(context) > max_context_length:
            print_agent_output(
                f"Context too long ({len(context)} chars). Truncating to {max_context_length} chars.",
                "SYNTHESIZER"
            )
            context = context[:max_context_length] + "..."
        
        try:
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
            
            # If no learnings were extracted, create some default ones
            if not learnings:
                print_agent_output("WARNING: No learnings extracted. Creating default learnings.", "SYNTHESIZER")
                
                # Create default learnings based on the query
                learnings = [
                    f"Research on '{query}' found limited specific information.",
                    "The search results may require further analysis or additional sources.",
                    "Consider refining the search query for more targeted results."
                ]
            
            # Store follow-up questions in the state
            follow_up_questions = questions[:num_learnings]
            
            # Return learnings and citations as a tuple
            return learnings[:num_learnings], citations
            
        except Exception as e:
            print_agent_output(f"Error processing research results: {str(e)}. Using default learnings.", "SYNTHESIZER")
            
            # Create default learnings
            default_learnings = [
                f"Research on '{query}' encountered processing issues.",
                "The available information could not be fully synthesized.",
                "Consider trying a different approach or search query."
            ]
            
            # Return default learnings with empty citations
            return default_learnings, {}
        
    async def synthesize(self, query: str, search_results: List[Dict[str, Any]], task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize search results into a coherent context.
        
        Args:
            query: The search query
            search_results: List of search results
            task: Task configuration
            
        Returns:
            Dictionary with synthesized context, sources, and citations
        """
        # Log the action
        await self._stream_or_print(f"Synthesizing search results for: {query}", "SYNTHESIZER")
        
        # Debug log the search results structure
        print_agent_output(f"Received {len(search_results)} search results to synthesize", "SYNTHESIZER")
        
        # Extract content from search results
        content_list = []
        sources = []
        
        # Debug log the structure of the first search result if available
        if search_results and len(search_results) > 0:
            first_result = search_results[0]
            if isinstance(first_result, dict):
                print_agent_output(f"First search result keys: {', '.join(first_result.keys())}", "SYNTHESIZER")
            else:
                print_agent_output(f"First search result is not a dictionary but a {type(first_result)}", "SYNTHESIZER")
        
        for i, result in enumerate(search_results):
            if isinstance(result, dict):
                title = result.get("title", "Unknown Title")
                url = result.get("url", "")
                content = result.get("content", "")
                
                # Debug log each result
                print_agent_output(f"Result {i+1}: Title: {title}, URL: {url}, Content length: {len(content)}", "SYNTHESIZER")
                
                # More robust content extraction - try different keys that might contain content
                if not content and "text" in result:
                    content = result.get("text", "")
                    print_agent_output(f"Using 'text' field instead of 'content' for result {i+1}", "SYNTHESIZER")
                
                if not content and "snippet" in result:
                    content = result.get("snippet", "")
                    print_agent_output(f"Using 'snippet' field instead of 'content' for result {i+1}", "SYNTHESIZER")
                
                if not content and "body" in result:
                    content = result.get("body", "")
                    print_agent_output(f"Using 'body' field instead of 'content' for result {i+1}", "SYNTHESIZER")
                
                # If we still don't have content but have other fields, create a summary from available fields
                if not content:
                    summary_parts = []
                    for key, value in result.items():
                        if key not in ["title", "url"] and isinstance(value, str) and len(value) > 0:
                            summary_parts.append(f"{key}: {value}")
                    
                    if summary_parts:
                        content = "\n".join(summary_parts)
                        print_agent_output(f"Created content from other fields for result {i+1}", "SYNTHESIZER")
                
                if content:
                    content_list.append(f"Source: {title}\nURL: {url}\nContent: {content}")
                    sources.append(result)
                else:
                    print_agent_output(f"No content found for result {i+1}", "SYNTHESIZER")
            else:
                print_agent_output(f"Result {i+1} is not a dictionary but a {type(result)}", "SYNTHESIZER")
        
        # Combine content
        combined_content = "\n\n".join(content_list)
        
        # Log the combined content length
        print_agent_output(f"Combined content length: {len(combined_content)}", "SYNTHESIZER")
        
        # If no content, create a fallback
        if not combined_content:
            print_agent_output("WARNING: No content extracted from search results. Creating fallback content.", "SYNTHESIZER")
            
            # Create a fallback context directly from the search results
            fallback_context = f"# Research on: {query}\n\n"
            
            # Try to extract any useful information from the search results
            for i, result in enumerate(search_results):
                if isinstance(result, dict):
                    title = result.get("title", "Unknown Title")
                    url = result.get("url", "")
                    
                    # Try to extract any text content from any field
                    content_fields = []
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) > 10 and key not in ["title", "url"]:
                            content_fields.append(f"{key}: {value}")
                    
                    snippet = "\n".join(content_fields) if content_fields else ""
                    
                    if not snippet:
                        snippet = "No detailed content available for this source."
                    
                    if title or url or snippet:
                        fallback_context += f"## Source {i+1}: {title}\n"
                        if url:
                            fallback_context += f"URL: {url}\n"
                        fallback_context += f"Summary: {snippet}\n\n"
            
            # If we still don't have any content, create a generic message
            if fallback_context == f"# Research on: {query}\n\n":
                fallback_context += "No specific content could be extracted from the search results. This could be due to:\n\n"
                fallback_context += "1. API limitations or rate limiting\n"
                fallback_context += "2. Search results not containing detailed content\n"
                fallback_context += "3. Technical issues with content extraction\n\n"
                fallback_context += "Consider refining your search query or trying again later."
            
            # Use the fallback context
            return {
                "context": fallback_context,
                "sources": search_results,  # Use the original search results as sources
                "citations": {}
            }
        
        try:
            # Process research results
            learnings, citations = await self.process_research_results(query, combined_content)
            
            # Format learnings into a coherent context
            context_parts = []
            
            # Add query as header
            context_parts.append(f"# Research on: {query}")
            context_parts.append("")  # Empty line
            
            # Add learnings
            for learning in learnings:
                citation = citations.get(learning, "")
                if citation:
                    context_parts.append(f"- {learning} [Source: {citation}]")
                else:
                    context_parts.append(f"- {learning}")
            
            # Combine into final context
            context = "\n".join(context_parts)
            
            # Return synthesized result
            return {
                "context": context,
                "sources": sources,
                "citations": citations
            }
        except Exception as e:
            # Log the error
            print_agent_output(f"Error processing research results: {str(e)}. Using fallback approach.", "SYNTHESIZER")
            
            # Create a simple context from the combined content
            simple_context = f"# Research on: {query}\n\n"
            simple_context += "## Key Information\n\n"
            
            # Add a summary of each source
            for i, source in enumerate(sources):
                title = source.get("title", "Unknown Title")
                url = source.get("url", "")
                content = source.get("content", "")
                
                simple_context += f"### Source {i+1}: {title}\n"
                if url:
                    simple_context += f"URL: {url}\n"
                
                # Add a snippet of the content
                if content:
                    snippet = content[:300] + "..." if len(content) > 300 else content
                    simple_context += f"Summary: {snippet}\n\n"
            
            # Return the simple context
            return {
                "context": simple_context,
                "sources": sources,
                "citations": {}
            } 