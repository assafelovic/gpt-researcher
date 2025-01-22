# All About Logs

This document explains how to interpret the log files generated for each report. These logs provide a detailed record of the research process, from initial task planning to the gathering of information, and finally, the report writing process. Reports may change over time as new features are developed. 
  
## Log File Overview  

The log file is a JSON file that contains a list of events that happened during the research process. Each event is an object with a timestamp, type, and data. The data contains the specific information about the event.

You can find the log file in the `outputs` folder.  

Or you can access the log file from the report page itself by clicking the "Download Logs" button.

For developers, there is an additional `logs` folder that may be useful. See description below for more details.  

## Key Components:

* `timestamp`: The timestamp is in the format `YYYY-MM-DDTHH:MM:SS.ffffff` which is an ISO format. The main timestamp is for the generation of the file itself. The timestamps for the events are when each specific event happened during the research process. 
* `events`: This is an array containing all the logged events during the research task. Each event object has the following structure.
* `timestamp`: The specific time when the event occurred, allowing you to follow the sequence of actions.
* `type`: This will always be "event" for now.
* `data`: Contains specific information about the event. Includes:
* `type`: This indicates the general kind of event (e.g., "logs").
* `content`: A descriptor of what the tool is doing (e.g., "starting\_research", "running\_subquery\_research", "scraping\_content").
* `output`: A more detailed message, which often includes visual indicators (emojis), that is sent to the user when the tool performs the task
* `metadata`: Additional data related to the event. This can be `null` or contain an array of relevant information like URLs.

## Types of Events & Their Significance
Here's a complete breakdown of all the unique `content` types and what they mean. This is a comprehensive list of all the different actions the research tool will perform.
1. **`starting_research`**:
* Indicates that the research process has begun for a given task.
* `output`: Includes the text of the research query.
2. **`agent_generated`**:
* This is an indicator of what the agent is used for this task
* `output`: Will show the name of the agent
3. **`planning_research`**:
* Shows the tool is initially browsing to understand the scope of the request and start planning.
* The `output` indicates the tool is either browsing or doing initial planning.
4. **`subqueries`**:
* Indicates that the tool has created subqueries that it will use for research
* `output`: Lists out all of the subqueries that the tool will be running to perform the research
* `metadata`: An array of strings that contain the subqueries to be run
5. **`running_subquery_research`**:
* Indicates that a specific subquery research is being performed.
* `output`: Shows the specific subquery being run.
6. **`added_source_url`**:
* Signifies a URL that was identified as a relevant source of information.
* `output`: Provides the URL with a checkmark emoji to indicate success.
* `metadata`: Contains the actual URL added.
7. **`researching`**:
* Indicates the tool is actively searching across multiple sources for information.
* `output`: A general message indicating research across multiple sources is happening.
8. **`scraping_urls`**:
* Shows the tool is beginning to scrape content from a group of URLs.
* `output`: Indicates how many URLs the tool will be scraping from.
9. **`scraping_content`**:
* Indicates the tool successfully scraped the content from the URLs.
* `output`: Shows the number of pages that have been successfully scraped.
10. **`scraping_images`**:
* Signifies that images were identified and selected during the scraping process.
* `output`: Shows the number of new images selected and the total images found
* `metadata`: An array containing URLs of the selected images.
11. **`scraping_complete`**:
* Indicates that the scraping process is complete for the URLs.
* `output`: A message stating that the scraping process is complete
12. **`fetching_query_content`**:
* Indicates that the tool is fetching content based on a specific query.
* `output`: The specific query for which content is being fetched
13. **`subquery_context_window`**:
* Indicates the tool is creating a context window for a given subquery to help with more detailed research.
* `output`: A message stating the context window for the subquery is created.
14. **`research_step_finalized`**:
* Indicates that the research portion of a step is finalized.
* `output`: A message stating that the research is complete.
15. **`generating_subtopics`**:
* Signifies that the tool is generating subtopics to guide the report.
* `output`: A message indicating that the tool is generating subtopics.
16. **`subtopics_generated`**:
* Indicates that subtopics have been generated.
* `output`: A message that subtopics have been generated.
17. **`writing_introduction`**:
* Indicates the tool is beginning to write the introduction to the report.
* `output`: A message to the user that the introduction writing has started.
18. **`introduction_written`**:
* Indicates the introduction to the report is finished
* `output`: A message to the user that the introduction writing is complete
19. **`generating_draft_sections`**:
* Shows that the tool is generating draft sections for the report.
* `output`: A message that the report is generating draft sections.
20. **`draft_sections_generated`**:
* Indicates the draft sections of the report are generated.
* `output`: A message to the user that the draft sections have been generated.
21. **`fetching_relevant_written_content`**:
* Indicates the tool is fetching relevant written content for the report.
* `output`: A message to the user that relevant content is being fetched
22. **`writing_report`**:
* Indicates that the tool is starting to compile the research into a report.
* `output`: A message to the user that the report generation has started.
23. **`report_written`**:
* Signifies that the report generation is complete.
* `output`: A message that the report generation is finished.
24. **`relevant_contents_context`**:
* Indicates that a context window for relevant content has been created.
* `output`: A message indicating a context window for relevant content has been created.
25. **`writing_conclusion`**:
* Indicates the tool has started writing the conclusion for the report
* `output`: A message to the user that the conclusion is being written
26. **`conclusion_written`**:
* Indicates the conclusion of the report has been written
* `output`: A message to the user that the conclusion has been written

