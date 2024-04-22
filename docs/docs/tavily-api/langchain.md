# Langchain

We're excited to partner with Langchain as their recommended search tool! 🚀
See the [Langchain blog](https://blog.langchain.dev/weblangchain/) for more details.

Tavily API can now empower your Langchain application with real time online information optimized for RAG.

### How to use Tavily API with Langchain
```python
import os
from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain.tools.tavily_search import TavilySearchResults

# set up API key
os.environ["TAVILY_API_KEY"] = "..."

# set up the agent
llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)
search = TavilySearchAPIWrapper()
tavily_tool = TavilySearchResults(api_wrapper=search)

# initialize the agent
agent_chain = initialize_agent(
    [tavily_tool],
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# run the agent
agent_chain.run(
    "What happened in the latest burning man floods?",
)
```

#### Result:
```commandline
    
    
    > Entering new AgentExecutor chain...
    Thought: I'm not aware of the current situation regarding the Burning Man event. I'll need to search for recent news about any flooding that might have affected it.
    Action:
    ```
    {
      "action": "tavily_search_results_json",
      "action_input": {"query": "Burning Man floods latest news"}
    }
    ```
    Observation: [{'url': 'https://www.theguardian.com/culture/2023/sep/03/burning-man-nevada-festival-floods', 'content': 'More on this story\nMore on this story\nBurning Man revelers begin exodus from festival after road reopens\nBurning Man festival-goers trapped in desert as rain turns site to mud\n\nOfficials investigate death at Burning Man as thousands stranded by floods\n\nBurning Man festivalgoers surrounded by mud in Nevada desert – video\nBurning Man attendees roadblocked by climate activists: ‘They have a privileged mindset’\n\nin our favor. We will let you know. It could be sooner, and it could be later,” said an update on the Burning Man website on Saturday evening.'}, {'url': 'https://www.npr.org/2023/09/03/1197497458/the-latest-on-the-burning-man-flooding', 'content': "National\nThe latest on the Burning Man flooding\nClaudia Peschiutta\n\nClaudia Peschiutta\nAuthorities are investigating a death at the Burning Man festival in the Nevada desert after tens of thousands of people are stuck in camps because of rain.\nSCOTT DETROW, HOST:\n\nDETROW: Well, that's NPR's Claudia Peschiutta covered and caked in a lot of mud at Burning Man. Thanks for talking to us.\nPESCHIUTTA: Confirmed.\nDETROW: Stay dry as much as you can.\n\nwith NPR's Claudia Peschiutta, who's at her first burn, and she told me it's muddy where she is, but that she and her camp family have been making the best of things."}, {'url': 'https://www.npr.org/2023/09/03/1197497458/the-latest-on-the-burning-man-flooding', 'content': "National\nThe latest on the Burning Man flooding\nClaudia Peschiutta\n\nClaudia Peschiutta\nAuthorities are investigating a death at the Burning Man festival in the Nevada desert after tens of thousands of people are stuck in camps because of rain.\nSCOTT DETROW, HOST:\n\nDETROW: Well, that's NPR's Claudia Peschiutta covered and caked in a lot of mud at Burning Man. Thanks for talking to us.\nPESCHIUTTA: Confirmed.\nDETROW: Stay dry as much as you can.\n\nwith NPR's Claudia Peschiutta, who's at her first burn, and she told me it's muddy where she is, but that she and her camp family have been making the best of things."}, {'url': 'https://abcnews.go.com/US/burning-man-flooding-happened-stranded-festivalgoers/story?id=102908331', 'content': 'Tens of thousands of Burning Man attendees are now able to leave the festival after a downpour and massive flooding left them stranded over the weekend.\n\nIn 2013, according to a blog post in the "Burning Man Journal," a rainstorm similarly rolled in, unexpectedly "trapping 160 people on the playa overnight."\n\nABC News\nVideo\nLive\nShows\nElection 2024\n538\nStream on\nBurning Man flooding: What happened to stranded festivalgoers?\nSome 64,000 people were still on site Monday as the exodus began.\n\nBurning Man has been hosted for over 30 years, according to a statement from the organizers.'}, {'url': 'https://www.today.com/news/what-is-burning-man-flood-death-rcna103231', 'content': 'Tens of thousands of Burning Man festivalgoers are slowly making their way home from the Nevada desert after muddy conditions from heavy rains made it nearly impossible to leave over the weekend.\n\naccording to burningman.org.\n\nPresident Biden was notified of the situation and, according to a spokesperson, administration officials monitored and received updates on the latest details.\nWhy are people stranded at Burning Man?\n\n"Thank goodness this community knows how to take care of each other," the Instagram page for Burning Man Information Radio wrote on a post predicting more rain.'}]
    Thought:The latest Burning Man event was severely affected by heavy rainfall that led to flooding. This resulted in tens of thousands of festival attendees getting stuck in their camps due to the muddy conditions. As a result, the exodus from the festival was delayed. An unfortunate incident also occurred, with a death being investigated at the festival. The situation was severe enough that President Biden was informed about it and administration officials were monitoring it. However, it seems that the festival goers were able to handle the situation well, as the Burning Man community is known for looking out for each other. This is not the first time a rainstorm has disrupted the Burning Man event; a similar incident occurred in 2013 where a sudden storm trapped people overnight. 
    Action:
    ```
    {
      "action": "Final Answer",
      "action_input": "The latest Burning Man event was severely affected by heavy rainfall that led to flooding. This resulted in tens of thousands of festival attendees getting stuck in their camps due to the muddy conditions, delaying their exit from the festival. An unfortunate incident also occurred, with a death being investigated at the festival. The situation was severe enough that President Biden was informed about it and administration officials were monitoring it. However, the festival goers were able to handle the situation well, as the Burning Man community is known for looking out for each other. This is not the first time a rainstorm has disrupted the Burning Man event; a similar incident occurred in 2013 when a sudden storm trapped people overnight."
    }
    ```
    
    > Finished chain.





    'The latest Burning Man event was severely affected by heavy rainfall that led to flooding. This resulted in tens of thousands of festival attendees getting stuck in their camps due to the muddy conditions, delaying their exit from the festival. An unfortunate incident also occurred, with a death being investigated at the festival. The situation was severe enough that President Biden was informed about it and administration officials were monitoring it. However, the festival goers were able to handle the situation well, as the Burning Man community is known for looking out for each other. This is not the first time a rainstorm has disrupted the Burning Man event; a similar incident occurred in 2013 when a sudden storm trapped people overnight.'
```

