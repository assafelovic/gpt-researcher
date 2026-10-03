import os
import sys
import base64
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx
from google import genai

app = FastAPI(title="DevAgent - AI GitHub Developer Agent")

app.add_middleware(SessionMiddleware, secret_key="devagent-super-secret-key-change-in-production")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

GITHUB_API_URL = "https://api.github.com"
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/templates/hero-graphic.png")
async def get_hero_graphic():
    image_path = os.path.join(BASE_DIR, "templates", "hero-graphic.png")
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Graphic not found")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, error: str = None):
    return templates.TemplateResponse(request, "index.html", {"request": request, "error": error})

@app.post("/login")
async def login(request: Request, token: str = Form(...)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        )
    
    if response.status_code != 200:
        return templates.TemplateResponse(request, "index.html", {"request": request, "error": "Invalid Personal Access Token."})
    
    user_data = response.json()
    request.session["github_token"] = token
    request.session["github_user"] = user_data.get("login")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get("github_token"):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "dashboard.html", {"request": request, "user": request.session.get("github_user")})

@app.get("/api/repos")
async def get_user_repos(request: Request):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user/repos",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            params={"sort": "updated", "per_page": 50, "affiliation": "owner,collaborator,organization_member"}
        )
    
    if response.status_code != 200:
        return {"repositories": []}
    
    repos = response.json()
    formatted_repos = [{
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "description": repo.get("description"),
        "private": repo.get("private"),
        "language": repo.get("language") or "Mixed",
        "updated_at": repo.get("updated_at")
    } for repo in repos]
    
    return {"repositories": formatted_repos}

@app.get("/api/repo/overview")
async def get_repo_overview(request: Request, owner: str, repo: str):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient() as client:
        repo_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}", headers=headers)
        if repo_res.status_code != 200:
            raise HTTPException(status_code=404, detail="Repository not found")
        repo_data = repo_res.json()
        
        lang_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/languages", headers=headers)
        languages = lang_res.json() if lang_res.status_code == 200 else {}
        
        dependencies = []
        for dep_file in ["package.json", "requirements.txt", "Cargo.toml", "pom.xml", "go.mod", "CMakeLists.txt"]:
            file_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{dep_file}", headers=headers)
            if file_res.status_code == 200:
                try:
                    content = base64.b64decode(file_res.json().get("content", "")).decode("utf-8")
                    dependencies.append({"file": dep_file, "snippet": content[:400]})
                except Exception:
                    pass

    description = repo_data.get("description") or "No description provided."
    dep_text = str(dependencies).lower()
    frameworks = []
    if "fastapi" in dep_text: frameworks.append("FastAPI")
    if "flask" in dep_text: frameworks.append("Flask")
    if "react" in dep_text or "next" in dep_text: frameworks.append("Next.js / React")
    if "express" in dep_text: frameworks.append("Node.js Express")
    if not frameworks: frameworks.append("Core Modular Architecture")

    return {
        "name": repo_data.get("name"),
        "full_name": repo_data.get("full_name"),
        "private": repo_data.get("private"),
        "what_it_does": description,
        "tech_stack": list(languages.keys())[:5],
        "languages": languages,
        "frameworks": frameworks,
        "dependencies": [d["file"] for d in dependencies] if dependencies else ["None detected"]
    }

@app.get("/api/repo/tree")
async def get_repo_tree(request: Request, owner: str, repo: str):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient() as client:
        tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/main?recursive=1", headers=headers)
        if tree_res.status_code != 200:
            tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1", headers=headers)
        if tree_res.status_code != 200:
            return {"files": []}
        tree_data = tree_res.json()
        files = [{"path": item["path"], "type": item["type"]} for item in tree_data.get("tree", []) if item["type"] in ["blob", "tree"]]
    return {"files": files}

@app.get("/api/repo/file")
async def get_repo_file_content(request: Request, owner: str, repo: str, path: str):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient() as client:
        file_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}", headers=headers)
        if file_res.status_code != 200:
            raise HTTPException(status_code=404, detail="File not found")
        try:
            content = base64.b64decode(file_res.json().get("content", "")).decode("utf-8")
        except Exception:
            content = "Binary or unreadable file content."
    return {"path": path, "content": content}

