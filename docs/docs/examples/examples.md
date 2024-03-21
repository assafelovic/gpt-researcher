# Examples

### Getting Started
```python
# install tavily
!pip install tavily-python
```

```python  
# import and connect
from tavily import TavilyClient
client = TavilyClient(api_key="")
```
```python  
# simple query using tavily's advanced search
client.search("What happened in the latest burning man floods?", search_depth="advanced")
```
### Response
```commandline
{'query': 'What happened in the latest burning man floods?',
 'follow_up_questions': ['How severe were the floods at Burning Man?',
  'What were the impacts of the floods?',
  'How did the organizers handle the floods at Burning Man?'],
 'answer': None,
 'images': None,
 'results': [{'content': "This year’s rains opened the floodgates for Burning Man criticism  Give Newsletters Site search Vox main menu Filed under: The Burning Man flameout, explained Climate change — and schadenfreude\xa0— finally caught up to the survivalist cosplayers. Share this story Share  Has Burning Man finally lost its glamour?  September 1, after most of the scheduled events and live performances were canceled due to the weather, Burning Man organizers closed routes in and out of the area, forcing attendees to stay behindShare Attendees look at a rainbow over flooding on a desert plain on September 1, 2023, after heavy rains turned the annual Burning Man festival site in Nevada's Black Rock desert into a mud...",
   'url': 'https://www.vox.com/culture/2023/9/6/23861675/burning-man-2023-mud-stranded-climate-change-playa-foot',
   'score': 0.9797,
   'raw_content': None},
  {'content': 'Tens of thousands of Burning Man festivalgoers are slowly making their way home from the Nevada desert after muddy conditions from heavy rains made it nearly impossible to leave over the weekend.  according to burningman.org.  Though the death at this year\'s Burning Man is still being investigated, a social media hoax was blamed for spreading rumors that it\'s due to a breakout of Ebola.  "Thank goodness this community knows how to take care of each other," the Instagram page for Burning Man Information Radio wrote on a post predicting more rain.News Burning Man attendees make mass exodus after being stranded in the mud at festival A caravan of festivalgoers were backed up as much as eight hours when they were finally allowed to leave...',
   'url': 'https://www.today.com/news/what-is-burning-man-flood-death-rcna103231',
   'score': 0.9691,
   'raw_content': None},
  {'content': '“It was a perfect, typical Burning Man weather until Friday — then the rain started coming down hard," said Phillip Martin, 37. "Then it turned into Mud Fest."  After more than a half-inch (1.3 centimeters) of rain fell Friday, flooding turned the playa to foot-deep mud — closing roads and forcing burners to lean on each other for help.  ABC News Video Live Shows Election 2024 538 Stream on No longer stranded, tens of thousands clean up and head home after Burning Man floods  Mark Fromson, 54, who goes by the name “Stuffy” on the playa, had been staying in an RV, but the rains forced him to find shelter at another camp, where fellow burners provided him food and cover.RENO, Nev. -- The traffic jam leaving the Burning Man festival eased up considerably Tuesday as the exodus from the mud-caked Nevada desert entered another day following massive rain that left tens of thousands of partygoers stranded for days.',
   'url': 'https://abcnews.go.com/US/wireStory/wait-times-exit-burning-man-drop-after-flooding-102936473',
   'score': 0.9648,
   'raw_content': None},
  {'content': 'Burning Man hit by heavy rains, now mud soaked.People there told to conserve food and water as they shelter in place.(Video: Josh Keppel) pic.twitter.com/DuBj0Ejtb8  More on this story Burning Man revelers begin exodus from festival after road reopens Officials investigate death at Burning Man as thousands stranded by floods  Burning Man festival-goers trapped in desert as rain turns site to mud Tens of thousands of ‘burners’ urged to conserve food and water as rain and flash floods sweep Nevada  Burning Man festivalgoers surrounded by mud in Nevada desert – video Burning Man attendees roadblocked by climate activists: ‘They have a privileged mindset’Last year, Burning Man drew approximately 80,000 people. This year, only about 60,000 were expected - with many citing the usual heat and dust and eight-hour traffic jams when they tried to leave.',
   'url': 'https://www.theguardian.com/culture/2023/sep/02/burning-man-festival-mud-trapped-shelter-in-place',
   'score': 0.9618,
   'raw_content': None},
  {'content': 'Skip links Live Navigation menu Live Death at Burning Man investigated in US, thousands stranded by flooding  Attendees trudged through mud, many barefoot or wearing plastic bags on their feet. The revellers were urged to shelter in place and conserve food, water and other supplies.  Thousands of festivalgoers remain stranded as organisers close vehicular traffic to the festival site following storm flooding in Nevada’s desert.  Authorities in Nevada are investigating a death at the site of the Burning Man festival, where thousands of attendees remained stranded after flooding from storms swept through the Nevada desert in3 Sep 2023. Authorities in Nevada are investigating a death at the site of the Burning Man festival, where thousands of attendees remained stranded after flooding from storms swept through the ...',
   'url': 'https://www.aljazeera.com/news/2023/9/3/death-under-investigation-after-storm-flooding-at-burning-man-festival',
   'score': 0.9612,
   'raw_content': None}],
 'response_time': 6.23}
```

