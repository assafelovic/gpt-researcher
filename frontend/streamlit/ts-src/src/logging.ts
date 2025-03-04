/**
 * Logging functionality for the GPT Researcher UI
 */

type LogLevel = 'info' | 'warn' | 'error';

/**
 * Sets up console log redirection to the output element
 */
export function setupConsoleLogRedirect(): void {
  const originalConsoleLog = console.log;
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;

  console.log = function (...args: any[]): void {
    originalConsoleLog.apply(console, args);
    appendToOutput(args, 'info');
  };

  console.error = function (...args: any[]): void {
    originalConsoleError.apply(console, args);
    appendToOutput(args, 'error');
  };

  console.warn = function (...args: any[]): void {
    originalConsoleWarn.apply(console, args);
    appendToOutput(args, 'warn');
  };

  /**
   * Appends log messages to the output element
   * @param args The arguments to log
   * @param level The log level
   */
  function appendToOutput(args: any[], level: LogLevel): void {
    const output = document.getElementById("output");
    if (!output || output.style.display === "none") return;

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
    logSpan.className = `log-${level}`;
    logSpan.textContent = `[${level.toUpperCase()}] ${message}`;

    output.appendChild(logSpan);
    output.appendChild(document.createTextNode("\n"));

    output.scrollTop = output.scrollHeight;
  }
}

/**
 * Appends a server message to the output element
 * @param message The message to append
 * @param isError Whether the message is an error
 */
export function appendServerMessage(message: string, isError: boolean = false): void {
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
 * Appends a log message to the output element
 * @param level The log level
 * @param message The message to append
 */
export function appendLogMessage(level: string, message: string): void {
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