@app.post("/api/repo/analyze-readme")
async def analyze_readme(request: Request):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    owner, repo = body.get("owner"), body.get("repo")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    
    async with httpx.AsyncClient() as client:
        repo_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}", headers=headers)
        repo_data = repo_res.json() if repo_res.status_code == 200 else {}
        
        readme_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/readme", headers=headers)
        readme_content = ""
        if readme_res.status_code == 200:
            try:
                readme_content = base64.b64decode(readme_res.json().get("content", "")).decode("utf-8")
            except Exception:
                pass

    prompt = f"Analyze README quality, missing sections, and generate an improved README.md for {owner}/{repo}. Description: {repo_data.get('description')}. Current README: {readme_content}"
    response = client_ai.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return {"analysis": response.text}

@app.post("/api/repo/code-smells")
async def analyze_code_smells(request: Request):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    owner, repo = body.get("owner"), body.get("repo")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    
    async with httpx.AsyncClient() as client:
        tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/main?recursive=1", headers=headers)
        if tree_res.status_code != 200:
            tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1", headers=headers)
        tree_data = tree_res.json() if tree_res.status_code == 200 else {}
        files = [item["path"] for item in tree_data.get("tree", []) if item["type"] == "blob"]

        code_context = ""
        for kf in [f for f in files if f.endswith(('.py', '.js', '.ts', '.java', '.cpp'))][:6]:
            file_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{kf}", headers=headers)
            if file_res.status_code == 200:
                try:
                    code_context += f"\n--- FILE: {kf} ---\n{base64.b64decode(file_res.json().get('content', '')).decode('utf-8')[:1500]}\n"
                except Exception:
                    pass

    prompt = f"Analyze code smells (Long Functions, Duplicate Code, Naming Problems, Error Handling) for {owner}/{repo}:\n{code_context}"
    response = client_ai.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return {"analysis": response.text}

@app.post("/api/repo/semantic-search")
async def semantic_search(request: Request):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    owner, repo, query = body.get("owner"), body.get("repo"), body.get("query", "")
    if not query:
        return {"results": ""}
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient() as client:
        tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/main?recursive=1", headers=headers)
        if tree_res.status_code != 200:
            tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1", headers=headers)
        tree_data = tree_res.json() if tree_res.status_code == 200 else {}
        files = [item["path"] for item in tree_data.get("tree", []) if item["type"] == "blob"]

        code_chunks = []
        for kf in [f for f in files if f.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.md'))][:15]:
            file_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{kf}", headers=headers)
            if file_res.status_code == 200:
                try:
                    content = base64.b64decode(file_res.json().get("content", "")).decode("utf-8")
                    for i in range(0, len(content), 800):
                        if len(content[i:i+800].strip()) > 50:
                            code_chunks.append({"path": kf, "snippet": content[i:i+800]})
                except Exception:
                    pass

    prompt = f"Semantic RAG Search. Intent: '{query}'. Chunks: {str(code_chunks[:25])}. Select top matching code chunks by meaning."
    response = client_ai.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return {"results": response.text}

@app.post("/api/codebase/query")
async def codebase_query(request: Request):
    token = request.session.get("github_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    query, owner, repo = body.get("query", ""), body.get("owner"), body.get("repo")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    
    async with httpx.AsyncClient() as client:
        tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/main?recursive=1", headers=headers)
        if tree_res.status_code != 200:
            tree_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1", headers=headers)
        tree_data = tree_res.json() if tree_res.status_code == 200 else {}
        files = [item["path"] for item in tree_data.get("tree", []) if item["type"] == "blob"]

        code_context = ""
        for kf in [f for f in files if f.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.json', '.md'))][:6]:
            file_res = await client.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{kf}", headers=headers)
            if file_res.status_code == 200:
                try:
                    code_context += f"\n--- FILE: {kf} ---\n{base64.b64decode(file_res.json().get('content', '')).decode('utf-8')[:1200]}\n"
                except Exception:
                    pass

    prompt = f"Explain codebase for {owner}/{repo}. Question: {query}. Context: {code_context}"
    response = client_ai.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return {"answer": response.text, "indexed_files_count": len(files)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)