import Image from "next/image";

interface QuestionProps {
  question: string;
}

const Question: React.FC<QuestionProps> = ({ question }) => {
  return (
    <div className="container w-full flex flex-col sm:flex-row items-start gap-3 pt-5 mb-2">
      <div className="flex items-center gap-2 sm:gap-4">
        <Image
          src={"/img/message-question-circle.svg"}
          alt="message"
          width={24}
          height={24}
          className="w-6 h-6"
        />
        <p className="font-bold uppercase leading-[152%] text-white">
          Research Task:
        </p><br/>
      </div>
      <div className="grow text-white break-words max-w-full log-message">&quot;{question}&quot;</div>
    </div>
  );
};

export default Question;
