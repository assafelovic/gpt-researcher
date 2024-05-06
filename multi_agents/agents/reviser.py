from .utils.views import print_agent_output
from .utils.llms import call_model
import json

sample_revision_notes = """
{
  "draft": { 
    draft title: The revised draft that you are submitting for review 
  },
  "revision_notes": Your message to the reviewer about the changes you made to the draft based on their feedback
}
"""

class ReviserAgent:
    def __init__(self):
        pass

    def revise_draft(self, draft_state: dict):
        """
        Review a draft article
        :param draft_state:
        :return:
        """
        review = draft_state.get("review")
        task = draft_state.get("task")
        draft_report = draft_state.get("draft")
        prompt = [{
            "role": "system",
            "content": "You are an expert writer. Your goal is to revise drafts based on reviewer notes."
        }, {
            "role": "user",
            "content": f"""Draft:\n{draft_report}" + "Reviewer's notes:\n{review}\n\n
You have been tasked by your reviewer with revising the following draft, which was written by a non-expert.
If you decide to follow the reviewer's notes, please write a new draft and make sure to address all of the points they raised.
Please keep all other aspects of the draft the same.
You MUST return nothing but a JSON in the following format:
{sample_revision_notes}
"""
        }]

        response = call_model(prompt, model=task.get("model"), response_format='json')
        return json.loads(response)

    def run(self, draft_state: dict):
        draft_title = draft_state.get("title")
        print_agent_output(f"Rewriting draft based on feedback...", agent="REVISOR")
        revision = self.revise_draft(draft_state)
        print_agent_output(f"Revision notes: {revision.get('revision_notes')}", agent="REVISOR")
        return {"draft": revision.get("draft"),
                "revision_notes": revision.get("revision_notes")}
