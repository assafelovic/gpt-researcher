/**
 * GPT Researcher - TypeScript Frontend
 * 2025 Version
 */

// Type definitions
interface LogEvent {
    type: string;
    level?: string;
    message?: string;
    content?: string;
    files?: Record<string, string>;
    base_filename?: string;
    format?: string;
}

interface ChatResponse {
    type: string;
    content: string;
}

interface FormElements extends HTMLFormControlsCollection {
    query: HTMLInputElement;
    report_type: HTMLSelectElement;
    documents: HTMLInputElement;
}

interface ResearchForm extends HTMLFormElement {
    elements: FormElements;
}

/**
 * Toggles the advanced section visibility
 */
function toggleAdvanced(): void {
    const advancedSection = document.getElementById("advancedSection");
    const advancedToggle = document.getElementById("advancedToggle") as HTMLInputElement;

    if (!advancedSection || !advancedToggle) return;

    const isChecked = advancedToggle.checked;
    advancedSection.classList.toggle("visible", isChecked);

    localStorage.setItem("showAdvanced", isChecked ? "true" : "false");
}

/**
 * Sets up console log redirection to the output element
 */
function setupConsoleLogRedirect(): void {
    const originalConsoleLog = console.log;
    const originalConsoleError = console.error;
    const originalConsoleWarn = console.warn;

    console.log = function (...args: any[]): void {
        originalConsoleLog.apply(console, args);

        const output = document.getElementById("output");
        if (output && output.style.display !== "none") {
            const message = args
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

    console.error = function (...args: any[]): void {
        originalConsoleError.apply(console, args);

        const output = document.getElementById("output");
        if (output && output.style.display !== "none") {
            const message = args
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

    console.warn = function (...args: any[]): void {
        originalConsoleWarn.apply(console, args);

        const output = document.getElementById("output");
        if (output && output.style.display !== "none") {
            const message = args
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

/**
 * Initializes dark mode functionality
 */
function initDarkMode(): void {
    const themeToggle = document.getElementById("themeToggle");
    if (!themeToggle) return;

    const sunIcon = themeToggle.querySelector(".sun-icon") as HTMLElement;
    const moonIcon = themeToggle.querySelector(".moon-icon") as HTMLElement;
    const themeSelect = document.getElementById("themeSelect") as HTMLSelectElement;

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
        if (sunIcon) sunIcon.style.display = "none";
        if (moonIcon) moonIcon.style.display = "block";
        if (themeSelect) themeSelect.value = savedTheme || "system";
    } else {
        document.documentElement.classList.remove("dark-mode");
        if (sunIcon) sunIcon.style.display = "block";
        if (moonIcon) moonIcon.style.display = "none";
        if (themeSelect) themeSelect.value = savedTheme || "light";
    }

    themeToggle.addEventListener("click", () => {
        const isDark = document.documentElement.classList.toggle("dark-mode");
        if (sunIcon) sunIcon.style.display = isDark ? "none" : "block";
        if (moonIcon) moonIcon.style.display = isDark ? "block" : "none";
        localStorage.setItem("theme", isDark ? "dark" : "light");
        if (themeSelect) themeSelect.value = isDark ? "dark" : "light";
    });

    const darkModeMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    darkModeMediaQuery.addEventListener("change", (e) => {
        if (localStorage.getItem("theme") === "system") {
            const shouldBeDark = e.matches;
            document.documentElement.classList.toggle("dark-mode", shouldBeDark);
            if (sunIcon) sunIcon.style.display = shouldBeDark ? "none" : "block";
            if (moonIcon) moonIcon.style.display = shouldBeDark ? "block" : "none";
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
            if (sunIcon) sunIcon.style.display = shouldBeDark ? "none" : "block";
            if (moonIcon) moonIcon.style.display = shouldBeDark ? "block" : "none";
        });
    }
}

/**
 * Initializes the settings modal
 */
function initSettingsModal(): void {
    const settingsModal = document.getElementById("settingsModal");
    const closeSettings = document.getElementById("closeSettings");
    const saveSettings = document.getElementById("saveSettings");
    const settingsTabs = document.querySelectorAll<HTMLElement>(".settings-tab");
    const settingsTabContents = document.querySelectorAll<HTMLElement>(".settings-tab-content");

    if (!settingsModal) return;

    const container = document.querySelector<HTMLElement>(".container");
    if (!container) return;

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
            (configFileInput as HTMLInputElement).click();
        }
    });

    if (closeSettings) {
        closeSettings.addEventListener("click", () => {
            settingsModal.style.display = "none";
        });
    }

    if (saveSettings) {
        saveSettings.addEventListener("click", () => {
            saveAllSettings();
            settingsModal.style.display = "none";
        });
    }

    settingsTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const tabId = tab.getAttribute("data-tab");
            if (!tabId) return;

            settingsTabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");

            settingsTabContents.forEach((content) => {
                content.style.display = "none";
            });

            const tabContent = document.getElementById(`${tabId}Tab`);
            if (tabContent) {
                tabContent.style.display = "block";
            }
        });
    });
}

