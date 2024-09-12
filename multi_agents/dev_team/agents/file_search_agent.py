from .utils.llms import call_model
import os
sample_json = """
{
  "relevant_file_names": ["README.md", "docs/docs/gpt-researcher/frontend.md", "backend/server.py", "backend/websocket_manager.py", "backend/utils.py"],
}
"""
class FileSearchAgent:
    async def find_relevant_files(self, state):
        
        prompt = [
            {"role": "system", "content": f"""You are the File System Agent responsible for fetching the relevant file names based on the user's query: {state.get('query')}"""},
            {"role": "user", "content": f"""
        
                Here is the repo's directory structure: {state.get("github_data")}

                If the user asks for a file which is not in the directory structure, you should not return it in the response.

                You MUST return nothing but a JSON in the following format (without json markdown): {sample_json}
            """
            }
        ]
        
        response = await call_model(
            prompt=prompt,
            model=state.get("model"),
            response_format="json"
        )
        print("response of file_search_agent_llm_call: ", response, flush=True)
        return {"relevant_file_names": response["relevant_file_names"]}