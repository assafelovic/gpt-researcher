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

  const [socket, setSocket] = useState(null);
  const [orderedData, setOrderedData] = useState([]);
  const heartbeatInterval = useRef(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [orderedData]);

  const startResearch = (chatBoxSettings) => {
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
          const contentAndType = `${data.content}-${data.type}`;
          setOrderedData((prevOrder) => [...prevOrder, { ...data, contentAndType }]);

          if (data.type === 'report') {
            setAnswer((prev) => prev + data.output);
          } else if (data.type === 'path') {
            setLoading(false);
            newSocket.close();
            setSocket(null);
          }
        };

        newSocket.onopen = () => {
          const { task, report_type, report_source, tone } = chatBoxSettings;
          let data = "start " + JSON.stringify({ task: promptValue, report_type, report_source, tone, headers });
          newSocket.send(data);

          // Start sending heartbeat messages every 30 seconds
          heartbeatInterval.current = setInterval(() => {
            newSocket.send(JSON.stringify({ type: 'ping' }));
          }, 30000);
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

  const handleDisplayResult = async (newQuestion?: string) => {
    newQuestion = newQuestion || promptValue;

    setShowResult(true);
    setLoading(true);
    setQuestion(newQuestion);
    setPromptValue("");
    setAnswer(""); // Reset answer for new query

    // Add the new question to orderedData
    setOrderedData((prevOrder) => [...prevOrder, { type: 'question', content: newQuestion }]);

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

  const preprocessOrderedData = (data) => {
    const groupedData = [];
    let currentAccordionGroup = null;
    let currentSourceGroup = null;
    let currentReportGroup = null;
    let finalReportGroup = null;
  
    data.forEach((item) => {
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
        } else if (content === 'added_source_url') {
          if (!currentSourceGroup) {
            currentSourceGroup = { type: 'sourceBlock', items: [] };
            groupedData.push(currentSourceGroup);
          }
          const hostname = new URL(metadata).hostname.replace('www.', '');
          currentSourceGroup.items.push({ name: hostname, url: metadata });
        } else if (type !== 'path' && content !== '') {
          if (!currentAccordionGroup) {
            currentAccordionGroup = { type: 'accordionBlock', items: [] };
            groupedData.push(currentAccordionGroup);
          }
          currentAccordionGroup.items.push(item);
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

    return groupedData.map((data, index) => {
      if (data.type === 'accordionBlock') {
        const uniqueKey = `accordionBlock-${index}`;
        const logs = data.items.map((item, subIndex) => ({
          header: item.content,
          text: item.output,
          key: `${item.type}-${item.content}-${subIndex}`,
        }));

        return <LogMessage key={uniqueKey} logs={logs} />;

      } else if (data.type === 'sourceBlock') {
        const uniqueKey = `sourceBlock-${index}`;
        return <Sources key={uniqueKey} sources={data.items} isLoading={false} />;
      } else if (data.type === 'reportBlock') {
        const uniqueKey = `reportBlock-${index}`;
        return <Answer key={uniqueKey} answer={data.content} />;
      } else if (data.type === 'langgraphButton') {
        const uniqueKey = `langgraphButton-${index}`;
        return (
          <div></div>
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
              <div className="container space-y-2">
                {renderComponentsInOrder()}
              </div>

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