/**
 * Loads settings from localStorage
 */
function loadSettings(): void {
    const apiKey = document.getElementById("apiKey") as HTMLInputElement;

    if (apiKey) {
        apiKey.value = localStorage.getItem("apiKey") || "";
    }
}

/**
 * Saves all settings to localStorage
 */
function saveAllSettings(): void {
    const apiKey = document.getElementById("apiKey") as HTMLInputElement;

    if (apiKey) {
        localStorage.setItem("apiKey", apiKey.value);
    }
}

/**
 * Collects all settings from the research form
 * @returns Object containing all form settings
 */
function collectAllSettings(): Record<string, any> {
    const settings: Record<string, any> = {};
    const form = document.getElementById("researchForm") as HTMLFormElement;
    if (!form) return settings;

    const inputs = form.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>("input, select, textarea");

    inputs.forEach((input) => {
        let value: string | number | boolean;

        if (input.type === "checkbox") {
            value = (input as HTMLInputElement).checked;
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

/**
 * Exports settings to a JSON file
 */
function exportSettings(): void {
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

/**
 * Loads configuration from JSON data
 * @param jsonData - JSON configuration data
 */
async function loadConfigFromJSON(jsonData: string): Promise<void> {
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
        if (error instanceof Error) {
            alert(`Error: ${error.message}`);
        } else {
            alert("An unknown error occurred");
        }
    } finally {
        hideLoading();
    }
}

/**
 * Initializes the config file upload functionality
 */
function initConfigFileUpload(): void {
    const configFileInput = document.createElement("input");
    configFileInput.type = "file";
    configFileInput.id = "configFileInput";
    configFileInput.accept = ".json";
    configFileInput.style.display = "none";
    document.body.appendChild(configFileInput);

    configFileInput.addEventListener("change", (event) => {
        const target = event.target as HTMLInputElement;
        const file = target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const result = e.target?.result;
                if (typeof result === 'string') {
                    loadConfigFromJSON(result);
                }
            };
            reader.readAsText(file);
        }
    });
}

/**
 * Initializes the document file upload area
 */
function initFileUpload(): void {
    const fileUploadArea = document.getElementById("fileUploadArea");
    const fileInput = document.getElementById("documents") as HTMLInputElement;
    const selectedFiles = document.getElementById("selectedFiles");

    if (!fileUploadArea || !fileInput || !selectedFiles) return;

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

        if (e.dataTransfer?.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateSelectedFiles();
        }
    });

    fileUploadArea.addEventListener("click", () => {
        fileInput.click();
    });

    /**
     * Updates the selected files display
     */
    function updateSelectedFiles(): void {
        selectedFiles.innerHTML = "";

        if (fileInput.files && fileInput.files.length > 0) {
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

/**
 * Shows loading message
 * @param message - Loading message to display
 */
function showLoading(message: string = "Processing your request..."): void {
    console.log("Loading status: " + message);
}

/**
 * Hides loading message
 */
function hideLoading(): void {
    // Implementation depends on UI requirements
}

/**
 * Sets up tag input functionality
 * @param containerId - ID of the container element
 * @param hiddenInputId - ID of the hidden input element
 */
function setupTagInput(containerId: string, hiddenInputId: string): void {
  const container = document.getElementById(containerId);
  if (!container) return;

  const input = container.querySelector("input") as HTMLInputElement;
  const hiddenInput = document.getElementById(hiddenInputId) as HTMLInputElement;
  if (!input || !hiddenInput) return;
  
  const tags = new Set<string>();

  /**
   * Updates the hidden input value with the current tags
   */
  function updateHiddenInput(): void {
    hiddenInput.value = Array.from(tags).join(",");
  }

  /**
   * Adds a new tag
   * @param value - Tag value to add
   */
  function addTag(value: string): void {
    if (!value) return;
    tags.add(value);
    const tag = document.createElement("div");
    tag.className = "tag";
    tag.innerHTML = `
      ${value}
      <span class="tag-remove" data-value="${value}">×</span>
    `;
    
    const removeButton = tag.querySelector(".tag-remove");
    if (removeButton) {
      removeButton.addEventListener("click", () => {
        tags.delete(value);
        tag.remove();
        updateHiddenInput();
      });
    }
    
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

/**
 * Appends a server message to the output
 * @param message - Message to append
 * @param isError - Whether the message is an error
 */
function appendServerMessage(message: string, isError: boolean = false): void {
  if (!message || !message.trim()) return;

  const output = document.getElementById("output");
  if (!output) return;
  
  const msgDiv = document.createElement("div");
  msgDiv.className = isError ? "server-error" : "server-message";
  msgDiv.textContent = message;
  output.appendChild(msgDiv);
  output.scrollTop = output.scrollHeight;
  console.log(isError ? `[ERROR] ${message}` : `[SERVER] ${message}`);
}

/**
 * Appends a log message to the output
 * @param level - Log level
 * @param message - Message to append
 */
function appendLogMessage(level: string, message: string): void {
  if (!message || !message.trim()) return;

  const output = document.getElementById("output");
  if (!output) return;
  
  const msgDiv = document.createElement("div");
  msgDiv.className = `log-message log-${level}`;
  msgDiv.textContent = message;
  output.appendChild(msgDiv);
  output.scrollTop = output.scrollHeight;
  console.log(`[${level.toUpperCase()}] ${message}`);
}

/**
 * Starts the research process
 * @param event - Form submit event
 */
async function startResearch(event: Event): Promise<void> {
  event.preventDefault();
  console.log("startResearch function called");

  const form = event.target as HTMLFormElement;
  const submitBtn = form.querySelector('button[type="submit"]') as HTMLButtonElement;
  const spinner = submitBtn.querySelector(".spinner") as HTMLElement;
  const submitText = submitBtn.querySelector("span") as HTMLElement;
  const progress = document.getElementById("progress") as HTMLElement;
  const output = document.getElementById("output") as HTMLElement;
  const error = document.getElementById("error") as HTMLElement;
  const reportContainer = document.getElementById("report-container") as HTMLElement;
  const reportContent = document.getElementById("report-content") as HTMLElement;

  if (!submitBtn || !spinner || !submitText || !progress || !output || !error || !reportContainer || !reportContent) {
    console.error("Required elements not found");
    return;
  }

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
    const query = formData.get("query") as string;
    const reportType = formData.get("report_type") as string;

    if (!query || !reportType) {
      throw new Error(
        "Missing required fields: query and report_type must be provided"
      );
    }

    appendServerMessage(`Starting research on: "${query}"`);
    appendServerMessage(`Report type: ${reportType}`);

    const fileInput = form.querySelector("#documents") as HTMLInputElement;
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const files = fileInput.files;
      formData.delete("documents");

      for (let i = 0; i < files.length; i++) {
        formData.append("documents", files[i]);
      }
      appendServerMessage(`Uploading ${files.length} document(s) for analysis`);
    }

    console.log("Form data being sent:");
    for (const [key, value] of formData.entries()) {
      console.log(`${key}: ${value}`);
    }

    appendServerMessage("Sending research request to server...");

    const xhr = new XMLHttpRequest();
    let markdownContent = "";
    let reportStarted = false;

    const requestPromise = new Promise<XMLHttpRequest>((resolve, reject) => {
      xhr.open("POST", "/research", true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round(
            (event.loaded / event.total) * 100
          );
          appendServerMessage(`Upload progress: ${percentComplete}%`);
        }
      };

      xhr.onreadystatechange = function () {
        console.log(
          `XHR state changed: ${xhr.readyState}, status: ${xhr.status}`
        );

        if (xhr.readyState === 4) {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(xhr);
          } else {
            reject(
              new Error(
                `Server returned status ${xhr.status}: ${xhr.statusText}`
              )
            );
          }
        }
      };

      xhr.onerror = () => {
        reject(new Error("Network error occurred"));
      };

      xhr.ontimeout = () => {
        reject(new Error("Request timed out"));
      };

      xhr.timeout = 300000; // 5 minutes

      xhr.send(formData);
    });

    const response = await requestPromise;

    appendServerMessage(
      "Research request sent successfully. Processing results..."
    );

    const reader = response.responseText.split("\n");
    let currentLine = 0;

    processInitialResponse();

    const checkInterval = setInterval(processNewContent, 100);

    /**
     * Processes the initial response
     */
    function processInitialResponse(): void {
      while (currentLine < reader.length) {
        const line = reader[currentLine++];
        processLine(line);
      }
    }

    /**
     * Processes new content as it arrives
     */
    function processNewContent(): void {
      if (currentLine < reader.length) {
        while (currentLine < reader.length) {
          const line = reader[currentLine++];
          processLine(line);
        }
      }

      if (xhr.readyState === 4 && currentLine >= reader.length) {
        clearInterval(checkInterval);

        submitBtn.disabled = false;
        spinner.style.display = "none";
        submitText.textContent = "Start Research";
        progress.style.display = "none";

        if (markdownContent && reportContainer.style.display === "none") {
          displayReport(markdownContent);
        }
      }
    }

    /**
     * Processes a single line of response
     * @param line - Line to process
     */
    function processLine(line: string): void {
      if (!line || !line.trim()) return;

      if (line.startsWith("data: ")) {
        try {
          const eventData = JSON.parse(line.slice(6)) as LogEvent;
          console.log("Parsed event data:", eventData);

          if (eventData.type === "log" && eventData.level && eventData.message) {
            appendLogMessage(eventData.level, eventData.message);
          } else if (eventData.type === "report_complete" && eventData.content) {
            appendServerMessage("✅ Report generation complete!");

            displayReport(eventData.content);

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
              
              if (downloadButtons) {
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
            }
          } else if (eventData.type === "file_ready" && eventData.format) {
            appendServerMessage(
              `✅ ${eventData.format.toUpperCase()} file ready for download`
            );
          } else if (eventData.type === "files_ready" && eventData.message) {
            appendServerMessage(eventData.message);
          }
        } catch (e) {
          console.error("Error parsing event data:", e, line);
        }
      } else {
        if (line.startsWith("[LOG]")) {
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
            } catch (e) {
              // Not valid JSON, continue with normal processing
            }
          } else if (!line.startsWith("[") && !line.startsWith("Sending")) {
            markdownContent += line + "\n";
            updateReportDisplay(markdownContent);
            return;
          }
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

    /**
     * Updates the report display with new content
     * @param content - Markdown content to display
     */
    function updateReportDisplay(content: string): void {
      if (content && reportContainer.style.display === "none") {
        reportContainer.style.display = "block";
      }

      if (content && reportContent) {
        // Using marked library to parse markdown
        if (typeof marked !== 'undefined') {
          reportContent.innerHTML = marked.parse(content);
        } else {
          reportContent.textContent = content;
        }

        reportContent.scrollTop = reportContent.scrollHeight;
      }
    }

    /**
     * Displays the final report
     * @param content - Markdown content to display
     */
    function displayReport(content: string): void {
      if (!content) return;

      reportContainer.style.display = "block";

      // Using marked library to parse markdown
      if (typeof marked !== 'undefined') {
        reportContent.innerHTML = marked.parse(content);
      } else {
        reportContent.textContent = content;
      }

      markdownContent = content;
    }

    /**
     * Gets the icon for a file format
     * @param format - File format
     * @returns Icon string
     */
    function getFormatIcon(format: string): string {
      switch (format.toLowerCase()) {
        case "pdf":
          return "📄";
        case "docx":
          return "📝";
        case "md":
          return "📋";
        default:
          return "📄";
      }
    }
  } catch (e) {
    console.error("Error in research process:", e);

    if (e instanceof Error) {
      error.textContent = `Error: ${e.message}`;
    } else {
      error.textContent = "An unknown error occurred";
    }
    error.style.display = "block";

    submitBtn.disabled = false;
    spinner.style.display = "none";
    submitText.textContent = "Start Research";
    progress.style.display = "none";

    if (e instanceof Error) {
      appendServerMessage(`Error: ${e.message}`, true);
    } else {
      appendServerMessage("An unknown error occurred", true);
    }
  }
}

/**
 * Downloads content as a file
 * @param content - Content to download
 * @param filename - Filename to use
 * @param contentType - Content type
 */
function downloadAsFile(content: string, filename: string, contentType: string): void {
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

/**
 * Generates and downloads a PDF from markdown content
 * @param markdownContent - Markdown content to convert
 * @param filename - Filename to use
 */
function generateAndDownloadPDF(markdownContent: string, filename: string): void {
  const htmlContent = typeof marked !== 'undefined' 
    ? marked.parse(markdownContent) 
    : markdownContent;

  alert(
    "PDF generation is being handled in the browser. For production use, consider using a server-side PDF generation service for better formatting."
  );

  // Check if html2pdf is available
  if (typeof html2pdf !== 'undefined') {
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

/**
 * Generates and downloads a DOCX from markdown content
 * @param markdownContent - Markdown content to convert
 * @param filename - Filename to use
 */
function generateAndDownloadDOCX(markdownContent: string, filename: string): void {
  alert(
    "DOCX generation is being handled in the browser. For production use, consider using a server-side DOCX generation service for better formatting."
  );

  // Check if docx is available
  if (typeof docx !== 'undefined') {
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

/**
 * Initializes the chat functionality
 */
function initChat(): void {
  const chatInput = document.getElementById("chat-input") as HTMLInputElement;
  const chatSubmit = document.getElementById("chat-submit") as HTMLButtonElement;
  const chatMessages = document.getElementById("chat-messages") as HTMLElement;

  if (!chatInput || !chatSubmit || !chatMessages) return;

  /**
   * Adds a chat message to the chat container
   * @param content - Message content
   * @param isUser - Whether the message is from the user
   */
  function addChatMessage(content: string, isUser: boolean = false): void {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${isUser ? "user" : "assistant"}`;

    if (!isUser && typeof marked !== 'undefined') {
      messageDiv.innerHTML = marked.parse(content);
    } else {
      messageDiv.textContent = content;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  /**
   * Sends a chat message to the server
   */
  async function sendChatMessage(): Promise<void> {
    const message = chatInput.value.trim();
    if (!message) return;

    addChatMessage(message, true);

    chatInput.value = "";

    chatInput.disabled = true;
    chatSubmit.disabled = true;
    const spinner = chatSubmit.querySelector(".spinner") as HTMLElement;
    const submitText = chatSubmit.querySelector("span") as HTMLElement;
    
    if (spinner) spinner.style.display = "block";
    if (submitText) submitText.textContent = "Sending...";

    showLoading("Processing your question...");

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.statusText}`);
      }

      const data = await response.json() as ChatResponse;

      if (data.type === "chat" && data.content) {
        addChatMessage(data.content);
      } else {
        addChatMessage(
          "Sorry, I encountered an error processing your request."
        );
      }
    } catch (error) {
      console.error("Chat error:", error);
      if (error instanceof Error) {
        addChatMessage(`Error: ${error.message}`);
      } else {
        addChatMessage("An unknown error occurred");
      }
    } finally {
      chatInput.disabled = false;
      chatSubmit.disabled = false;
      if (spinner) spinner.style.display = "none";
      if (submitText) submitText.textContent = "Send";
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

// Add declaration for marked library
declare const marked: {
  parse: (markdown: string) => string;
};

// Add declaration for html2pdf library
declare const html2pdf: () => {
  set: (options: any) => any;
  from: (element: HTMLElement) => any;
  save: () => any;
};

// Add declaration for docx library
declare const docx: any;

/**
 * Document ready event handler
 */
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM loaded, initializing application");

  setupConsoleLogRedirect();

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
    const reportTypeSelect = document.getElementById("report_type") as HTMLSelectElement;
    if (reportTypeSelect) reportTypeSelect.value = defaultReportType;
  }

  if (defaultReportFormat) {
    const reportFormatSelect = document.getElementById("report_format") as HTMLSelectElement;
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

      const form = this.closest("form") as HTMLFormElement;
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
          preventDefault: () => {},
          target:
            document.getElementById("research-form") ||
            document.querySelector("form"),
        } as unknown as Event);
      }
    });
  } else {
    console.error("Submit button not found!");
  }

  const advancedExpanded = localStorage.getItem("advancedExpanded");
  if (advancedExpanded === "true") {
    toggleAdvanced();
  }
}); 