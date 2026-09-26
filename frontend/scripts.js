// Establish WebSocket connection to the FastAPI backend
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws`;
let ws = null;

function connectWebSocket() {
    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        console.log("Connected to DevAgent backend server via WebSocket.");
        updateActivityLog("✓ Connected to backend WebSocket");
    };

    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleIncomingMessage(data);
        } catch (e) {
            console.log("Raw message received:", event.data);
        }
    };

    ws.onclose = function() {
        console.log("WebSocket connection closed. Reconnecting in 3 seconds...");
        updateActivityLog("⚠ Connection lost. Reconnecting...");
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = function(error) {
        console.error("WebSocket error:", error);
        updateActivityLog("❌ WebSocket error encountered");
    };
}

// Triggered when clicking 'Analyze Repository'
function startAnalysis() {
    const statusText = document.getElementById("status-text");
    statusText.innerText = "Initializing agent loop... Indexing codebase structure.";
    updateActivityLog("✓ Started repository analysis task");

    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = {
            task: "Analyze github-developer-agent codebase structure, architecture, and security.",
            report_type: "research_report",
            report_source: "web"
        };
        
        ws.send("start " + JSON.stringify(payload));
    } else {
        alert("WebSocket connection is not active. Please ensure your backend server is running.");
    }
}

// Handle incoming messages streamed from the Python agent
function handleIncomingMessage(data) {
    const statusText = document.getElementById("status-text");
    
    if (data.type === "logs" || data.output) {
        statusText.innerText = data.output;
        updateActivityLog(`✓ ${data.output}`);
    } else if (data.type === "report") {
        renderReportOutput(data.output);
        updateActivityLog("✓ Final report generated successfully");
    }
}

// Helper to update the right sidebar activity feed dynamically
function updateActivityLog(message) {
    const activityLog = document.getElementById("activity-log");
    if (activityLog) {
        const p = document.createElement("p");
        p.className = "text-slate-300 flex items-center gap-1.5 mt-1";
        p.innerHTML = `<span class="w-1.5 h-1.5 bg-emerald-400 rounded-full"></span> ${message}`;
        activityLog.appendChild(p);
        activityLog.scrollTop = activityLog.scrollHeight;
    }
}

// Render final AI agent output in the center chat panel
function renderReportOutput(reportText) {
    const chatContainer = document.getElementById("chat-container");
    const reportBox = document.createElement("div");
    reportBox.className = "bg-[#0b101c] border border-slate-800 rounded-2xl p-5 space-y-4 mt-4 animate-fade-in";
    
    reportBox.innerHTML = `
        <div class="flex items-center gap-2 text-indigo-400 font-semibold">
            <span>🤖 DevAgent Final Analysis Report</span>
        </div>
        <div class="text-slate-300 leading-relaxed whitespace-pre-wrap text-xs">
            ${reportText}
        </div>
    `;
    chatContainer.appendChild(reportBox);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Initialize connection on page load
window.onload = function() {
    connectWebSocket();
};