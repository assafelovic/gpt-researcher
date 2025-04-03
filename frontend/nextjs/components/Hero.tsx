import Image from "next/image";
import React, { FC } from "react";
import InputArea from "./ResearchBlocks/elements/InputArea";

type THeroProps = {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleDisplayResult: (query : string) => void;
};

const Hero: FC<THeroProps> = ({
  promptValue,
  setPromptValue,
  handleDisplayResult,
}) => {
  const handleClickSuggestion = (value: string) => {
    setPromptValue(value);
  };

  return (
    <div className="relative overflow-hidden">
      {/* Background gradient elements */}
      <div className="absolute top-[-100px] left-[-100px] w-[400px] h-[400px] rounded-full bg-purple-600/20 blur-[100px] -z-10"></div>
      <div className="absolute top-[20%] right-[-100px] w-[350px] h-[350px] rounded-full bg-pink-600/20 blur-[100px] -z-10"></div>
      
      <div className="flex flex-col items-center justify-center py-8 md:py-12 lg:pt-8 lg:pb-16">
        <div className="landing flex flex-col items-center mb-8 md:mb-12">
          <h1 className="text-4xl font-extrabold text-center lg:text-7xl mb-6">
            Say Goodbye to <br />
            <span
              className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent animate-pulse"
            >
              Hours of Research
            </span>
          </h1>
          <h2 className="text-xl font-light text-center px-4 mb-10 md:mb-12 text-gray-300 max-w-2xl">
            Say Hello to GPT Researcher, your AI mate for rapid insights and comprehensive research
          </h2>
          
          {/* Visual element */}
          <div className="hidden md:block relative w-20 h-20 mb-8">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-spin-slow opacity-80"></div>
            <div className="absolute inset-2 bg-black rounded-full flex items-center justify-center">
              <img src="/img/gptr-logo.png" alt="GPT Researcher" className="w-12 h-12" />
            </div>
          </div>
        </div>

        {/* Input section */}
        <div className="w-full max-w-[708px] pb-8 md:pb-10 px-4">
          <InputArea
            promptValue={promptValue}
            setPromptValue={setPromptValue}
            handleSubmit={handleDisplayResult}
          />
        </div>

        {/* Suggestions section */}
        <div className="flex flex-wrap items-center justify-center gap-3 md:gap-4 pb-8 md:pb-10 px-4 lg:flex-nowrap lg:justify-normal">
          {suggestions.map((item) => (
            <div
              className="flex h-[40px] cursor-pointer items-center justify-center gap-[5px] rounded-full border border-solid border-gray-700 bg-gray-800/50 hover:bg-gray-700/60 px-4 py-2 transition-all duration-200 hover:scale-105 shadow-lg"
              onClick={() => handleClickSuggestion(item?.name)}
              key={item.id}
            >
              <img
                src={item.icon}
                alt={item.name}
                width={18}
                height={16}
                className="w-[18px]"
              />
              <span className="text-sm font-medium leading-[normal] text-gray-200">
                {item.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

type suggestionType = {
  id: number;
  name: string;
  icon: string;
};

const suggestions: suggestionType[] = [
  {
    id: 1,
    name: "Stock analysis on ",
    icon: "/img/stock2.svg",
  },
  {
    id: 2,
    name: "Help me plan an adventure to ",
    icon: "/img/hiker.svg",
  },
  {
    id: 3,
    name: "What are the latest news on ",
    icon: "/img/news.svg",
  },
];

export default Hero;
