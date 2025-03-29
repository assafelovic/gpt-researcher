function toggleAdvanced() {
    const advancedSection = document.getElementById("advancedSection");
    const isChecked = document.getElementById("advancedToggle").checked;
    advancedSection.classList.toggle("visible", isChecked);

    localStorage.setItem("showAdvanced", isChecked ? "true" : "false");
}

function setupConsoleLogRedirect() {
    const originalConsoleLog = console.log;

    console.log = function () {
        originalConsoleLog.apply(console, arguments);

        const output = document.getElementById("output");
        if (output && output.style.display !== "none") {
            const message = Array.from(arguments)
                .map((arg) => {
                    if (typeof arg === "object") {
                        try {
                            return JSON.stringify(arg, null, 2);
                        } catch (e) {
                            return String(arg);
                        }
                    }
                    return String(arg);
                })
                .join(" ");

            const logSpan = document.createElement("span");
            logSpan.className = "log-info";
            logSpan.textContent = `[LOG] ${message}`;

            output.appendChild(logSpan);
            output.appendChild(document.createTextNode("\n"));

            output.scrollTop = output.scrollHeight;
        }
    };

    const originalConsoleError = console.error;
    console.error = function () {
        originalConsoleError.apply(console, arguments);

        const output = document.getElementById("output");
        if (output && output.style.display !== "none") {
            const message = Array.from(arguments)
                .map((arg) => {
                    if (typeof arg === "object") {
                        try {
                            return JSON.stringify(arg, null, 2);
                        } catch (e) {
                            return String(arg);
                        }
                    }
                    return String(arg);
                })
                .join(" ");

            const logSpan = document.createElement("span");
            logSpan.className = "log-error";
            logSpan.textContent = `[ERROR] ${message}`;

            output.appendChild(logSpan);
            output.appendChild(document.createTextNode("\n"));

            output.scrollTop = output.scrollHeight;
        }
    };

    const originalConsoleWarn = console.warn;
    console.warn = function () {
        originalConsoleWarn.apply(console, arguments);

        const output = document.getElementById("output");
        if (output && output.style.display !== "none") {
            const message = Array.from(arguments)
                .map((arg) => {
                    if (typeof arg === "object") {
                        try {
                            return JSON.stringify(arg, null, 2);
                        } catch (e) {
                            return String(arg);
                        }
                    }
                    return String(arg);
                })
                .join(" ");

            const logSpan = document.createElement("span");
            logSpan.className = "log-warn";
            logSpan.textContent = `[WARN] ${message}`;

            output.appendChild(logSpan);
            output.appendChild(document.createTextNode("\n"));

            output.scrollTop = output.scrollHeight;
        }
    };
}

function initDarkMode() {
    const themeToggle = document.getElementById("themeToggle");
    const sunIcon = themeToggle.querySelector(".sun-icon");
    const moonIcon = themeToggle.querySelector(".moon-icon");
    const themeSelect = document.getElementById("themeSelect");

    const savedTheme = localStorage.getItem("theme");
    const prefersDark =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (
        savedTheme === "dark" ||
        (savedTheme === "system" && prefersDark) ||
        (!savedTheme && prefersDark)
    ) {
        document.documentElement.classList.add("dark-mode");
        sunIcon.style.display = "none";
        moonIcon.style.display = "block";
        if (themeSelect) themeSelect.value = savedTheme || "system";
    } else {
        document.documentElement.classList.remove("dark-mode");
        sunIcon.style.display = "block";
        moonIcon.style.display = "none";
        if (themeSelect) themeSelect.value = savedTheme || "light";
    }

    themeToggle.addEventListener("click", () => {
        const isDark = document.documentElement.classList.toggle("dark-mode");
        sunIcon.style.display = isDark ? "none" : "block";
        moonIcon.style.display = isDark ? "block" : "none";
        localStorage.setItem("theme", isDark ? "dark" : "light");
        if (themeSelect) themeSelect.value = isDark ? "dark" : "light";
    });

    window
        .matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", (e) => {
            if (localStorage.getItem("theme") === "system") {
                const shouldBeDark = e.matches;
                document.documentElement.classList.toggle("dark-mode", shouldBeDark);
                sunIcon.style.display = shouldBeDark ? "none" : "block";
                moonIcon.style.display = shouldBeDark ? "block" : "none";
            }
        });

    if (themeSelect) {
        themeSelect.addEventListener("change", () => {
            const selectedTheme = themeSelect.value;
            localStorage.setItem("theme", selectedTheme);

            const prefersDark =
                window.matchMedia &&
                window.matchMedia("(prefers-color-scheme: dark)").matches;
            const shouldBeDark =
                selectedTheme === "dark" || (selectedTheme === "system" && prefersDark);

            document.documentElement.classList.toggle("dark-mode", shouldBeDark);
            sunIcon.style.display = shouldBeDark ? "none" : "block";
            moonIcon.style.display = shouldBeDark ? "block" : "none";
        });
    }
}

