"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { useWebSocket } from '@/hooks/useWebSocket';
import { startLanggraphResearch } from '../components/Langgraph/Langgraph';
import findDifferences from '../helpers/findDifferences';
import { Data, ChatBoxSettings, QuestionData } from '../types/data';
import { preprocessOrderedData } from '../utils/dataProcessing';
import { ResearchResults } from '../components/ResearchResults';

import Header from "@/components/Header";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
import InputArea from "@/components/ResearchBlocks/elements/InputArea";
import HumanFeedback from "@/components/HumanFeedback";
import LoadingDots from "@/components/LoadingDots";

export default function Home() {
  const [promptValue, setPromptValue] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatBoxSettings, setChatBoxSettings] = useState<ChatBoxSettings>({ 
    report_source: 'web', 
    report_type: 'research_report', 
    tone: 'Objective' 
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

  const { socket, initializeWebSocket } = useWebSocket(
    setOrderedData,
    setAnswer,
    setLoading,
    setShowHumanFeedback,
    setQuestionForHuman
  );

  const handleFeedbackSubmit = (feedback: string | null) => {
    if (socket) {
      socket.send(JSON.stringify({ type: 'human_feedback', content: feedback }));
    }
    setShowHumanFeedback(false);
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
    setShowResult(true);
    setLoading(true);
    setQuestion(newQuestion);
    setPromptValue("");
    setAnswer("");
    setOrderedData((prevOrder) => [...prevOrder, { type: 'question', content: newQuestion }]);

    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
    const langgraphHostUrl = apiVariables.LANGGRAPH_HOST_URL;

    if (chatBoxSettings.report_type === 'multi_agents' && langgraphHostUrl) {
      let { streamResponse, host, thread_id } = await startLanggraphResearch(newQuestion, chatBoxSettings.report_source, langgraphHostUrl);
      const langsmithGuiLink = `https://smith.langchain.com/studio/thread/${thread_id}?baseUrl=${host}`;
      setOrderedData((prevOrder) => [...prevOrder, { type: 'langgraphButton', link: langsmithGuiLink }]);

      let previousChunk = null;
      for await (const chunk of streamResponse) {
        if (chunk.data.report != null && chunk.data.report != "Full report content here") {
          setOrderedData((prevOrder) => [...prevOrder, { ...chunk.data, output: chunk.data.report, type: 'report' }]);
          setLoading(false);
        } else if (previousChunk) {
          const differences = findDifferences(previousChunk, chunk);
          setOrderedData((prevOrder) => [...prevOrder, { type: 'differences', content: 'differences', output: JSON.stringify(differences) }]);
        }
        previousChunk = chunk;
      }
    } else {
      initializeWebSocket(newQuestion, chatBoxSettings);
    }
  };

  const reset = () => {
    setShowResult(false);
    setPromptValue("");
    setQuestion("");
    setAnswer("");
  };

  const handleClickSuggestion = (value: string) => {
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
    if (socket) {
      socket.close();
    }
    setLoading(false);
    setIsStopped(true);
  };

  /**
   * Handles starting a new research
   * - Clears all previous research data and states
   * - Resets UI to initial state
   * - Closes any existing WebSocket connections
   */
  const handleStartNewResearch = () => {
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
    if (socket) {
      socket.close();
    }
    setLoading(false);
  };

  /**
   * Processes ordered data into logs for display
   * Updates whenever orderedData changes
   */
  useEffect(() => {
    const groupedData = preprocessOrderedData(orderedData);
    const statusReports = ["agent_generated", "starting_research", "planning_research"];
    
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
    const resizeObserver = new ResizeObserver(() => {
      handleScroll();
    });

    if (mainContentRef.current) {
      resizeObserver.observe(mainContentRef.current);
    }

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleScroll);
    
    return () => {
      if (mainContentRef.current) {
        resizeObserver.unobserve(mainContentRef.current);
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
    <>
      <Header 
        loading={loading}
        isStopped={isStopped}
        showResult={showResult}
        onStop={handleStopResearch}
        onNewResearch={handleStartNewResearch}
      />
      <main ref={mainContentRef} className="min-h-[100vh] pt-[120px]">
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
                />
              </div>

              {showHumanFeedback && (
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
                <LoadingDots />
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
      </main>
      {showScrollButton && showResult && (
        <button
          onClick={scrollToBottom}
          className="fixed bottom-8 right-8 flex items-center justify-center w-12 h-12 text-white bg-[rgb(168,85,247)] rounded-full hover:bg-[rgb(147,51,234)] transform hover:scale-105 transition-all duration-200 shadow-lg z-50"
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
    </>
  );
}