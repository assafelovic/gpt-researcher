import Image from "next/image";
import { FC } from "react";
import InputArea from "./InputArea";

import logo from './logo.svg';

type THeroProps = {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleDisplayResult: () => void;
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
        <div className="landing">
          <h1 className="text-4xl font-extrabold mx-auto lg:text-7xl">
            Say Goodbye to <br/>
            <span
              style={{
                backgroundImage: 'linear-gradient(to right, #9867F0, #ED4E50)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Hours of Research
            </span>
          </h1>
        </div>
        

        {/* input section */}
        <div className="w-full max-w-[708px] pb-6">
          <InputArea
            promptValue={promptValue}
            setPromptValue={setPromptValue}
            handleDisplayResult={handleDisplayResult}
          />
        </div>

        {/* Suggestions section */}
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
    name: "What happened to the dinosaurs",
    icon: "/img/dinosaur.svg",
  },
  {
    id: 2,
    name: "Help me plan an adventure to ",
    icon: "/img/hiker.svg",
  },
  {
    id: 3,
    name: "What made Michael Jordan the best",
    icon: "/img/dunk.svg",
  },
];

export default Hero;
