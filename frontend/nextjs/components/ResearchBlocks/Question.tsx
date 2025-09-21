import React from 'react';
import Image from "next/image";

interface QuestionProps {
  question: string;
}

const Question: React.FC<QuestionProps> = ({ question }) => {
  return (
    <div className="container w-full flex flex-col sm:flex-row items-start gap-3 pt-5 mb-5 px-4 sm:px-6 py-4 rounded-lg border border-gray-700/30 backdrop-blur-sm bg-black/20 mt-5">
      <div className="flex items-center gap-2 sm:gap-4">
        <img
          src={"/img/message-question-circle.svg"}
          alt="message"
          width={24}
          height={24}
          className="w-6 h-6"
        />
        {/*<p className="font-bold uppercase leading-[152%] text-teal-200">
          Research Task:
        </p>*/}
      </div>
      <div className="grow text-white break-words max-w-full log-message mt-1 sm:mt-0 font-medium">{question}</div>
    </div>
  );
};

export default Question;