function initSettingsModal() {
    const settingsModal = document.getElementById("settingsModal");
    const closeSettings = document.getElementById("closeSettings");
    const saveSettings = document.getElementById("saveSettings");
    const settingsTabs = document.querySelectorAll(".settings-tab");
    const settingsTabContents = document.querySelectorAll(
        ".settings-tab-content"
    );

    const container = document.querySelector(".container");
    container.style.position = "relative";

    const configButtons = document.createElement("div");
    configButtons.className = "config-buttons";
    container.appendChild(configButtons);

    const settingsButton = document.createElement("button");
    settingsButton.className = "config-button";
    settingsButton.innerHTML = "⚙️ API Settings";
    configButtons.appendChild(settingsButton);

    const exportSettingsButton = document.createElement("button");
    exportSettingsButton.className = "config-button";
    exportSettingsButton.innerHTML = "📤 Export Settings";
    configButtons.appendChild(exportSettingsButton);

    const loadConfigButton = document.createElement("button");
    loadConfigButton.className = "config-button";
    loadConfigButton.innerHTML = "📥 Load Config";
    configButtons.appendChild(loadConfigButton);

    exportSettingsButton.addEventListener("click", () => {
        exportSettings();
    });

    settingsButton.addEventListener("click", () => {
        settingsModal.style.display = "flex";
        loadSettings();
    });

    loadConfigButton.addEventListener("click", () => {
        const configFileInput = document.getElementById("configFileInput");
        if (configFileInput) {
            configFileInput.click();
        }
    });

    closeSettings.addEventListener("click", () => {
        settingsModal.style.display = "none";
    });

    saveSettings.addEventListener("click", () => {
        saveAllSettings();
        settingsModal.style.display = "none";
    });

    settingsTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const tabId = tab.getAttribute("data-tab");

            settingsTabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");

            settingsTabContents.forEach((content) => {
                content.style.display = "none";
            });
            document.getElementById(`${tabId}Tab`).style.display = "block";
        });
    });

    function loadSettings() {
        const apiKey = document.getElementById("apiKey");

        if (apiKey) {
            apiKey.value = localStorage.getItem("apiKey") || "";
        }
    }

    function saveAllSettings() {
        const apiKey = document.getElementById("apiKey");

        if (apiKey) {
            localStorage.setItem("apiKey", apiKey.value);
        }
    }
}

function collectAllSettings() {
    const settings = {};
    const form = document.getElementById("researchForm");

    const inputs = form.querySelectorAll("input, select, textarea");

    inputs.forEach((input) => {
        let value;

        if (input.type === "checkbox") {
            value = input.checked;
        } else if (input.type === "number") {
            value = parseFloat(input.value);
        } else {
            value = input.value;
        }

        if (input.name) {
            settings[input.name] = value;
        }
    });

    return settings;
}

