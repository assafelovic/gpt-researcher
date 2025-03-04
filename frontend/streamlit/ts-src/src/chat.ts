/**
 * Chat functionality for the GPT Researcher UI
 */
import { showLoading, hideLoading } from './utils';
import { ChatMessage } from './types';

// Add a declaration for the marked library
declare global {
  interface Window {
    marked: {
      parse: (text: string) => string;
    };
  }
}

/**
 * Initializes the chat functionality
 */
export function initChat(): void {
  const chatInput = document.getElementById("chat-input") as HTMLInputElement;
  const chatSubmit = document.getElementById("chat-submit") as HTMLButtonElement;
  const chatMessages = document.getElementById("chat-messages");

  if (!chatInput || !chatSubmit || !chatMessages) return;

  /**
   * Adds a chat message to the chat messages container
   * @param content The message content
   * @param isUser Whether the message is from the user
   */
  function addChatMessage(content: string, isUser: boolean = false): void {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${isUser ? "user" : "assistant"}`;

    if (!isUser && window.marked) {
      messageDiv.innerHTML = window.marked.parse(content);
    } else {
      messageDiv.textContent = content;
    }

    chatMessages!.appendChild(messageDiv);
    chatMessages!.scrollTop = chatMessages!.scrollHeight;
  }

  /**
   * Sends a chat message to the server
   */
  async function sendChatMessage(): Promise<void> {
    const message = chatInput!.value.trim();
    if (!message) return;

    addChatMessage(message, true);

    chatInput!.value = "";

    chatInput!.disabled = true;
    chatSubmit!.disabled = true;
    const spinner = chatSubmit!.querySelector(".spinner") as HTMLElement | null;
    const submitText = chatSubmit!.querySelector("span") as HTMLElement | null;
    
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

      const data = await response.json();

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
      chatInput!.disabled = false;
      chatSubmit!.disabled = false;
      if (spinner) spinner.style.display = "none";
      if (submitText) submitText.textContent = "Send";
      chatInput!.focus();

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