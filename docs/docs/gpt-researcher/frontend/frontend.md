# Frontend Application

This frontend project aims to enhance the user experience of GPT Researcher, providing an intuitive and efficient interface for automated research. It offers two deployment options to suit different needs and environments.

View a Product Tutorial here: [GPT-Researcher Frontend Tutorial](https://www.youtube.com/watch?v=hIZqA6lPusk)


## NextJS Frontend App

The React app (located in the `frontend` directory) is our Frontend 2.0 which we hope will enable us to display the robustness of the backend on the frontend, as well.

It comes with loads of added features, such as: 
 - a drag-n-drop user interface for uploading and deleting files to be used as local documents by GPTResearcher.
 - a GUI for setting your GPTR environment variables.
 - the ability to trigger the multi_agents flow via the Backend Module or Langgraph Cloud Host (currently in closed beta).
 - stability fixes
 - and more coming soon!

### Run the NextJS React App with Docker

> **Step 1** - [Install Docker](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **Step 2** - Clone the '.env.example' file, add your API Keys to the cloned file and save the file as '.env'

> **Step 3** - Within the docker-compose file comment out services that you don't want to run with Docker.

```bash
docker compose up --build
```

If that doesn't work, try running it without the dash:
```bash
docker compose up --build
```

> **Step 4** - By default, if you haven't uncommented anything in your docker-compose file, this flow will start 2 processes:
 - the Python server running on localhost:8000
 - the React app running on localhost:3000

Visit localhost:3000 on any browser and enjoy researching!


## Other Options: 1: Static Frontend (FastAPI)

A lightweight solution using FastAPI to serve static files.

#### Prerequisites
- Python 3.11+
- pip

#### Setup and Running

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Start the server:
   ```
   python -m uvicorn main:app
   ```

3. Access at `http://localhost:8000`

#### Demo
<iframe height="400" width="700" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/dd6cf08f-b31e-40c6-9907-1915f52a7110" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>


## Yet Another Option: Running NextJS Frontend via CLI

A more robust solution with enhanced features and performance.

#### Prerequisites
- Node.js (v18.17.0 recommended)
- npm

#### Setup and Running

1. Navigate to NextJS directory:
   ```
   cd nextjs
   ```

2. Set up Node.js:
   ```
   nvm install 18.17.0
   nvm use v18.17.0
   ```

3. Install dependencies:
   ```
   npm install --legacy-peer-deps
   ```

4. Start development server:
   ```
   npm run dev
   ```

5. Access at `http://localhost:3000`

Note: Requires backend server on `localhost:8000` as detailed in option 1.

#### Demo
<iframe height="400" width="700" src="https://github.com/user-attachments/assets/092e9e71-7e27-475d-8c4f-9dddd28934a3" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

## Choosing an Option

- Static Frontend: Quick setup, lightweight deployment.
- NextJS Frontend: Feature-rich, scalable, better performance and SEO.

For production, NextJS is recommended.

## Frontend Features

Our frontend enhances GPT-Researcher by providing:

1. Intuitive Research Interface: Streamlined input for research queries.
2. Real-time Progress Tracking: Visual feedback on ongoing research tasks.
3. Interactive Results Display: Easy-to-navigate presentation of findings.
4. Customizable Settings: Adjust research parameters to suit specific needs.
5. Responsive Design: Optimal experience across various devices.

These features aim to make the research process more efficient and user-friendly, complementing GPT-Researcher's powerful agent capabilities.