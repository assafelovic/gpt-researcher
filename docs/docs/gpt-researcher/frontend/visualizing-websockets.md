# Visualizing Websockets

The GPTR Frontend is powered by Websockets streaming back from the Backend. This allows for real-time updates on the status of your research tasks, as well as the ability to interact with the Backend directly from the Frontend.


## Inspecting Websockets

When running reports via the frontend, you can inspect the websocket messages in the Network Tab.

Here's how: 

![image](https://github.com/user-attachments/assets/15fcb5a4-77ea-4b3b-87d7-55d4b6f80095)


## Am I polling the right URL?

If you're concerned that your frontend isn't hitting the right API Endpoint, you can check the URL in the Network Tab.

Click into the WS request & go to the "Headers" tab

![image](https://github.com/user-attachments/assets/dbd58c1d-3506-411a-852b-e1b133b6f5c8)

For debugging, have a look at the <a href="https://github.com/assafelovic/gpt-researcher/blob/master/frontend/nextjs/helpers/getHost.ts">getHost function.</a>