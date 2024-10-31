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
import Accordion from '../components/Task/Accordion';
import LogMessage from '../components/Task/LogMessage';

import { startLanggraphResearch } from '../components/Langgraph/Langgraph';
import findDifferences from '../helpers/findDifferences';
import HumanFeedback from "@/components/HumanFeedback";

interface BaseData {
  type: string;
}

interface BasicData extends BaseData {
  type: 'basic';
  content: string;
}

interface LanggraphButtonData extends BaseData {
  type: 'langgraphButton';
  link: string;
}

interface DifferencesData extends BaseData {
  type: 'differences';
  content: string;
  output: string;
}

type Data = BasicData | LanggraphButtonData | DifferencesData;


export default function Home() {
  const [promptValue, setPromptValue] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatBoxSettings, setChatBoxSettings] = useState({ report_source: 'web', report_type: 'research_report', tone: 'Objective' });
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [question, setQuestion] = useState("");
  const [sources, setSources] = useState<{ name: string; url: string }[]>([]);
  const [similarQuestions, setSimilarQuestions] = useState<string[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [orderedData, setOrderedData] = useState<Data[]>([]);
  const heartbeatInterval = useRef<number>();
  const [showHumanFeedback, setShowHumanFeedback] = useState(false);
  const [questionForHuman, setQuestionForHuman] = useState(false);
  

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [orderedData]);

  const startResearch = (chatBoxSettings:any) => {
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

    if (!socket) {
      if (typeof window !== 'undefined') {
        const { protocol, pathname } = window.location;
        let { host } = window.location;
        host = host.includes('localhost') ? 'localhost:8000' : host;
        const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${host}${pathname}ws`;

        const newSocket = new WebSocket(ws_uri);
        setSocket(newSocket);

        newSocket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log('websocket data caught in frontend: ', data);

          if (data.type === 'human_feedback' && data.content === 'request') {
            console.log('triggered human feedback condition')
            setQuestionForHuman(data.output)
            setShowHumanFeedback(true);
          } else {
            const contentAndType = `${data.content}-${data.type}`;
            setOrderedData((prevOrder) => [...prevOrder, { ...data, contentAndType }]);

            if (data.type === 'report') {
              setAnswer((prev:any) => prev + data.output);
            } else if (data.type === 'path') {
              setLoading(false);
              newSocket.close();
              setSocket(null);
            }
          }
          
        };

        newSocket.onopen = () => {
          const { task, report_type, report_source, tone } = chatBoxSettings;
          let data = "start " + JSON.stringify({ task: promptValue, report_type, report_source, tone, headers });
          newSocket.send(data);

          // Start sending heartbeat messages every 30 seconds
          // heartbeatInterval.current = setInterval(() => {
          //   newSocket.send(JSON.stringify({ type: 'ping' }));
          // }, 30000);
        };

        newSocket.onclose = () => {
          clearInterval(heartbeatInterval.current);
          setSocket(null);
        };
      }
    } else {
      const { task, report_type, report_source, tone } = chatBoxSettings;
      let data = "start " + JSON.stringify({ task: promptValue, report_type, report_source, tone, headers });
      socket.send(data);
    }
  };

  // Add this function to handle feedback submission
  const handleFeedbackSubmit = (feedback: string | null) => {
    console.log('user feedback is passed to handleFeedbackSubmit: ', feedback);
    if (socket) {
      socket.send(JSON.stringify({ type: 'human_feedback', content: feedback }));
    }
    setShowHumanFeedback(false);
  };

  const handleDisplayResult = async (newQuestion?: string) => {
    newQuestion = newQuestion || promptValue;

    setShowResult(true);
    setLoading(true);
    setQuestion(newQuestion);
    setPromptValue("");
    setAnswer(""); // Reset answer for new query

    // Add the new question to orderedData
    setOrderedData((prevOrder:any) => [...prevOrder, { type: 'question', content: newQuestion }]);

    const { report_type, report_source, tone } = chatBoxSettings;

    // Retrieve LANGGRAPH_HOST_URL from local storage or state
    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
    const langgraphHostUrl = apiVariables.LANGGRAPH_HOST_URL;

    if (report_type === 'multi_agents' && langgraphHostUrl) {

      let { streamResponse, host, thread_id } = await startLanggraphResearch(newQuestion, report_source, langgraphHostUrl);

      const langsmithGuiLink = `https://smith.langchain.com/studio/thread/${thread_id}?baseUrl=${host}`;

      console.log('langsmith-gui-link in page.tsx', langsmithGuiLink);
      // Add the Langgraph button to orderedData
      setOrderedData((prevOrder) => [...prevOrder, { type: 'langgraphButton', link: langsmithGuiLink }]);

      let previousChunk = null;

      for await (const chunk of streamResponse) {
        console.log(chunk);
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
      startResearch(chatBoxSettings);

      // await Promise.all([
      //   handleSourcesAndAnswer(newQuestion),
      //   handleSimilarQuestions(newQuestion),
      // ]);
    }
  };

  const reset = () => {
    setShowResult(false);
    setPromptValue("");
    setQuestion("");
    setAnswer("");
    setSources([]);
    setSimilarQuestions([]);
  };

  const handleClickSuggestion = (value: string) => {
    setPromptValue(value);
    const element = document.getElementById('input-area');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const preprocessOrderedData = (data:any) => {

    const groupedData: any[] = [];
    let currentAccordionGroup:any = null;
    let currentSourceGroup:any = null;
    let currentReportGroup:any = null;
    let finalReportGroup:any = null;
    let sourceBlockEncountered = false;
    let lastSubqueriesIndex = -1;
  
    data.forEach((item:any, index:any) => {
      const { type, content, metadata, output, link } = item;
  
      if (type === 'report') {
        if (!currentReportGroup) {
          currentReportGroup = { type: 'reportBlock', content: '' };
          groupedData.push(currentReportGroup);
        }
        currentReportGroup.content += output;
      } else if (type === 'logs' && content === 'research_report') {
        if (!finalReportGroup) {
          finalReportGroup = { type: 'reportBlock', content: '' };
          groupedData.push(finalReportGroup);
        }
        finalReportGroup.content += output.report;
      } else if (type === 'langgraphButton') {
        groupedData.push({ type: 'langgraphButton', link });
      } else if (type === 'question') {
        groupedData.push({ type: 'question', content });
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
          currentSourceGroup = item;
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
            if (typeof metadata === 'string') {
              hostname = new URL(metadata).hostname.replace('www.', '');
            }
          } catch (e) {
            console.error(`Invalid URL: ${metadata}`, e);
            hostname = "unknown"; // Default or fallback value
          }
          currentSourceGroup.items.push({ name: hostname, url: metadata });
        } else if (type !== 'path' && content !== '') {
          if (sourceBlockEncountered) {
            if (!currentAccordionGroup) {
              currentAccordionGroup = { type: 'accordionBlock', items: [] };
              groupedData.push(currentAccordionGroup);
            }
            currentAccordionGroup.items.push(item);
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
    console.log('orderedData in renderComponentsInOrder: ', groupedData)
    let statusReports = ["agent_generated","starting_research","planning_research"]

    return groupedData.map((data, index) => {
      if (data.type === 'accordionBlock') {
        const uniqueKey = `accordionBlock-${index}`;
        const logs = data.items.map((item:any, subIndex:any) => ({
          header: item.content,
          text: item.output,
          metadata: item.metadata,
          key: `${item.type}-${item.content}-${subIndex}`,
        }));

        return (
           <div className="container mx-auto">
              <LogMessage key={uniqueKey} logs={logs} />
            </div>
        )

      } else if (data.type === 'sourceBlock') {
        const uniqueKey = `sourceBlock-${index}`;
        return <Sources key={uniqueKey} sources={data.items}/>;
      } else if (data.type === 'reportBlock') {
        const uniqueKey = `reportBlock-${index}`;
        return <Answer key={uniqueKey} answer={data.content} />;
      } else if (data.type === 'langgraphButton') {
        const uniqueKey = `langgraphButton-${index}`;
        return (
          <div key={uniqueKey}></div>
          // <div key={uniqueKey} className="flex justify-center py-4">
          //   <a
          //     href={data.link}
          //     target="_blank"
          //     rel="noopener noreferrer"
          //     className="px-4 py-2 text-white bg-[#0DB7ED] rounded"
          //   >
          //     View the full Langgraph logs here
          //   </a>
          // </div>
        );
      } else if (data.type === 'question') {
        const uniqueKey = `question-${index}`;
        return <Question key={uniqueKey} question={data.content} />;
      } else {
        const { type, content, metadata, output } = data;
        const uniqueKey = `${type}-${content}-${index}`;

        if (content === 'subqueries') {
          return (
            <SubQuestions
              key={uniqueKey}
              metadata={data.metadata}
              handleClickSuggestion={handleClickSuggestion}
            />
          );
        } else if (type === 'path') {
          return <AccessReport key={uniqueKey} accessData={output} report={answer} />;
        } else if (statusReports.includes(data.content)) {
          const uniqueKey = `accordionBlock-${index}`;
          const logs = [{
            header: data.content,
            text: data.output,
            metadata: data.metadata,
            key: `${data.type}-${data.content}`,
          }]

          return <LogMessage key={uniqueKey} logs={logs} />;
        } else {
          return null;
        }
      }
    });
  };

  return (
    <>
      <Header />
      <main className="h-full px-4 pb-4 pt-10">
        {!showResult && (
          <Hero
            promptValue={promptValue}
            setPromptValue={setPromptValue}
            handleDisplayResult={handleDisplayResult}
          />
        )}

        {showResult && (
          <div className="flex h-full min-h-[68vh] w-full grow flex-col justify-between">
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
              <InputArea
                promptValue={promptValue}
                setPromptValue={setPromptValue}
                handleDisplayResult={handleDisplayResult}
                disabled={loading}
                reset={reset}
              />
            </div>
          </div>
        )}
      </main>
      <Footer setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
    </>
  );
}