document.addEventListener("DOMContentLoaded", () => {
    // Check if user is authenticated via local storage or prompt for username
    const storedUser = localStorage.getItem("github_user");
    let currentUser = "PradnyaDange"; // Default fallback handle

    if (storedUser) {
        try {
            const userData = JSON.parse(storedUser);
            currentUser = userData.username || currentUser;
        } catch (e) {
            console.error("Error parsing stored user data:", e);
        }
    }

    // Load repositories automatically on startup
    loadUserRepositories(currentUser);
});

async function loadUserRepositories(username) {
    const container = document.getElementById("my-repositories-container");
    if (!container) return;

    container.innerHTML = `<div class="text-xs text-slate-400 p-4">Loading repositories for @${username}...</div>`;

    try {
        const response = await fetch(`/api/github/user/${username}/repos`);
        const data = await response.json();

        if (response.ok && data.repositories && data.repositories.length > 0) {
            container.innerHTML = "";
            data.repositories.forEach(repo => {
                const repoCard = document.createElement("div");
                repoCard.className = "bg-[#121826] border border-slate-800 p-4 rounded-xl hover:border-indigo-500 transition-all cursor-pointer space-y-2";
                repoCard.innerHTML = `
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-semibold text-white">${repo.name}</span>
                        <span class="text-[10px] px-2 py-0.5 rounded-full ${repo.private ? 'bg-amber-950 text-amber-400 border border-amber-900' : 'bg-emerald-950 text-emerald-400 border border-emerald-900'}">${repo.private ? 'Private' : 'Public'}</span>
                    </div>
                    <p class="text-xs text-slate-400 line-clamp-2">${repo.description || 'No description provided.'}</p>
                    <div class="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/60">
                        <span>⭐ ${repo.stars || 0}</span>
                        <span>💻 ${repo.language || 'Mixed'}</span>
                    </div>
                `;
                repoCard.onclick = () => selectAndAnalyzeRepository(username, repo.name);
                container.appendChild(repoCard);
            });
        } else {
            container.innerHTML = `<div class="text-xs text-rose-400 p-4">No repositories found for @${username}.</div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="text-xs text-rose-400 p-4">Error connecting to GitHub API backend.</div>`;
    }
}

async function selectAndAnalyzeRepository(username, repoName) {
    const titleElement = document.getElementById("selected-repo-title");
    const linkElement = document.getElementById("selected-repo-link");

    if (titleElement) titleElement.innerText = repoName;
    if (linkElement) {
        linkElement.innerText = `github.com/${username}/${repoName}`;
        linkElement.href = `https://github.com/${username}/${repoName}`;
    }

    // Trigger details fetch
    try {
        const response = await fetch(`/api/github/repo/${username}/${repoName}/details`);
        const data = await response.json();

        if (response.ok && data.commits) {
            console.log("Fetched commit history:", data.commits);
        }
    } catch (err) {
        console.error("Failed to load repo commits:", err);
    }
}