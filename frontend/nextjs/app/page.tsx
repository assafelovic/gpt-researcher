"use client";

import Answer from "@/components/Answer";
import Footer from "@/components/Footer";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import InputArea from "@/components/InputArea";
import Sources from "@/components/Sources";
import Question from "@/components/Question";
import SubQuestions from "@/components/SubQuestions";
import { useRef, useState, useEffect } from "react";
import AccessReport from '../components/Task/AccessReport';
import LogMessage from '../components/Task/LogMessage';
import { startLanggraphResearch } from '../components/Langgraph/Langgraph';
import findDifferences from '../helpers/findDifferences';
import HumanFeedback from "@/components/HumanFeedback";
import LoadingDots from "@/components/LoadingDots";
import { Data, ChatBoxSettings, QuestionData, WebSocketMessage, AccordionGroup, SourceGroup, ReportGroup } from '../types/data';

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
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [orderedData, setOrderedData] = useState<Data[]>([]);
  const heartbeatInterval = useRef<number>();
  const [showHumanFeedback, setShowHumanFeedback] = useState(false);
  const [questionForHuman, setQuestionForHuman] = useState<boolean>(false);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [orderedData]);

  const initializeWebSocket = (message: string) => {
    if (typeof window === 'undefined') return;

    const { protocol, pathname, host } = window.location;
    const wsHost = host.includes('localhost') ? 'localhost:8000' : host;
    const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${wsHost}${pathname}ws`;

    const newSocket = new WebSocket(ws_uri);
    setSocket(newSocket);

    newSocket.onopen = () => newSocket.send(message);
    newSocket.onmessage = handleWebSocketMessage;
    newSocket.onclose = () => {
      clearInterval(heartbeatInterval.current);
      setSocket(null);
    };
  };

  const handleWebSocketMessage = (event: MessageEvent) => {
    const data: WebSocketMessage = JSON.parse(event.data);
    console.log('websocket data caught in frontend: ', data);

    if (data.type === 'human_feedback' && data.content === 'request') {
      setQuestionForHuman(data.output);
      setShowHumanFeedback(true);
    } else {
      const contentAndType = `${data.content}-${data.type}`;
      setOrderedData(prevOrder => [...prevOrder, { ...data, contentAndType }]);

      if (data.type === 'report') {
        setAnswer(prev => prev + (data.output || ''));
      } else if (data.type === 'path' || data.type === 'chat') {
        setLoading(false);
      }
    }
  };

  const startResearch = (settings: ChatBoxSettings) => {
    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
    const headers = {
      'retriever': apiVariables.RETRIEVER,
      'langchain_api_key': apiVariables.LANGCHAIN_API_KEY,
      'openai_api_key': apiVariables.OPENAI_API_KEY,
      'tavily_api_key': apiVariables.TAVILY_API_KEY,
      'google_api_key': apiVariables.GOOGLE_API_KEY,
      'google_cx_key': apiVariables.GOOGLE_CX_KEY,
      'bing_api_key': apiVariables.BING_API_KEY,
      'searchapi_api_key': apiVariables.SEARCHAPI_API_KEY,
      'serpapi_api_key': apiVariables.SERPAPI_API_KEY,
      'serper_api_key': apiVariables.SERPER_API_KEY,
      'searx_url': apiVariables.SEARX_URL
    };

    const { task, report_type, report_source, tone } = settings;
    const message = "start " + JSON.stringify({ task: promptValue, report_type, report_source, tone, headers });

    if (!socket) {
      initializeWebSocket(message);
    } else {
      socket.send(message);
    }
  };

  const handleFeedbackSubmit = (feedback: string | null) => {
    if (socket) {
      socket.send(JSON.stringify({ type: 'human_feedback', content: feedback }));
    }
    setShowHumanFeedback(false);
  };

  const handleChat = async (message: string) => {
    if (socket) {
      setShowResult(true);
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
    setPromptValue("");
    setAnswer("");

    setOrderedData(prevOrder => [...prevOrder, { type: 'question', content: newQuestion }]);

    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
    const langgraphHostUrl = apiVariables.LANGGRAPH_HOST_URL;

    if (chatBoxSettings.report_type === 'multi_agents' && langgraphHostUrl) {
      await handleLanggraphResearch(newQuestion, langgraphHostUrl);
    } else {
      startResearch({ ...chatBoxSettings, task: newQuestion });
    }
  };

  const handleLanggraphResearch = async (question: string, hostUrl: string) => {
    const { streamResponse, host, thread_id } = await startLanggraphResearch(
      question, 
      chatBoxSettings.report_source, 
      hostUrl
    );

    const langsmithGuiLink = `https://smith.langchain.com/studio/thread/${thread_id}?baseUrl=${host}`;
    setOrderedData(prevOrder => [...prevOrder, { type: 'langgraphButton', link: langsmithGuiLink }]);

    let previousChunk = null;

    for await (const chunk of streamResponse) {
      if (chunk.data.report != null && chunk.data.report != "Full report content here") {
        setOrderedData(prevOrder => [...prevOrder, { ...chunk.data, output: chunk.data.report, type: 'report' }]);
        setLoading(false);
      } else if (previousChunk) {
        const differences = findDifferences(previousChunk, chunk);
        setOrderedData(prevOrder => [...prevOrder, { type: 'differences', content: 'differences', output: JSON.stringify(differences) }]);
      }
      previousChunk = chunk;
    }
  };

  const reset = () => {
    setShowResult(false);
    setPromptValue("");
    setAnswer("");
    setOrderedData([]);
  };

  const handleClickSuggestion = (value: string) => {
    setPromptValue(value);
    const element = document.getElementById('input-area');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const preprocessOrderedData = (data: Data[]) => {
    const groupedData: Data[] = [];
    let currentAccordionGroup: AccordionGroup | null = null;
    let currentSourceGroup: SourceGroup | null = null;
    let currentReportGroup: ReportGroup | null = null;
    let finalReportGroup: ReportGroup | null = null;
    let sourceBlockEncountered = false;
    let lastSubqueriesIndex = -1;

    data.forEach((item) => {
      const { type, content, metadata, output, link } = item;

      if (type === 'report') {
        if (!currentReportGroup) {
          currentReportGroup = { type: 'reportBlock', content: '' };
          groupedData.push(currentReportGroup);
        }
        currentReportGroup.content += output || '';
      } else if (type === 'logs' && content === 'research_report') {
        if (!finalReportGroup) {
          finalReportGroup = { type: 'reportBlock', content: '' };
          groupedData.push(finalReportGroup);
        }
        if (output && typeof output === 'object' && 'report' in output) {
          finalReportGroup.content += output.report || '';
        }
      } else if (type === 'langgraphButton' && link) {
        groupedData.push({ type: 'langgraphButton', link });
      } else if (type === 'question' && content) {
        groupedData.push({ type: 'question', content });
      } else if (type === 'chat' && content) {
        groupedData.push({ type: 'chat', content });
      } else {
        if (currentReportGroup) {
          currentReportGroup = null;
        }

        if (content === 'subqueries') {
          if (currentAccordionGroup) {
            currentAccordionGroup = null;
          }
          if (currentSourceGroup) {
            groupedData.push(currentSourceGroup);
            currentSourceGroup = null;
          }
          groupedData.push(item);
          lastSubqueriesIndex = groupedData.length - 1;
        } else if (type === 'sourceBlock') {
          currentSourceGroup = item as SourceGroup;
          if (lastSubqueriesIndex !== -1) {
            groupedData.splice(lastSubqueriesIndex + 1, 0, currentSourceGroup);
            lastSubqueriesIndex = -1;
          } else {
            groupedData.push(currentSourceGroup);
          }
          sourceBlockEncountered = true;
          currentSourceGroup = null;
        } else if (content === 'added_source_url') {
          if (!currentSourceGroup) {
            currentSourceGroup = { type: 'sourceBlock', items: [] };
            if (lastSubqueriesIndex !== -1) {
              groupedData.splice(lastSubqueriesIndex + 1, 0, currentSourceGroup);
              lastSubqueriesIndex = -1;
            } else {
              groupedData.push(currentSourceGroup);
            }
            sourceBlockEncountered = true;
          }
          let hostname = "";
          try {
            hostname = typeof metadata === 'string' ? new URL(metadata).hostname.replace('www.', '') : "unknown";
          } catch (e) {
            console.error(`Invalid URL: ${metadata}`, e);
            hostname = "unknown";
          }
          currentSourceGroup.items.push({ name: hostname, url: metadata });
        } else if (type !== 'path' && content !== '') {
          if (sourceBlockEncountered) {
            if (!currentAccordionGroup) {
              currentAccordionGroup = { type: 'accordionBlock', items: [] };
              groupedData.push(currentAccordionGroup);
            }
            currentAccordionGroup.items.push({
              content: item.content || '',
              output: item.output || '',
              metadata: item.metadata,
              type: item.type
            });
          } else {
            groupedData.push(item);
          }
        } else {
          if (currentAccordionGroup) {
            currentAccordionGroup = null;
          }
          if (currentSourceGroup) {
            currentSourceGroup = null;
          }
          groupedData.push(item);
        }
      }
    });

    return groupedData;
  };

  const renderComponentsInOrder = () => {
    const groupedData = preprocessOrderedData(orderedData);
    const statusReports = ["agent_generated", "starting_research", "planning_research"];

    return groupedData.map((data, index) => {
      const key = `${data.type}-${index}`;

      switch (data.type) {
        case 'accordionBlock':
          const logs = data.items?.map((item, subIndex) => ({
            header: item.content || '',
            text: item.output || '',
            metadata: item.metadata,
            key: `${item.type}-${item.content}-${subIndex}`,
          }));
          return <LogMessage key={key} logs={logs || []} />;

        case 'sourceBlock':
          return <Sources key={key} sources={data.items || []} />;

        case 'reportBlock':
          return <Answer key={key} answer={data.content || ''} />;

        case 'langgraphButton':
          return <div key={key}></div>;

        case 'question':
          return <Question key={key} question={data.content || ''} />;

        case 'chat':
          return <Answer key={key} answer={data.content || ''} />;

        default:
          if (data.content === 'subqueries') {
            return (
              <SubQuestions
                key={key}
                metadata={data.metadata}
                handleClickSuggestion={handleClickSuggestion}
              />
            );
          } else if (data.type === 'path') {
            return <AccessReport key={key} accessData={data.output} report={answer} />;
          } else if (statusReports.includes(data.content || '')) {
            const logs = [{
              header: data.content || '',
              text: data.output || '',
              metadata: data.metadata,
              key: `${data.type}-${data.content}`,
            }];
            return <LogMessage key={key} logs={logs} />;
          }
          return null;
      }
    });
  };

  return (
    <>
      <Header />
      <main className="min-h-[calc(100vh-64px)]">
        {!showResult ? (
          <Hero
            promptValue={promptValue}
            setPromptValue={setPromptValue}
            handleDisplayResult={handleDisplayResult}
          />
        ) : (
          <div className="flex h-full w-full grow flex-col justify-between">
            <div className="container w-full space-y-2">
              <div className="container space-y-2 task-components">
                {renderComponentsInOrder()}
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
                />
              )}
            </div>
          </div>
        )}
      </main>
      <Footer setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
    </>
  );
}