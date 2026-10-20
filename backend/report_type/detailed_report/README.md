## Detailed Reports

Introducing long and detailed reports, built by researching each subtopic of the task in depth and combining the results into a single report.

In this method we do the following:

1. Trigger Initial GPT Researcher report based on task
2. Generate subtopics from research summary
3. For each subtopic the headers of the subtopic report are extracted and accumulated
4. For each subtopic a report is generated making sure that any information about the headers accumulated until now are not re-generated.
5. An additional introduction section is written along with a table of contents constructed from the entire report.
6. The final report is constructed by appending these : Intro + Table of contents + Subsection reports