"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { useConnectionManager } from '@/hooks/useConnectionManager';
import { useConnectionHealth } from '@/hooks/useConnectionHealth';
import { useResearchHistory } from '@/hooks/useResearchHistory';
import { startLanggraphResearch } from '../components/Langgraph/Langgraph';
import findDifferences from '../helpers/findDifferences';
import { Data, ChatBoxSettings, QuestionData } from '../types/data';
import { preprocessOrderedData } from '../utils/dataProcessing';
import { ResearchResults } from '../components/ResearchResults';
import {
  logUserAction,
  logSystem,
  logError,
  logResearchProgress,
  logResearchComplete,
  generateRequestId,
  terminalLogger
} from "../utils/terminalLogger";

import Header from "@/components/Header";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
import InputArea from "@/components/ResearchBlocks/elements/InputArea";
import HumanFeedback from "@/components/HumanFeedback";
import LoadingDots from "@/components/LoadingDots";
import ResearchSidebar from "@/components/ResearchSidebar";
import ResearchStatusIndicator from "@/components/ResearchStatusIndicator";

export default function Home() {
  const [promptValue, setPromptValue] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatBoxSettings, setChatBoxSettings] = useState<ChatBoxSettings>({
    report_source: 'web',
    report_type: 'research_report',
    tone: 'Objective',
    domains: [],
    defaultReportType: 'research_report',
    mcp_enabled: false,
    mcp_configs: []
  });
  const [question, setQuestion] = useState("");
  const [orderedData, setOrderedData] = useState<Data[]>([]);
  const [showHumanFeedback, setShowHumanFeedback] = useState(false);
  const [questionForHuman, setQuestionForHuman] = useState<true | false>(false);
  const [allLogs, setAllLogs] = useState<any[]>([]);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [isStopped, setIsStopped] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const mainContentRef = useRef<HTMLDivElement>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const {
    history,
    saveResearch,
    getResearchById,
    deleteResearch
  } = useResearchHistory();

  const {
    socket,
    researchState,
    startResearch,
    stopResearch,
    sendFeedback,
    getStatusDescription,
    isConnected,
    isRetrying
  } = useConnectionManager(
    setOrderedData,
    setAnswer,
    setLoading,
    setShowHumanFeedback,
    setQuestionForHuman
  );

  const {
    health: connectionHealth,
    getHealthDescription,
    getHealthColor
  } = useConnectionHealth(socket);

  const handleFeedbackSubmit = (feedback: string | null) => {
    sendFeedback(feedback);
  };

  const handleChat = async (message: string) => {
    if (socket) {
      setShowResult(true);
      setQuestion(message);
      setLoading(true);
      setPromptValue("");
      setAnswer("");

      const questionData: QuestionData = { type: 'question', content: message };
      setOrderedData(prevOrder => [...prevOrder, questionData]);

      socket.send(`chat${JSON.stringify({ message })}`);
    }
  };

  const handleDisplayResult = async (newQuestion: string) => {
    const requestId = generateRequestId();
    const researchStartTime = Date.now();

    // Log user initiation
    logUserAction('Research initiated', {
      question: newQuestion,
      settings: chatBoxSettings,
      sessionId: terminalLogger.getSessionId()
    }, requestId);

    logSystem('Starting research process', {
      question: newQuestion,
      chatBoxSettings,
      requestId
    }, requestId);

    console.log('🔍 Starting research with question:', newQuestion);
    console.log('📋 Current chatBoxSettings:', chatBoxSettings);

    setShowResult(true);
    setLoading(true);
    setQuestion(newQuestion);
    setPromptValue("");
    setAnswer("");
    setOrderedData((prevOrder) => [...prevOrder, { type: 'question', content: newQuestion }]);

    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
    const langgraphHostUrl = apiVariables.LANGGRAPH_HOST_URL;

    logSystem('Configuration check', {
      report_type: chatBoxSettings.report_type,
      langgraphHostUrl: langgraphHostUrl,
      hasLangGraph: !!langgraphHostUrl,
      apiVariables: Object.keys(apiVariables)
    }, requestId);

    console.log('🔧 Config check:', {
      report_type: chatBoxSettings.report_type,
      langgraphHostUrl: langgraphHostUrl,
      hasLangGraph: !!langgraphHostUrl
    });

    if (chatBoxSettings.report_type === 'multi_agents' && langgraphHostUrl) {
      logResearchProgress('Starting LangGraph Multi-Agent Research', 5, { langgraphHostUrl }, requestId);
      console.log('🤖 Using LangGraph multi-agents path');

      try {
        logSystem('Initiating LangGraph research stream', {
          question: newQuestion,
          source: chatBoxSettings.report_source
        }, requestId);

        let { streamResponse, host, thread_id } = await startLanggraphResearch(newQuestion, chatBoxSettings.report_source, langgraphHostUrl);

        const langsmithGuiLink = `https://smith.langchain.com/studio/thread/${thread_id}?baseUrl=${host}`;
        logSystem('LangGraph research stream initiated', {
          threadId: thread_id,
          host,
          langsmithGuiLink
        }, requestId);

        setOrderedData((prevOrder) => [...prevOrder, { type: 'langgraphButton', link: langsmithGuiLink }]);

        let previousChunk = null;
        let chunkCount = 0;
        logResearchProgress('Processing LangGraph Stream', 20, undefined, requestId);

        for await (const chunk of streamResponse) {
          chunkCount++;
          logSystem(`Processing LangGraph chunk ${chunkCount}`, {
            hasReport: !!chunk.data.report,
            reportPreview: chunk.data.report ? chunk.data.report.substring(0, 100) : null
          }, requestId);

          if (chunk.data.report != null && chunk.data.report != "Full report content here") {
            logResearchProgress('LangGraph Report Generated', 90, {
              chunkCount,
              reportLength: chunk.data.report.length
            }, requestId);

            setOrderedData((prevOrder) => [...prevOrder, { ...chunk.data, output: chunk.data.report, type: 'report' }]);
            setLoading(false);

            const totalTime = Date.now() - researchStartTime;
            logResearchComplete(totalTime, {
              type: 'langgraph',
              reportLength: chunk.data.report.length,
              chunkCount,
              question: newQuestion
            }, requestId);

          } else if (previousChunk) {
            const differences = findDifferences(previousChunk, chunk);
            logSystem(
              'Processing LangGraph differences',
              {
                differenceCount: Object.keys(differences).length,
                differences: differences,
                requestId
              }
            );
            setOrderedData((prevOrder) => [...prevOrder, { type: 'differences', content: 'differences', output: JSON.stringify(differences) }]);
          }
          previousChunk = chunk;
        }
      } catch (error) {
        logError('LangGraph research failed', error, requestId);
        console.error('❌ LangGraph research failed:', error);
        setLoading(false);
        setOrderedData((prevOrder) => [...prevOrder, {
          type: 'error',
          content: 'LangGraph Error',
          output: `Failed to start LangGraph research: ${(error as Error).message}`
        }]);
      }
    } else {
      logResearchProgress('Starting WebSocket Research', 5, {
        connectionManager: 'ResilientConnection'
      }, requestId);

      console.log('🌐 Using WebSocket research path');
      console.log('📡 Starting research with connection manager:', { newQuestion, chatBoxSettings });

      try {
        logSystem('Initiating WebSocket research', {
          question: newQuestion,
          settings: chatBoxSettings
        }, requestId);

        startResearch(newQuestion, chatBoxSettings);

        logSystem('WebSocket research initiated successfully', undefined, requestId);
      } catch (error) {
        logError('Research initialization failed', error, requestId);
        console.error('❌ Research initialization failed:', error);
        setLoading(false);
        setOrderedData((prevOrder) => [...prevOrder, {
          type: 'error',
          content: 'Research Error',
          output: `Failed to start research: ${(error as Error).message}`
        }]);
      }
    }
  };

  const reset = () => {
    const requestId = generateRequestId();
    logUserAction('Research reset initiated', {
      hadResults: showResult,
      hadAnswer: !!answer,
      dataItemsCount: orderedData.length
    }, requestId);

    logSystem('Resetting research state', {
      previousQuestion: question,
      answerLength: answer?.length || 0,
      orderedDataCount: orderedData.length
    }, requestId);

    // Reset UI states
    setShowResult(false);
    setPromptValue("");
    setIsStopped(false);

    // Clear previous research data
    setQuestion("");
    setAnswer("");
    setOrderedData([]);
    setAllLogs([]);

    // Reset feedback states
    setShowHumanFeedback(false);
    setQuestionForHuman(false);

    // Clean up connections
    stopResearch();

    logSystem('Research state reset completed', undefined, requestId);
  };

  const handleClickSuggestion = (value: string) => {
    const requestId = generateRequestId();
    logUserAction('Suggestion clicked', { suggestion: value }, requestId);

    setPromptValue(value);
    const element = document.getElementById('input-area');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  /**
   * Handles stopping the current research
   * - Closes WebSocket connection
   * - Stops loading state
   * - Marks research as stopped
   * - Preserves current results
   */
  const handleStopResearch = () => {
    const requestId = generateRequestId();
    logUserAction('Research stop requested', {
      wasLoading: loading,
      currentQuestion: question,
      currentProgress: orderedData.length
    }, requestId);

    logSystem('Stopping active research', {
      question,
      orderedDataCount: orderedData.length,
      answerLength: answer?.length || 0
    }, requestId);

    stopResearch();
    setIsStopped(true);

    logSystem('Research stopped successfully', undefined, requestId);
  };

  /**
   * Handles starting a new research
   * - Clears all previous research data and states
   * - Resets UI to initial state
   * - Closes any existing WebSocket connections
   */
  const handleStartNewResearch = () => {
    const requestId = generateRequestId();
    logUserAction('New research requested', {
      previousQuestion: question,
      sidebarWasOpen: sidebarOpen
    }, requestId);

    logSystem('Starting new research session', {
      previousQuestion: question,
      clearingDataCount: orderedData.length
    }, requestId);

    reset();
    setSidebarOpen(false);

    logSystem('New research session prepared', undefined, requestId);
  };

  // Save completed research to history
  useEffect(() => {
    // Only save when research is complete and not loading
    if (showResult && !loading && answer && question && orderedData.length > 0) {
      const requestId = generateRequestId();

      // Check if this is a new research (not loaded from history)
      const isNewResearch = !history.some(item =>
        item.question === question && item.answer === answer
      );

      if (isNewResearch) {
        logSystem('Saving completed research to history', {
          question,
          answerLength: answer.length,
          orderedDataCount: orderedData.length,
          historyCount: history.length
        }, requestId);

        saveResearch(question, answer, orderedData);

        logSystem('Research saved to history successfully', {
          newHistoryCount: history.length + 1
        }, requestId);
      } else {
        logSystem('Research already exists in history, skipping save', {
          question,
          historyCount: history.length
        }, requestId);
      }
    }
  }, [showResult, loading, answer, question, orderedData, history, saveResearch]);

  // Handle selecting a research from history
  const handleSelectResearch = (id: string) => {
    const requestId = generateRequestId();
    logUserAction('Historical research selected', { researchId: id }, requestId);

    const research = getResearchById(id);
    if (research) {
      logSystem('Loading historical research', {
        researchId: id,
        question: research.question,
        answerLength: research.answer.length,
        dataCount: research.orderedData.length
      }, requestId);

      setShowResult(true);
      setQuestion(research.question);
      setPromptValue("");
      setAnswer(research.answer);
      setOrderedData(research.orderedData);
      setLoading(false);
      setSidebarOpen(false);

      logSystem('Historical research loaded successfully', undefined, requestId);
    } else {
      logError('Failed to load historical research', { researchId: id }, requestId);
    }
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    const requestId = generateRequestId();
    logUserAction('Sidebar toggled', {
      wasOpen: sidebarOpen,
      willBeOpen: !sidebarOpen
    }, requestId);

    setSidebarOpen(!sidebarOpen);
  };

  /**
   * Processes ordered data into logs for display
   * Updates whenever orderedData changes
   */
  useEffect(() => {
    if (orderedData.length > 0) {
      const requestId = generateRequestId();
      logSystem('Processing ordered data for display', {
        orderedDataCount: orderedData.length,
        dataTypes: Array.from(new Set(orderedData.map(d => d.type)))
      }, requestId);

      const groupedData = preprocessOrderedData(orderedData);
      const statusReports = ["agent_generated", "starting_research", "planning_research", "error"];

      const newLogs = groupedData.reduce((acc: any[], data) => {
        // Process accordion blocks (grouped data)
        if (data.type === 'accordionBlock') {
          const logs = data.items.map((item: any, subIndex: any) => ({
            header: item.content,
            text: item.output,
            metadata: item.metadata,
            key: `${item.type}-${item.content}-${subIndex}`,
          }));
          return [...acc, ...logs];
        }
        // Process status reports
        else if (statusReports.includes(data.content)) {
          return [...acc, {
            header: data.content,
            text: data.output,
            metadata: data.metadata,
            key: `${data.type}-${data.content}`,
          }];
        }
        return acc;
      }, []);

      setAllLogs(newLogs);

      logSystem('Ordered data processed for display', {
        processedLogsCount: newLogs.length,
        accordionBlocks: groupedData.filter(d => d.type === 'accordionBlock').length,
        statusReports: groupedData.filter(d => statusReports.includes(d.content)).length
      }, requestId);
    }
  }, [orderedData]);

  const handleScroll = useCallback(() => {
    // Calculate if we're near bottom (within 100px)
    const scrollPosition = window.scrollY + window.innerHeight;
    const nearBottom = scrollPosition >= document.documentElement.scrollHeight - 100;

    // Show button if we're not near bottom and page is scrollable
    const isPageScrollable = document.documentElement.scrollHeight > window.innerHeight;
    setShowScrollButton(isPageScrollable && !nearBottom);
  }, []);

  // Add ResizeObserver to watch for content changes
  useEffect(() => {
    const mainContentElement = mainContentRef.current;
    const resizeObserver = new ResizeObserver(() => {
      handleScroll();
    });

    if (mainContentElement) {
      resizeObserver.observe(mainContentElement);
    }

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleScroll);

    return () => {
      if (mainContentElement) {
        resizeObserver.unobserve(mainContentElement);
      }
      resizeObserver.disconnect();
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, [handleScroll]);

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
  };

  return (
    <main className="flex min-h-screen flex-col">
      <Header
        loading={loading}
        isStopped={isStopped}
        showResult={showResult}
        onStop={handleStopResearch}
        onNewResearch={handleStartNewResearch}
        connectionStatus={getStatusDescription(researchState.status)}
        isRetrying={isRetrying}
      />

      <ResearchStatusIndicator
        researchState={researchState}
        getStatusDescription={getStatusDescription}
        isVisible={showResult && (loading || isRetrying || researchState.status !== 'idle')}
        connectionHealth={connectionHealth}
        getHealthDescription={getHealthDescription}
        getHealthColor={getHealthColor}
      />

      <ResearchSidebar
        history={history}
        onSelectResearch={handleSelectResearch}
        onNewResearch={handleStartNewResearch}
        onDeleteResearch={deleteResearch}
        isOpen={sidebarOpen}
        toggleSidebar={toggleSidebar}
      />

      <div
        ref={mainContentRef}
        className="min-h-[100vh] pt-[120px]"
      >
        {!showResult && (
          <Hero
            promptValue={promptValue}
            setPromptValue={setPromptValue}
            handleDisplayResult={handleDisplayResult}
          />
        )}

        {showResult && (
          <div className="flex h-full w-full grow flex-col justify-between">
            <div className="container w-full space-y-2">
              <div className="container space-y-2 task-components">
                <ResearchResults
                  orderedData={orderedData}
                  answer={answer}
                  allLogs={allLogs}
                  chatBoxSettings={chatBoxSettings}
                  handleClickSuggestion={handleClickSuggestion}
                  onNewSearch={handleDisplayResult}
                />
              </div>

              {showHumanFeedback && false && (
                <HumanFeedback
                  questionForHuman={questionForHuman}
                  websocket={socket}
                  onFeedbackSubmit={handleFeedbackSubmit}
                />
              )}

              <div className="pt-1 sm:pt-2" ref={chatContainerRef}></div>
            </div>
            <div id="input-area" className="container px-4 lg:px-0">
              {loading ? (
                <LoadingDots
                  message={researchState.currentTask || getStatusDescription(researchState.status)}
                  variant={
                    researchState.status === 'connecting' || researchState.status === 'reconnecting'
                      ? 'connecting'
                      : researchState.status === 'processing'
                        ? 'processing'
                        : 'default'
                  }
                />
              ) : (
                <InputArea
                  promptValue={promptValue}
                  setPromptValue={setPromptValue}
                  handleSubmit={handleChat}
                  handleSecondary={handleDisplayResult}
                  disabled={loading}
                  reset={reset}
                  isStopped={isStopped}
                />
              )}
            </div>
          </div>
        )}
      </div>
      {showScrollButton && showResult && (
        <button
          onClick={scrollToBottom}
          className="fixed bottom-8 right-8 flex items-center justify-center w-12 h-12 text-white bg-gradient-to-br from-teal-500 to-teal-600 rounded-full hover:from-teal-600 hover:to-teal-700 transform hover:scale-105 transition-all duration-200 shadow-lg z-50 backdrop-blur-sm border border-teal-400/20"
          title="Scroll to bottom"
          aria-label="Scroll to bottom"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        </button>
      )}
      <Footer setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
    </main>
  );
}
