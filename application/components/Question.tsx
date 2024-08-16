import Image from "next/image";

interface QuestionProps {
  question: string;
}

const Question: React.FC<QuestionProps> = ({ question }) => {
  return (
    <div className="container flex w-full items-start gap-3 pt-2">
      <div className="flex w-fit items-center gap-4">
        <Image
          src={"/img/message-question-circle.svg"}
          alt="message"
          width={30}
          height={30}
          className="size-[24px]"
        />
        <p className="pr-5 font-bold uppercase leading-[152%] text-white">
          Question:
        </p>
      </div>
      <div className="grow text-white">&quot;{question}&quot;</div>
    </div>
  );
};

export default Question;