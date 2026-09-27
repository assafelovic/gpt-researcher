from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import json
import httpx

app = FastAPI(title="DevAgent AI GitHub Developer Agent")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Store session token temporarily in memory
session_store = {"token": None}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page where you can input your Personal Access Token."""
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.post("/login")
async def handle_login(request: Request, token: str = Form(...)):
    """Validate your Personal Access Token against the GitHub API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token.strip()}", "Accept": "application/vnd.github+json"}
        )
        if response.status_code != 200:
            return templates.TemplateResponse(request, "index.html", {
                "request": request, 
                "error": "Invalid Personal Access Token. Please check and try again."
            })
        
        session_store["token"] = token.strip()
        
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve the dashboard after successful token validation."""
    if not session_store["token"]:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@app.get("/api/repos")
async def get_user_repos():
    """Fetch all repositories (public and private) for the authenticated user."""
    token = session_store.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos?sort=updated&per_page=100",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch repositories.")
        
        repos = response.json()
        formatted_repos = [{
            "name": repo["name"],
            "full_name": repo["full_name"],
            "private": repo["private"],
            "html_url": repo["html_url"],
            "language": repo["language"] or "Unknown",
            "updated_at": repo["updated_at"],
            "description": repo.get("description")
        } for repo in repos]
        
        return {"repositories": formatted_repos}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    token = session_store.get("token")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            repo_full_name = payload.get("repo_name", "repository")
            
            await websocket.send_text(json.dumps({
                "type": "logs", 
                "content": f"Fetching commits, file tree, and contributions for '{repo_full_name}'..."
            }))
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
                
                # Fetch recent commits
                commits_resp = await client.get(f"https://api.github.com/repos/{repo_full_name}/commits?per_page=5", headers=headers)
                commits = commits_resp.json() if commits_resp.status_code == 200 else []
                
                # Fetch file tree recursively
                tree_resp = await client.get(f"https://api.github.com/repos/{repo_full_name}/git/trees/HEAD?recursive=1", headers=headers)
                tree_data = tree_resp.json() if tree_resp.status_code == 200 else {}
                file_count = len(tree_data.get("tree", []))

            commit_summaries = "<br>".join([f"- {c['commit']['message']} (by {c['commit']['author']['name']})" for c in commits[:3]]) if isinstance(commits, list) else "No commits found."

            await websocket.send_text(json.dumps({
                "type": "report", 
                "content": f"""
                    <h4>Repository: {repo_full_name}</h4>
                    <p><b>Total Indexed Files:</b> {file_count}</p>
                    <p><b>Recent Commits & Contributions:</b><br>{commit_summaries}</p>
                    <p><b>Status:</b> Codebase synced and ready for AI updates.</p>
                """
            }))
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")