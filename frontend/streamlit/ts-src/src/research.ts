/**
 * Research functionality for the GPT Researcher UI
 */
import { EventData } from './types';
import { appendServerMessage, appendLogMessage } from './logging';
import { showLoading, hideLoading, getFormatIcon } from './utils';
import { initChat } from './chat';

declare global {
  interface Window {
    marked: {
      parse: (text: string) => string;
    };
  }
}

/**
 * Starts the research process
 * @param event The form submission event
 */
export async function startResearch(event: Event): Promise<void> {
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

      xhr.timeout = 300000;

      xhr.send(formData);
    });

    const response = await requestPromise;

    appendServerMessage(
      "Research request sent successfully. Processing results..."
    );

    const reader = response.responseText.split("\n");
    let currentLine = 0;
    let markdownContent = "";
    let reportStarted = false;

    processInitialResponse();

    const checkInterval = setInterval(processNewContent, 100);

    function processInitialResponse(): void {
      while (currentLine < reader.length) {
        const line = reader[currentLine++];
        processLine(line);
      }
    }

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

    function processLine(line: string): void {
      if (!line || !line.trim()) return;

      if (line.startsWith("data: ")) {
        try {
          const eventData = JSON.parse(line.slice(6)) as EventData;
          console.log("Parsed event data:", eventData);

          if (eventData.type === "log") {
            appendLogMessage(eventData.level || "info", eventData.message || "");
          } else if (eventData.type === "report_complete") {
            appendServerMessage("✅ Report generation complete!");

            displayReport(eventData.content || "");

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
                  button.download = `${eventData.base_filename || "report"}.${format}`;
                  downloadButtons.appendChild(button);
                }
              }
            }
          } else if (eventData.type === "file_ready") {
            appendServerMessage(
              `✅ ${eventData.format?.toUpperCase() || ""} file ready for download`
            );
          } else if (eventData.type === "files_ready") {
            appendServerMessage(eventData.message || "");
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

    function updateReportDisplay(content: string): void {
      if (content && reportContainer.style.display === "none") {
        reportContainer.style.display = "block";
      }

      if (content && reportContent && window.marked) {
        reportContent.innerHTML = window.marked.parse(content);
        reportContent.scrollTop = reportContent.scrollHeight;
      }
    }

    function displayReport(content: string): void {
      if (!content) return;

      reportContainer.style.display = "block";

      if (window.marked) {
        reportContent.innerHTML = window.marked.parse(content);
      }

      markdownContent = content;
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

    appendServerMessage(`Error: ${e instanceof Error ? e.message : "Unknown error"}`, true);
  }
} 