## How to Use the Logs

* **Troubleshooting:** If the research results are unexpected, the log files can help you understand the exact steps the tool took, including the queries used, the sources it visited, and how the report was generated.
* **Transparency:** The logs provide transparency into the research process. You can see exactly which URLs were visited, which images were selected, and how the report was built.
* **Understanding the Process**: The logs will provide an overview of what the tool does and what each of the steps look like.
* **Reproducibility:** The log files allow users to trace the exact process.

## Example Usage
By looking at the timestamps, you can see the flow of the research task. The logs will show you the subqueries used by the tool to approach the main query, all the URLs used, if images were selected for the research, and all the steps the tool took to generate the report.

## Logs for Developers
In addition to the user-facing log files (detailed and summary reports), the application also generates two types of log files specifically for developers:
1. A `.log` file which is a basic log file format for logging events as they occur
2. A `.json` file which is more structured
Find the logs in the `logs` folder.

### Basic Log File (.log)

* **Format:** Plain text format. Each line represents a log entry.
* **Content:**
	* Timestamps with millisecond precision.
	* Log level: Usually `INFO`, but could include `DEBUG`, `WARNING`, or `ERROR` in a more complex setup.
	* Module name (e.g., "research").
	* Descriptive messages about various processes.
	* Includes data about:
		* Start and end of research tasks
		* Web searches being performed
		* Planning of the research
		* Subqueries generated and their results
		* The sizes of scraped data
		* The size of content found from subqueries
		* The final combined size of all context found
* **Use Cases for Developers:**
	* **Real-time Monitoring:** Can be used to monitor the tool's activity in real time.
	* **Debugging:** Helpful for pinpointing issues by seeing the chronological flow of operations, the size of content collected, etc.
	* **Performance Analysis:** Timestamps can help in identifying bottlenecks by measuring how long certain operations take.
	* **High-level overview**: Allows developers to easily see which steps of the tool were performed, and some basic information like sizes of collected content.
* **Key Differences from User Logs:**
	* Less structured, more for developers to review in real-time.
	* Contains technical information not usually relevant to a non-developer user.
	* Does not have emojis or simplified language.
	* No information on the images collected

### JSON Log File (.json)

* **Format**: Structured JSON format
* **Content**:
	* Timestamps, as in all log files
		* `type` field that can be:
		* `sub_query`: which contains the subquery string along with `scraped_data_size`
		* `content_found`: which includes the `sub_query` and the `content_size`
		* A `content` field which gives a snapshot of the overall research and can contain the final context and sources found from the research for that task
* **Use Cases for Developers**:
	* **Detailed Analysis**: Allows developers to view specific details of how the tool is running, particularly related to the subqueries and the results of the research.
	* **Process Understanding**: Developers can see the different subqueries run and how much content each generated which can lead to better debugging and understanding of the tool.
	* **Data Inspection**: Can be useful for reviewing the generated queries and content sizes.
* **Key Differences from User Logs**:
	* Highly structured and focused on subquery execution, and the results of this process, specifically the sizes of collected information.
	* Does not contain simplified language, emojis, or high-level explanations.
	* Does not contain information on the overall context or the images collected, it mainly focuses on the subquery process.