function exportSettings() {
    const settings = collectAllSettings();

    const jsonSettings = JSON.stringify(settings, null, 2);

    const blob = new Blob([jsonSettings], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "gpt_researcher_config.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

async function loadConfigFromJSON(jsonData) {
    showLoading("Loading configuration...");

    try {
        const response = await fetch("/load_config", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: jsonData,
        });

        const result = await response.json();

        if (response.ok) {
            window.location.reload();
        } else {
            alert(`Error loading configuration: ${result.message}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function initConfigFileUpload() {
    const configFileInput = document.createElement("input");
    configFileInput.type = "file";
    configFileInput.id = "configFileInput";
    configFileInput.accept = ".json";
    configFileInput.style.display = "none";
    document.body.appendChild(configFileInput);

    configFileInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const jsonData = e.target.result;
                loadConfigFromJSON(jsonData);
            };
            reader.readAsText(file);
        }
    });
}

function initFileUpload() {
    const fileUploadArea = document.getElementById("fileUploadArea");
    const fileInput = document.getElementById("documents");
    const selectedFiles = document.getElementById("selectedFiles");

    if (!fileUploadArea || !fileInput) return;

    fileInput.addEventListener("change", () => {
        updateSelectedFiles();
    });

    fileUploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        fileUploadArea.classList.add("drag-active");
    });

    fileUploadArea.addEventListener("dragleave", () => {
        fileUploadArea.classList.remove("drag-active");
    });

    fileUploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove("drag-active");

        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateSelectedFiles();
        }
    });

    fileUploadArea.addEventListener("click", () => {
        fileInput.click();
    });

    function updateSelectedFiles() {
        selectedFiles.innerHTML = "";

        if (fileInput.files.length > 0) {
            const fileList = document.createElement("ul");
            fileList.className = "file-list";

            Array.from(fileInput.files).forEach((file) => {
                const li = document.createElement("li");
                li.textContent = file.name;
                fileList.appendChild(li);
            });

            selectedFiles.appendChild(fileList);
        }
    }
}

function showLoading(message = "Processing your request...") {
    console.log("Loading status: " + message);
}

function hideLoading() {}

function setupTagInput(containerId, hiddenInputId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const input = container.querySelector("input");
    const hiddenInput = document.getElementById(hiddenInputId);
    const tags = new Set();

    function updateHiddenInput() {
        hiddenInput.value = Array.from(tags).join(",");
    }

    function addTag(value) {
        if (!value) return;
        tags.add(value);
        const tag = document.createElement("div");
        tag.className = "tag";
        tag.innerHTML = `
                                                ${value}
                                                <span class="tag-remove" onclick="this.parentElement.remove();tags.delete('${value}');updateHiddenInput();">×</span>
                                `;
        container.insertBefore(tag, input);
        input.value = "";
        updateHiddenInput();
    }

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            addTag(input.value.trim());
        }
    });

    input.addEventListener("blur", () => {
        if (input.value.trim()) {
            addTag(input.value.trim());
        }
    });
}

function appendServerMessage(message, isError = false) {
    if (!message || !message.trim()) return;

    const output = document.getElementById("output");
    const msgDiv = document.createElement("div");
    msgDiv.className = isError ? "server-error" : "server-message";
    msgDiv.textContent = message;
    output.appendChild(msgDiv);
    output.scrollTop = output.scrollHeight;
    console.log(isError ? `[ERROR] ${message}` : `[SERVER] ${message}`);
}

function appendLogMessage(level, message) {
    if (!message || !message.trim()) return;

    const output = document.getElementById("output");
    const msgDiv = document.createElement("div");
    msgDiv.className = `log-message log-${level}`;
    msgDiv.textContent = message;
    output.appendChild(msgDiv);
    output.scrollTop = output.scrollHeight;
    console.log(`[${level.toUpperCase()}] ${message}`);
}

// Define displayReport in the global scope so it can be accessed from the websocket handler
function displayReport(content) {
    if (!content) return;

    const reportContainer = document.getElementById("report-container");
    const reportContent = document.getElementById("report-content");

    if (reportContainer && reportContent) {
        reportContainer.style.display = "block";
        reportContent.innerHTML = marked.parse(content);
    }
}

// Define updateReportDisplay in the global scope
function updateReportDisplay(content) {
    const reportContainer = document.getElementById("report-container");
    const reportContent = document.getElementById("report-content");

    if (content && reportContainer && reportContent) {
        if (reportContainer.style.display === "none") {
            reportContainer.style.display = "block";
        }

        const newContent = marked.parse(content);
        if (!reportContent.innerHTML.includes(newContent)) {
            reportContent.innerHTML += newContent;
            reportContent.scrollTop = reportContent.scrollHeight;
        }
    }
}

// Define getFormatIcon in the global scope
function getFormatIcon(format) {
    switch (format.toLowerCase()) {
        case "pdf":
            return "📄";
        case "docx":
            return "📝";
        case "md":
        case "markdown":
            return "📋";
        case "txt":
            return "📃";
        default:
            return "📄";
    }
}

async function startResearch(event) {
    event.preventDefault();
    console.log("startResearch function called");

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const spinner = submitBtn.querySelector(".spinner");
    const submitText = submitBtn.querySelector("span");
    const progress = document.getElementById("progress");
    const output = document.getElementById("output");
    const error = document.getElementById("error");
    const reportContainer = document.getElementById("report-container");
    const reportContent = document.getElementById("report-content");

    error.style.display = "none";
    output.textContent = "";
    reportContainer.style.display = "none";
    reportContent.innerHTML = "";
    submitBtn.disabled = true;
    spinner.style.display = "block";
    submitText.textContent = "Researching...";
    progress.style.display = "block";
    output.style.display = "block";

    try {
        const formData = new FormData(form);
        const query = formData.get("query");
        const reportType = formData.get("report_type");

        if (!query || !reportType) {
            throw new Error(
                "Missing required fields: query and report_type must be provided"
            );
        }

        appendServerMessage(`Starting research on: "${query}"`);
        appendServerMessage(`Report type: ${reportType}`);

        const fileInput = form.querySelector("#documents");
        if (fileInput && fileInput.files.length > 0) {
            appendServerMessage(`Processing ${fileInput.files.length} document(s) for upload...`);

            for (let i = 0; i < fileInput.files.length; i++) {
                const file = fileInput.files[i];
                const reader = new FileReader();

                reader.onload = function(e) {
                    const base64Data = e.target.result.split(',')[1];
                    // Create payload matching server's expected document format
                    const filePayload = {
                        type: "document_upload",
                        document: {
                            filename: file.name,
                            content: base64Data,
                            mime_type: file.type || "application/octet-stream"
                        }
                    };

                    if (!sendWebSocketMessage(researchWebSocket, "research", filePayload)) {
                        appendServerMessage(`File ${file.name} queued for upload when connection is restored`, true);
                    } else {
                        appendServerMessage(`File ${file.name} upload initiated`);
                    }
                };

                reader.onerror = function(e) {
                    console.error(`Error reading file ${file.name}:`, e);
                    appendServerMessage(`Error processing file ${file.name}: ${e.message || 'Unknown error'}`, true);
                };

                reader.readAsDataURL(file);
            }
            appendServerMessage(`Initiated upload of ${fileInput.files.length} document(s)`);
        }

        // Format arrays and get values with defaults
        const sourceUrls = formData.get("source_urls") ? formData.get("source_urls").split(",").filter(Boolean) : [];
        const queryDomains = formData.get("query_domains") ? formData.get("query_domains").split(",").filter(Boolean) : [];

        // Create research request payload matching ResearchAPIHandler.stream_research expectations
        const report_source = formData.get("report_source") || "web";
        const tone = formData.get("tone") || "Objective";

        // Convert arrays to strings since server will split them
        const sourceUrlsStr = Array.isArray(sourceUrls) ? sourceUrls.join(",") : "";
        const queryDomainsStr = Array.isArray(queryDomains) ? queryDomains.join(",") : "";

        // Document URLs handling (from local uploads)
        const documentUrls = [];
        if (fileInput && fileInput.files.length > 0) {
            for (const file of fileInput.files) {
                documentUrls.push(file.name);
            }
        }

        const payload = {
            type: "research_request",
            query: query, // Server expects 'query' not 'task'
            report_type: reportType,
            report_source,
            source_urls: sourceUrlsStr,
            document_urls: documentUrls.join(","),
            tone,
            query_domains: queryDomainsStr,
            language: formData.get("language") || "en"
        };

        console.log("Form data being sent:", payload);
        appendServerMessage("Sending research request to server...");

        // Attempt to send research request
        if (sendWebSocketMessage(researchWebSocket, "research", payload)) {
            appendServerMessage("Research request sent successfully. Processing results...");
        } else {
            appendServerMessage("Connection issue detected - request will be sent when connection is restored");
            submitBtn.disabled = true;
            spinner.style.display = "block";
            submitText.textContent = "Waiting for connection...";
            progress.style.display = "block";
            return;
        }

        let markdownContent = "";
        let reportStarted = false;

        function processLine(line) {
            if (!line || !line.trim()) return;

            if (line.startsWith("data: ")) {
                try {
                    const eventData = JSON.parse(line.slice(6));
                    console.log("Parsed event data:", eventData);

                    if (eventData.type === "log") {
                        appendLogMessage(eventData.level || "info", eventData.message);
                    } else if (eventData.type === "logs") {
                        appendLogMessage(
                            eventData.level || "info",
                            eventData.output || eventData.message || ""
                        );
                    } else if (eventData.type === "report_complete") {
                        markdownContent = eventData.content;
                        displayReport(eventData.content);

                        appendServerMessage("✅ Report generation complete!");

                        const chatContainer = document.getElementById("chat-container");
                        if (chatContainer) {
                            chatContainer.style.display = "block";
                            initChat();
                        }

                        const reportDownloads = document.getElementById("report-downloads");
                        if (reportDownloads && eventData.files) {
                            reportDownloads.innerHTML =
                                '<h3>Download Report</h3><div class="download-buttons"></div>';
                            const downloadButtons =
                                reportDownloads.querySelector(".download-buttons");

                            for (const [format, url] of Object.entries(eventData.files)) {
                                const formatLabel = format.toUpperCase();
                                const button = document.createElement("a");
                                button.href = url;
                                button.className = "download-button";
                                button.innerHTML = `<span class="download-icon">${getFormatIcon(
                                    format
                                )}</span> ${formatLabel}`;
                                button.download = `${eventData.base_filename}.${format}`;
                                downloadButtons.appendChild(button);
                            }
                        }

                        submitBtn.disabled = false;
                        spinner.style.display = "none";
                        submitText.textContent = "Start Research";
                        progress.style.display = "none";
                    } else if (eventData.type === "file_ready") {
                        appendServerMessage(
                            `✅ ${eventData.format.toUpperCase()} file ready for download`
                        );
                    } else if (eventData.type === "files_ready") {
                        appendServerMessage(eventData.message);
                    } else if (eventData.type === "research_progress") {
                        if (eventData.content && typeof eventData.content === "string") {
                            markdownContent += eventData.content;
                            updateReportDisplay(markdownContent);
                        }
                    }
                } catch (e) {
                    console.error("Error parsing event data:", e, line);
                }
            } else {
                if (
                    line.startsWith("[LOG]") ||
                    line.startsWith("[INFO]") ||
                    line.startsWith("[DEBUG]") ||
                    line.startsWith("[WARNING]") ||
                    line.startsWith("[ERROR]")
                ) {
                    appendServerMessage(line);
                } else if (line.includes("prompt_generate_report_conclusion:")) {
                    reportStarted = true;
                } else if (reportStarted) {
                    if (line.includes("CONTENT TO PROCESS:")) {
                        const contentMatch = line.match(/CONTENT TO PROCESS:\{(.*?)\}/);
                        if (contentMatch && contentMatch[1]) {
                            markdownContent += contentMatch[1];
                            updateReportDisplay(markdownContent);
                        }
                    } else if (line.includes("PROCESSING INSTRUCTIONS:")) {
                        return;
                    } else if (line.match(/^\s*\{.*\}\s*$/)) {
                        try {
                            const jsonContent = JSON.parse(line);
                            if (jsonContent.content) {
                                markdownContent += jsonContent.content;
                                updateReportDisplay(markdownContent);
                                return;
                            }
                        } catch (e) {}
                    } else if (!line.startsWith("[") && !line.startsWith("Sending")) {
                        markdownContent += line + "\n";
                        updateReportDisplay(markdownContent);
                        return;
                    }
                } else if (line.includes("Research complete")) {
                    appendServerMessage("✅ " + line);
                } else if (!reportStarted && !line.startsWith("---")) {
                    appendServerMessage(line);
                }

                if (
                    !reportStarted ||
                    line.startsWith("[") ||
                    line.startsWith("Sending")
                ) {
                    appendServerMessage(line);
                }
            }
        }
    } catch (e) {
        console.error("Error in research process:", e);

        error.textContent = `Error: ${e.message}`;
        error.style.display = "block";

        submitBtn.disabled = false;
        spinner.style.display = "none";
        submitText.textContent = "Start Research";
        progress.style.display = "none";

        appendServerMessage(`Error: ${e.message}`, true);
    }
}

function downloadAsFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function generateAndDownloadPDF(markdownContent, filename) {
    const htmlContent = marked.parse(markdownContent);

    alert(
        "PDF generation is being handled in the browser. For production use, consider using a server-side PDF generation service for better formatting."
    );

    if (window.html2pdf) {
        const element = document.createElement("div");
        element.className = "pdf-container";
        element.innerHTML = htmlContent;
        document.body.appendChild(element);

        const opt = {
            margin: [10, 10],
            filename: filename,
            image: { type: "jpeg", quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        };

        html2pdf()
            .set(opt)
            .from(element)
            .save()
            .then(() => {
                document.body.removeChild(element);
            });
    } else {
        downloadAsFile(htmlContent, filename.replace(".pdf", ".html"), "text/html");
        alert("PDF generation library not available. Downloaded as HTML instead.");
    }
}

function generateAndDownloadDOCX(markdownContent, filename) {
    alert(
        "DOCX generation is being handled in the browser. For production use, consider using a server-side DOCX generation service for better formatting."
    );

    if (window.docx) {
        alert("DOCX generation not fully implemented in this version.");
        downloadAsFile(
            markdownContent,
            filename.replace(".docx", ".md"),
            "text/markdown"
        );
    } else {
        downloadAsFile(
            markdownContent,
            filename.replace(".docx", ".md"),
            "text/markdown"
        );
        alert(
            "DOCX generation library not available. Downloaded as Markdown instead."
        );
    }
}

function initChat() {
    const chatInput = document.getElementById("chat-input");
    const chatSubmit = document.getElementById("chat-submit");
    const chatMessages = document.getElementById("chat-messages");

    if (chatInput && chatSubmit && chatMessages) {
        function addChatMessage(content, isUser = false) {
            const messageDiv = document.createElement("div");
            messageDiv.className = `chat-message ${isUser ? "user" : "assistant"}`;

            if (!isUser && window.marked) {
                messageDiv.innerHTML = marked.parse(content);
            } else {
                messageDiv.textContent = content;
            }

            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        async function sendChatMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            addChatMessage(message, true);

            chatInput.value = "";

            chatInput.disabled = true;
            chatSubmit.disabled = true;
            const spinner = chatSubmit.querySelector(".spinner");
            const submitText = chatSubmit.querySelector("span");
            spinner.style.display = "block";
            submitText.textContent = "Sending...";

            showLoading("Processing your question...");

            try {
                if (!chatWebSocket || chatWebSocket.readyState !== WebSocket.OPEN) {
                    throw new Error("WebSocket connection is not available");
                }

                if (!sendWebSocketMessage(chatWebSocket, "chat", { type: "chat_message", message })) {
                    addChatMessage("Connection issue - message will be sent when connection is restored", false);
                    chatInput.value = message; // Restore message for retry
                    return;
                }

                // Response will come through websocket.onmessage
            } catch (error) {
                console.error("Chat error:", error);
                addChatMessage(`Error: ${error.message}`);
            } finally {
                chatInput.disabled = false;
                chatSubmit.disabled = false;
                spinner.style.display = "none";
                submitText.textContent = "Send";
                chatInput.focus();

                hideLoading();
            }
        }

        chatSubmit.addEventListener("click", sendChatMessage);

        chatInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
}

let researchWebSocket;
let chatWebSocket;

let pendingMessages = {
    research: [],
    chat: []
};

function updateConnectionStatus(type, isConnected) {
    const submitBtn = document.getElementById("submitBtn");
    const chatInput = document.getElementById("chat-input");
    const chatSubmit = document.getElementById("chat-submit");

    if (type === "research") {
        if (submitBtn) {
            submitBtn.disabled = !isConnected;
            const statusText = submitBtn.querySelector("span");
            if (statusText) {
                statusText.textContent = isConnected ? "Start Research" : "Connecting...";
            }
        }
    } else if (type === "chat") {
        if (chatInput && chatSubmit) {
            chatInput.disabled = !isConnected;
            chatSubmit.disabled = !isConnected;
            const statusText = chatSubmit.querySelector("span");
            if (statusText) {
                statusText.textContent = isConnected ? "Send" : "Connecting...";
            }
        }
    }
}

function initWebSocket() {
    // Initialize research websocket
    researchWebSocket = new WebSocket(`ws://${window.location.host}/ws/research`);
    researchWebSocket = setupWebSocketHandlers(researchWebSocket, "research");

    // Initialize chat websocket
    chatWebSocket = new WebSocket(`ws://${window.location.host}/ws/chat`);
    chatWebSocket = setupWebSocketHandlers(chatWebSocket, "chat");

    // Initial connection check
    setTimeout(() => {
        if (!researchWebSocket || researchWebSocket.readyState !== WebSocket.OPEN) {
            console.warn("Research WebSocket failed to connect, retrying...");
            initWebSocket();
        }
        if (!chatWebSocket || chatWebSocket.readyState !== WebSocket.OPEN) {
            console.warn("Chat WebSocket failed to connect, retrying...");
            initWebSocket();
        }
    }, 5000);
}

function sendWebSocketMessage(socket, type, message) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.log(`${type} WebSocket not ready, queueing message`);
        pendingMessages[type].push(message);
        return false;
    }

    try {
        socket.send(JSON.stringify(message));
        return true;
    } catch (e) {
        console.error(`Error sending ${type} message:`, e);
        pendingMessages[type].push(message);
        return false;
    }
}

function setupWebSocketHandlers(socket, type) {
    socket.onopen = () => {
        console.log(`${type} WebSocket connection established`);
        updateConnectionStatus(type, true);
        appendServerMessage(`Connected to ${type} service`);

        // Clear any error messages
        if (type === "research") {
            const error = document.getElementById("error");
            if (error) {
                error.style.display = "none";
            }
        }

        // Send any pending messages
        if (pendingMessages[type].length > 0) {
            console.log(`Sending ${pendingMessages[type].length} pending ${type} messages`);
            // Process pending messages in order with pause between each
            const processPendingMessages = async () => {
                while (pendingMessages[type].length > 0) {
                    const msg = pendingMessages[type].shift();
                    try {
                        socket.send(JSON.stringify(msg));
                        await new Promise(resolve => setTimeout(resolve, 100)); // Small delay between messages
                    } catch (e) {
                        console.error(`Error sending pending ${type} message:`, e);
                        pendingMessages[type].unshift(msg); // Put message back at start of queue
                        break;
                    }
                }
            };
            processPendingMessages();
        }
    };

    socket.onerror = (error) => {
        console.error(`${type} WebSocket error:`, error);
        updateConnectionStatus(type, false);
        appendServerMessage(`Error connecting to ${type} service - will retry automatically`, true);

        // Show more detailed error feedback
        const errorText = `Connection error - retrying in 3 seconds. Your ${type} requests will be queued and sent automatically when connection is restored.`;
        if (type === "research") {
            const error = document.getElementById("error");
            if (error) {
                error.textContent = errorText;
                error.style.display = "block";
            }
        } else if (type === "chat") {
            addChatMessage(errorText, false);
        }
    };

    socket.onclose = () => {
        console.log(`${type} WebSocket connection closed`);
        updateConnectionStatus(type, false);

        const reconnectMsg = `${type} connection closed - attempting reconnection in 3 seconds...`;
        if (type === "research") {
            const error = document.getElementById("error");
            if (error) {
                error.textContent = reconnectMsg;
                error.style.display = "block";
            }
            setTimeout(() => {
                researchWebSocket = new WebSocket(`ws://${window.location.host}/ws/research`);
                setupWebSocketHandlers(researchWebSocket, "research");
            }, 3000);
        } else if (type === "chat") {
            addChatMessage(reconnectMsg, false);
            setTimeout(() => {
                chatWebSocket = new WebSocket(`ws://${window.location.host}/ws/chat`);
                setupWebSocketHandlers(chatWebSocket, "chat");
            }, 3000);
        }
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log(`Received ${type} websocket data:`, data);

            // Validate response matches server schema
            if (!data.type && !data.output) {
                throw new Error("Invalid server response: missing required fields");
            }

            if (type === "research") {
                if (data.type === "log") {
                    appendLogMessage(data.level || "info", data.message);
                } else if (data.type === "logs") {
                    appendLogMessage(data.level || "info", data.output || data.message || "");
                } else if (data.type === "report") {
                    displayReport(data.output);
                    resetResearchUI();
                } else if (data.type === "path") {
                    handleReportDownloads(data.output);
                } else if (data.type === "research_progress") {
                    if (data.content && typeof data.content === "string") {
                        updateReportDisplay(data.content);
                    }
                } else if (data.type === "error") {
                    appendServerMessage(data.message || data.output || "Unknown error occurred", true);
                    resetResearchUI();
                }
            } else if (type === "chat") {
                if (data.type === "error") {
                    addChatMessage("Sorry, I encountered an error: " + (data.message || "Unknown error"), false);
                } else {
                    addChatMessage(data.content || "No response received", false);
                }
            }
        } catch (e) {
            console.error(`Error processing ${type} websocket message:`, e);
            appendServerMessage(`Error processing ${type} message: ${e.message}`, true);
            if (type === "research") resetResearchUI();
        }
    };

    return socket;
}

function resetResearchUI() {
    const submitBtn = document.getElementById("submitBtn");
    const spinner = submitBtn.querySelector(".spinner");
    const submitText = submitBtn.querySelector("span");
    const progress = document.getElementById("progress");

    submitBtn.disabled = false;
    spinner.style.display = "none";
    submitText.textContent = "Start Research";
    progress.style.display = "none";
}

function handleReportDownloads(paths) {
    if (!paths || Object.keys(paths).length === 0) return;

    const reportDownloads = document.getElementById("report-downloads");
    if (!reportDownloads) return;

    reportDownloads.innerHTML = '<h3>Download Report</h3><div class="download-buttons"></div>';
    const downloadButtons = reportDownloads.querySelector(".download-buttons");

    for (const [format, path] of Object.entries(paths)) {
        const formatLabel = format.toUpperCase();
        const button = document.createElement("a");
        button.href = path;
        button.className = "download-button";
        button.innerHTML = `<span class="download-icon">${getFormatIcon(format)}</span> ${formatLabel}`;
        button.download = path.split("/").pop();
        downloadButtons.appendChild(button);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM loaded, initializing application");

    setupConsoleLogRedirect();
    initWebSocket();

    initDarkMode();

    initSettingsModal();

    initConfigFileUpload();

    initFileUpload();

    setupTagInput("sourceUrlsInput", "sourceUrls");
    setupTagInput("queryDomainsInput", "queryDomains");

    initChat();

    const defaultReportType = localStorage.getItem("defaultReportType");
    const defaultReportFormat = localStorage.getItem("defaultReportFormat");

    if (defaultReportType) {
        const reportTypeSelect = document.getElementById("report_type");
        if (reportTypeSelect) reportTypeSelect.value = defaultReportType;
    }

    if (defaultReportFormat) {
        const reportFormatSelect = document.getElementById("report_format");
        if (reportFormatSelect) reportFormatSelect.value = defaultReportFormat;
    }

    const researchForm = document.getElementById("research-form");
    console.log("Research form element:", researchForm);

    if (researchForm) {
        console.log("Research form found, attaching event listener");
        researchForm.addEventListener("submit", startResearch);
    } else {
        console.error(
            "Research form not found! This is likely the cause of the issue."
        );

        const forms = document.getElementsByTagName("form");
        console.log("Available forms:", forms.length);
        for (let i = 0; i < forms.length; i++) {
            console.log(`Form ${i} id:`, forms[i].id);

            forms[i].addEventListener("submit", startResearch);
            console.log(`Attached event listener to form ${i}`);
        }
    }

    const submitBtn = document.getElementById("submitBtn");
    if (submitBtn) {
        console.log("Submit button found, attaching direct click event listener");
        submitBtn.addEventListener("click", function (event) {
            event.preventDefault();
            console.log("Submit button clicked directly");

            const form = this.closest("form");
            if (form) {
                console.log("Form found from button, submitting");

                const submitEvent = new Event("submit", {
                    bubbles: true,
                    cancelable: true,
                });
                form.dispatchEvent(submitEvent);
            } else {
                console.error("Could not find form from submit button");

                startResearch({
                    preventDefault: function () {},
                    target:
                        document.getElementById("research-form") ||
                        document.querySelector("form"),
                });
            }
        });
    } else {
        console.error("Submit button not found!");
    }

    if (localStorage.getItem("advancedExpanded") === "true") {
        toggleAdvanced();
    }

    // Create download buttons if they do not exist
    const downloadFormats = ["docx", "markdown", "pdf"];
    let downloadContainer = document.getElementById("downloadContainer");
    if (!downloadContainer) {
        downloadContainer = document.createElement("div");
        downloadContainer.id = "downloadContainer";
        downloadContainer.style.marginTop = "10px";
        document.body.appendChild(downloadContainer);
    }
    downloadFormats.forEach(function (fmt) {
        let btn = document.getElementById("download_" + fmt);
        if (!btn) {
            btn = document.createElement("button");
            btn.id = "download_" + fmt;
            btn.textContent = "Download " + fmt.toUpperCase();
            btn.style.marginRight = "5px";
            btn.addEventListener("click", function () {
                sendWebSocketMessage(researchWebSocket, "research", { type: "request_download", format: fmt });
            });
            downloadContainer.appendChild(btn);
        }
    });

    // Helper functions
    function getOrCreateResearchContent() {
        let el = document.getElementById("researchContent");
        if (!el) {
            el = document.createElement("pre");
            el.id = "researchContent";
            el.style.border = "1px solid #ccc";
            el.style.padding = "10px";
            el.style.marginTop = "10px";
            el.style.whiteSpace = "pre-wrap"; // To maintain markdown formatting
            document.body.appendChild(el);
        }
        return el;
    }

    function startSpinner() {
        let spinner = document.getElementById("spinner");
        if (!spinner) {
            spinner = document.createElement("div");
            spinner.id = "spinner";
            spinner.textContent = "Loading...";
            spinner.style.fontSize = "20px";
            spinner.style.marginTop = "10px";
            document.body.appendChild(spinner);
        } else {
            spinner.style.display = "block";
        }
    }

    function stopSpinner() {
        let spinner = document.getElementById("spinner");
        if (spinner) {
            spinner.style.display = "none";
        }
    }

    // Overriding appendLogMessage to ensure logs are appended appropriately
    function appendLogMessage(level, message) {
        let logContainer = document.getElementById("logContainer");
        if (!logContainer) {
            logContainer = document.createElement("div");
            logContainer.id = "logContainer";
            logContainer.style.border = "1px solid #eee";
            logContainer.style.padding = "5px";
            logContainer.style.marginTop = "10px";
            logContainer.style.height = "150px";
            logContainer.style.overflowY = "auto";
            document.body.appendChild(logContainer);
        }
        const logEntry = document.createElement("div");
        logEntry.textContent = `[${level}] ${message}`;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
});