### Sample 1: Research Report using Tavily and GPT-4 with Langchain
```python
# install lanchain
!pip install langchain
```

```python
# set up openai api key
openai_api_key = ""
```
```python
# libraries
from langchain.adapters.openai import convert_openai_messages
from langchain_community.chat_models import ChatOpenAI

# setup query
query = "What happened in the latest burning man floods?"

# run tavily search
content = client.search(query, search_depth="advanced")["results"]

# setup prompt
prompt = [{
    "role": "system",
    "content":  f'You are an AI critical thinker research assistant. '\
                f'Your sole purpose is to write well written, critically acclaimed,'\
                f'objective and structured reports on given text.'
}, {
    "role": "user",
    "content": f'Information: """{content}"""\n\n' \
               f'Using the above information, answer the following'\
               f'query: "{query}" in a detailed report --'\
               f'Please use MLA format and markdown syntax.'
}]

# run gpt-4
lc_messages = convert_openai_messages(prompt)
report = ChatOpenAI(model='gpt-4',openai_api_key=openai_api_key).invoke(lc_messages).content

# print report
print(report)
```
### Response
```commandline
# The Burning Man Festival 2023: A Festival Turned Mud Fest

**Abstract:** The Burning Man Festival of 2023 in Nevada’s Black Rock desert will be remembered for a significant event: a heavy rainfall that turned the festival site into a muddy mess, testing the community spirit of the annual event attendees and stranding tens of thousands of festival-goers. 

**Keywords:** Burning Man Festival, flooding, rainfall, mud, community spirit, Nevada, Black Rock desert, stranded attendees, shelter

---
## 1. Introduction

The Burning Man Festival, an annual event known for its art installations, free spirit, and community ethos, faced an unprecedented challenge in 2023 due to heavy rains that flooded the festival site, turning it into a foot-deep mud pit[^1^][^2^]. The festival, held in Nevada's Black Rock desert, is known for its harsh weather conditions, including heat and dust, but this was the first time the event was affected to such an extent by rainfall[^4^].

## 2. Impact of the Rain

The heavy rains started on Friday, and more than a half-inch of rain fell, leading to flooding that turned the playa into a foot-deep mud pit[^2^]. The roads were closed due to the muddy conditions, stranding tens of thousands of festival-goers[^2^][^5^]. The burners, as the attendees are known, were forced to lean on each other for help[^2^].

## 3. Community Spirit Tested

The unexpected weather conditions put the Burning Man community spirit to the test[^1^]. Festival-goers found themselves sheltering in place, conserving food and water, and helping each other out[^3^]. For instance, Mark Fromson, who had been staying in an RV, was forced to find shelter at another camp due to the rains, where fellow burners provided him with food and cover[^2^].

## 4. Exodus After Rain

Despite the challenges, the festival-goers made the best of the situation. Once the rain stopped and things dried up a bit, the party quickly resumed[^3^]. A day later than scheduled, the massive wooden effigy known as the Man was set ablaze[^5^]. As the situation improved, thousands of Burning Man attendees began their mass exodus from the festival site[^5^].

## 5. Conclusion

The Burning Man Festival of 2023 will be remembered for the community spirit shown by the attendees in the face of heavy rainfall and flooding. Although the event was marred by the weather, the festival-goers managed to make the best of the situation, demonstrating the resilience and camaraderie that the Burning Man Festival is known for.

---
**References**

[^1^]: "Attendees walk through a muddy desert plain..." NPR. 2023. https://www.npr.org/2023/09/02/1197441202/burning-man-festival-rains-floods-stranded-nevada.

[^2^]: “'It was a perfect, typical Burning Man weather until Friday...'" ABC News. 2023. https://abcnews.go.com/US/wireStory/wait-times-exit-burning-man-drop-after-flooding-102936473.

[^3^]: "The latest on the Burning Man flooding..." WUNC. 2023. https://www.wunc.org/2023-09-03/the-latest-on-the-burning-man-flooding.

[^4^]: "Burning Man hit by heavy rains, now mud soaked..." The Guardian. 2023. https://www.theguardian.com/culture/2023/sep/02/burning-man-festival-mud-trapped-shelter-in-place.

[^5^]: "One day later than scheduled, the massive wooden effigy known as the Man was set ablaze..." CNN. 2023. https://www.cnn.com/2023/09/05/us/burning-man-storms-shelter-exodus-tuesday/index.html.
```
