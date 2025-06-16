import { createParser, ParsedEvent, ReconnectInterval } from "eventsource-parser";
import {
  logApiCall,
  logApiResponse,
  logApiError,
  logBackendQuery,
  logBackendResponse,
  logResearchProgress,
  logSystem,
  generateRequestId
} from "../utils/terminalLogger";

export async function handleSourcesAndAnswer(question: string) {
  const requestId = generateRequestId();
  const startTime = Date.now();

  logBackendQuery("Research sources and answer generation", { question }, requestId);
  logResearchProgress("Fetching Sources", 10, { question }, requestId);

  try {
    // Log sources API call
    logApiCall("POST", "/api/getSources", { question }, requestId);
    let sourcesResponse = await fetch("/api/getSources", {
      method: "POST",
      body: JSON.stringify({ question }),
    });

    logApiResponse("/api/getSources", sourcesResponse.status, undefined, requestId);
    let sources = await sourcesResponse.json();
    logSystem(`Retrieved ${sources?.length || 0} sources`, sources, requestId);
    logResearchProgress("Sources Retrieved", 40, { sourcesCount: sources?.length }, requestId);

    // Log answer API call
    logApiCall("POST", "/api/getAnswer", { question, sources }, requestId);
    logResearchProgress("Generating Answer", 60, undefined, requestId);

    const response = await fetch("/api/getAnswer", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, sources }),
    });

    logApiResponse("/api/getAnswer", response.status, undefined, requestId);

    if (!response.ok) {
      const error = new Error(response.statusText);
      logApiError("/api/getAnswer", error, requestId);
      throw error;
    }

    if (response.status === 202) {
      logResearchProgress("Answer Generated (Direct)", 100, undefined, requestId);
      const fullAnswer = await response.text();
      logBackendResponse("Direct answer generation", Date.now() - startTime, fullAnswer.length, requestId);
      return fullAnswer;
    }

    // This data is a ReadableStream
    const data = response.body;
    if (!data) {
      logSystem("No response body received", undefined, requestId);
      return;
    }

    logSystem("Processing streaming response", undefined, requestId);
    logResearchProgress("Processing Stream", 80, undefined, requestId);

    const onParse = (event: ParsedEvent | ReconnectInterval) => {
      if (event.type === "event") {
        const data = event.data;
        try {
          const text = JSON.parse(data).text ?? "";
          logSystem(`Streaming chunk received: ${text.length} chars`, { preview: text.substring(0, 100) }, requestId);
          return text;
        } catch (e) {
          logApiError("Stream parsing", e, requestId);
          console.error(e);
        }
      }
    };

    // https://web.dev/streams/#the-getreader-and-read-methods
    const reader = data.getReader();
    const decoder = new TextDecoder();
    const parser = createParser(onParse);
    let done = false;
    let chunkCount = 0;

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      const chunkValue = decoder.decode(value);
      chunkCount++;
      logSystem(`Processing stream chunk ${chunkCount}`, { size: chunkValue.length }, requestId);
      parser.feed(chunkValue);
    }

    logResearchProgress("Answer Generated (Stream)", 100, { totalChunks: chunkCount }, requestId);
    logBackendResponse("Streaming answer generation", Date.now() - startTime, chunkCount, requestId);

  } catch (error) {
    logApiError("Sources and Answer generation", error, requestId);
    throw error;
  }
}

export async function handleSimilarQuestions(question: string) {
  const requestId = generateRequestId();
  const startTime = Date.now();

  logBackendQuery("Similar questions lookup", { question }, requestId);
  logApiCall("POST", "/api/getSimilarQuestions", { question }, requestId);

  try {
    let res = await fetch("/api/getSimilarQuestions", {
      method: "POST",
      body: JSON.stringify({ question }),
    });

    logApiResponse("/api/getSimilarQuestions", res.status, undefined, requestId);
    let questions = await res.json();

    logBackendResponse("Similar questions lookup", Date.now() - startTime, questions?.length, requestId);
    logSystem(`Found ${questions?.length || 0} similar questions`, questions, requestId);

    return questions;
  } catch (error) {
    logApiError("/api/getSimilarQuestions", error, requestId);
    throw error;
  }
}

export async function handleLanggraphAnswer(question: string) {
  const requestId = generateRequestId();
  const startTime = Date.now();

  logBackendQuery("LangGraph multi-agent research", { question }, requestId);
  logResearchProgress("Starting LangGraph Research", 5, { question }, requestId);
  logApiCall("POST", "/api/generateLanggraph", { question }, requestId);

  try {
    const response = await fetch("/api/generateLanggraph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    logApiResponse("/api/generateLanggraph", response.status, undefined, requestId);

    if (!response.ok) {
      const error = new Error(response.statusText);
      logApiError("/api/generateLanggraph", error, requestId);
      throw error;
    }

    // This data is a ReadableStream
    const data = response.body;
    if (!data) {
      logSystem("No LangGraph response body received", undefined, requestId);
      return;
    }

    logSystem("Processing LangGraph streaming response", undefined, requestId);
    logResearchProgress("Processing LangGraph Stream", 20, undefined, requestId);

    const onParse = (event: ParsedEvent | ReconnectInterval) => {
      if (event.type === "event") {
        const data = event.data;
        try {
          const text = JSON.parse(data).text ?? "";
          logSystem(`LangGraph streaming chunk: ${text.length} chars`, { preview: text.substring(0, 100) }, requestId);

          // Try to extract agent work information from the stream
          if (text.includes("agent") || text.includes("researcher") || text.includes("browser")) {
            const agentMatch = text.match(/(\w+)\s+agent/i);
            if (agentMatch) {
              logSystem(`LangGraph Agent Activity: ${agentMatch[1]}`, { fullText: text }, requestId);
            }
          }

          return text;
        } catch (e) {
          logApiError("LangGraph stream parsing", e, requestId);
          console.error(e);
        }
      }
    };

    const reader = data.getReader();
    const decoder = new TextDecoder();
    const parser = createParser(onParse);
    let done = false;
    let chunkCount = 0;
    let progressIncrement = 70 / 20; // Spread remaining 70% across estimated chunks

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      const chunkValue = decoder.decode(value);
      chunkCount++;

      const currentProgress = Math.min(20 + (chunkCount * progressIncrement), 90);
      logResearchProgress("LangGraph Processing", currentProgress, { chunk: chunkCount }, requestId);
      logSystem(`LangGraph stream chunk ${chunkCount}`, { size: chunkValue.length }, requestId);

      parser.feed(chunkValue);
    }

    logResearchProgress("LangGraph Research Complete", 100, { totalChunks: chunkCount }, requestId);
    logBackendResponse("LangGraph multi-agent research", Date.now() - startTime, chunkCount, requestId);

  } catch (error) {
    logApiError("LangGraph generation", error, requestId);
    throw error;
  }
}
