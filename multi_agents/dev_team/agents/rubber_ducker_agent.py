from .utils.llms import call_model
from multi_agents.dev_team.agents import GithubAgent
import os
discord_markdown_guide = """
Headers
Don’t forget to add a space between your text and the code to create a header.
To create a header you just need to include a specific number of the hash/pound sign character (#). Use (#) for a big header, (##) for a smaller header, or (###) for an even smaller header as the first character(s) in a new line to make a header. Here is an example of what each header type looks like.

Subtext
Like Headers, you can add subtext to any chat message. To do so, add a (-# ) before the text you want to appear in the subtext. Don’t forget the space after # before your message. For example: 

Subtext works very similarly to Headers, so the (-#) must be at the very beginning of the line in order for it to work.
Masked links
You can use masked links to make text a clickable or pressable hyperlink. To do so, you need to include the text you want displayed in brackets and then the URL in parentheses. For example:

Lists
Don’t forget to add a space between your text and the code to create a header.
You can create a bulleted list using either (-) or (*) in the beginning of each line. For example:

You can also indent your list by adding a space before (-) or (*) at the beginning of each line. For example:

Code Blocks
You can make your own code blocks by wrapping your text in backticks (`). 

If you want to create a multi-line code block, you can do so by wrapping your text in (
), like this beautifully written haiku.

Block Quotes
Don’t forget to add a space between your text and the code to create a header.
Another option is using block quotes. To use a block quote, you just need to put (>) at the beginning of a line of text to create a single block quote. For example:

If you want to add multiple lines to a single block quote, just add (>>>) before the first line.
"""

class RubberDuckerAgent:
    async def think_aloud(self, state):
        github_agent = GithubAgent(github_token=os.environ.get("GITHUB_TOKEN"), repo_name=state.get("repo_name"), branch_name=state.get("branch_name"), vector_store=state.get("vector_store"))

        file_names_to_search = state.get("relevant_file_names")

        # Fetch the matching documents
        matching_docs = await github_agent.search_by_file_name(file_names_to_search)
        # print("matching_docs: ", matching_docs,flush=True)

        prompt = [
            {"role": "system", "content": "You are a rubber duck debugging assistant."},
            {"role": "user", "content": f"""
             
            Here is the developer's question: {state.get('query')}

            Here is the repo's directory structure: {state.get("github_data")}

            Here are some relevant files from the developer's branch: {matching_docs}
                
            If neccessary, please provide the full code snippets 
            & relevant file names to add or edit on the branch in order to solve the developer's question.
            
            Think out loud about the game plan for answering the user's question. 
            Explain your reasoning step by step.

            If it sounds like the user is asking for a feature, 
            or a bug fix, please provide the relevant file names to edit with the relevant code to edit or add within those files

            Please answer in discord markdown style (not as objects) by following this guide: {discord_markdown_guide}
            """}
        ]

        response = await call_model(
            prompt=prompt,
            model=state.get("model")
        )
        return {"rubber_ducker_thoughts": response} 