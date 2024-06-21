"use client";

import Answer from "@/components/Answer";
import Footer from "@/components/Footer";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import InputArea from "@/components/InputArea";
import SimilarTopics from "@/components/SimilarTopics";
import Sources from "@/components/Sources";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  createParser,
  ParsedEvent,
  ReconnectInterval,
} from "eventsource-parser";

import Report from '../components/Task/Report';
import AgentLogs from '../components/Task/AgentLogs';
import AccessReport from '../components/Task/AccessReport';
import Accordion from '../components/Task/Accordion';

import { handleSourcesAndAnswer, handleSimilarQuestions, handleLanggraphAnswer } from '../actions/apiActions';

export default function Home() {
  const [promptValue, setPromptValue] = useState("");
  const [question, setQuestion] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [sources, setSources] = useState<{ name: string; url: string }[]>([]);
  const [answer, setAnswer] = useState("");
  const [similarQuestions, setSimilarQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [chatBoxSettings, setChatBoxSettings] = useState({report_source: 'web', report_type: 'multi_agents'});
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [socket, setSocket] = useState(null);
  const [orderedData, setOrderedData] = useState([]);

  useEffect(() => {
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
        }
      };

      return () => newSocket.close();
    }
  }, []);

  const startResearch = (chatBoxSettings) => {
    const {task, report_type, report_source} = chatBoxSettings;
    
    let data = "start " + JSON.stringify({ task: promptValue, report_type, report_source });
    socket.send(data);
  };

  const handleDisplayResult = async (newQuestion?: string) => {
    newQuestion = newQuestion || promptValue;

    setShowResult(true);
    setLoading(true);
    setQuestion(newQuestion);
    setPromptValue("");

    if (chatBoxSettings.report_type === 'multi_agents') {
      await handleLanggraphAnswer(newQuestion);
    } else {
      startResearch(chatBoxSettings);

      await Promise.all([
        handleSourcesAndAnswer(newQuestion),
        handleSimilarQuestions(newQuestion),
      ]);
    }

    setLoading(false);
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
  };

  const preprocessOrderedData = (data) => {
    const groupedData = [];
    let currentAccordionGroup = null;
    let currentSourceGroup = null;

    data.forEach((item) => {
      const { type, content, metadata } = item;

      if (content === 'subqueries' || type === 'report') {
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
          groupedData.push(currentSourceGroup);
          currentSourceGroup = null;
        }
        groupedData.push(item);
      }
    });

    return groupedData;
  };

  const renderComponentsInOrder = () => {
    const groupedData = preprocessOrderedData(orderedData);

    return groupedData.map((data, index) => {
      if (data.type === 'accordionBlock') {
        const uniqueKey = `accordionBlock-${index}`;
        const logs = data.items.map((item, subIndex) => ({
          header: item.content,
          text: item.output,
          key: `${item.type}-${item.content}-${subIndex}`,
        }));
        return <Accordion key={uniqueKey} logs={logs} />;
      } else if (data.type === 'sourceBlock') {
        const uniqueKey = `sourceBlock-${index}`;
        return <Sources key={uniqueKey} sources={data.items} isLoading={false} />;
      } else {
        const { type, content, metadata, output } = data;
        const uniqueKey = `${type}-${content}-${index}`;

        if (content === 'subqueries') {
          return (
            <div key={uniqueKey} className="flex flex-wrap items-center justify-center gap-2.5 pb-[30px] lg:flex-nowrap lg:justify-normal">
              {metadata.map((item, subIndex) => (
                <div
                  className="flex h-[35px] cursor-pointer items-center justify-center gap-[5px] rounded border border-solid border-[#C1C1C1] bg-[#EDEDEA] px-2.5 py-2"
                  onClick={() => handleClickSuggestion(item)}
                  key={`${uniqueKey}-${subIndex}`}
                >
                  <span className="text-sm font-light leading-[normal] text-[#1B1B16]">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          );
        } else if (type === 'report') {
          return <Answer key={uniqueKey} answer={output} />;
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
      <main className="h-full px-4 pb-4">
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
                <div className="container flex w-full items-start gap-3 px-5 pt-2 lg:px-10">
                  <div className="flex w-fit items-center gap-4">
                    <Image
                      src={"/img/message-question-circle.svg"}
                      alt="message"
                      width={30}
                      height={30}
                      className="size-[24px]"
                    />
                    <p className="pr-5 font-bold uppercase leading-[152%] text-black">
                      Question:
                    </p>
                  </div>
                  <div className="grow">&quot;{question}&quot;</div>
                </div>
                {renderComponentsInOrder()}
              </div>

              <div className="pt-1 sm:pt-2" ref={chatContainerRef}></div>
            </div>
            <div className="container px-4 lg:px-0">
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