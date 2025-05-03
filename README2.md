eed install nodjs 
need make a env file with api key, set to git ignore
download python
download npm

maybe use vm evn

install uvicorn?

  Install (or reinstall) uvicorn in your active environment
powershell
Copy
Edit
# with the virtual‑env activated, or in your base interpreter
python -m pip install uvicorn      # lightweight, cross‑platform
On Windows you should not use the [standard] extras because C‑extensions (uvloop, httptools) don’t compile natively there. 
Stack Overflow

If you’re starting fresh with GPT‑Researcher‑CLI you’ll normally do:

powershell
Copy
Edit
python -m venv .venv
.\.venv\Scripts\Activate            # PowerShell:  .\.venv\Scripts\Activate
python -m pip install -r requirements.txt



python -m pip install uvicorn
$ git clone https://github.com/assafelovic/gpt-researcher.git
or morganross gpt-researcher-CLI
$ cd gpt-researcher
$ pip install -r requirements.txt
$ python uvicorn main:app --reload
uvicorn main:app --reload
test the multi_agents main script

cd multi_agents
pip install -r requirements.txt
python main.py


run the frontend
cd frontend/nextjs
nvm install 18.17.0
nvm use v18.17.0
npm install --legacy-peer-deps
npm run dev


python -m multi_agents.main [OPTIONS]
Options
-t, --config-file: Path to a single JSON configuration file. This file will override the default task.json.
--config-files: Paths to one or more JSON configuration files. These files will be merged with the default task.json, with later files overriding earlier ones in case of key conflicts.
--query-file: Path to a file containing the research query. The file can contain either a JSON object with a "query" key or plain text.
-o, --output-file: Path to write the research report. The file extension (.md, .pdf, or .docx) will determine the output format.
Configuration
The CLI uses a default configuration defined in task.json. You can override this configuration by providing one or more custom configuration files using the --config-file or --config-files options.

The task.json file contains various settings for the research task, such as the research query, desired report format, and agent configurations.
