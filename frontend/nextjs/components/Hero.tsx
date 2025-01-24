import Image from "next/image";
import { FC } from "react";
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
    <div>
      <div className="flex flex-col items-center justify-center">
        <div className="landing flex flex-col items-center">
          <h1 className="text-4xl font-extrabold text-center lg:text-7xl">
            Transform Your Research with <br />
            <span
              style={{
                backgroundImage: 'linear-gradient(to right, #9867F0, #ED4E50)', 
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              AI-Powered Insights
            </span>
          </h1>
          <h2 className="text-xl md:text-2xl font-light text-center px-4 mb-10 text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Unlock powerful research capabilities with Content Spells AI Researcher - your intelligent companion for generating comprehensive insights and in-depth analysis in minutes
          </h2>
        </div>

        {/* Input section */}
        <div className="w-full max-w-[708px] pb-6">
          <InputArea
            promptValue={promptValue}
            setPromptValue={setPromptValue}
            handleSubmit={handleDisplayResult}
          />
        </div>

        {/* Suggestions section
        <div className="flex flex-wrap items-center justify-center gap-2.5 pb-[30px] lg:flex-nowrap lg:justify-normal">
          {suggestions.map((item) => (
            <div
              className="flex h-[35px] cursor-pointer items-center justify-center gap-[5px] rounded border border-solid border-[#C1C1C1] bg-[#EDEDEA] px-2.5 py-2"
              onClick={() => handleClickSuggestion(item?.name)}
              key={item.id}
            >
              <Image
                src={item.icon}
                alt={item.name}
                width={18}
                height={16}
                className="w-[18px]"
              />
              <span className="text-sm font-light leading-[normal] text-[#1B1B16]">
                {item.name}
              </span>
            </div>
          ))}
        </div> */}
      </div>
    </div>
  );
};


export default Hero;
