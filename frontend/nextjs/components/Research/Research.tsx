import { useRef } from 'react';
import Answer from "../ResearchBlocks/Answer";
import Sources from "../ResearchBlocks/Sources";
import Question from "../ResearchBlocks/Question";
import SubQuestions from "../ResearchBlocks/elements/SubQuestions";
import LogsSection from "../ResearchBlocks/LogsSection";
import ImageSection from "../ResearchBlocks/ImageSection";
import AccessReport from "../Task/AccessReport";

interface GroupedData {
  type: string;
  content?: string;
  metadata?: any;
  items?: any[];
  output?: string;
}

interface ResearchProps {
  orderedData: any[];
  allLogs: any[];
  answer: string;
  handleClickSuggestion: (value: string) => void;
  preprocessOrderedData: (data: any[]) => GroupedData[];
}

export const Research = ({ 
  orderedData, 
  allLogs, 
  answer, 
  handleClickSuggestion,
  preprocessOrderedData 
}: ResearchProps) => {
  const groupedData = preprocessOrderedData(orderedData);
  
  const imageComponents = groupedData
    .filter((data: GroupedData) => data.type === 'imagesBlock')
    .map((data: GroupedData, index: number) => (
      <ImageSection key={`images-${index}`} metadata={data.metadata} />
    ));

  const reportComponents = groupedData
    .filter((data: GroupedData) => data.type === 'reportBlock')
    .map((data: GroupedData, index: number) => (
      <Answer key={`reportBlock-${index}`} answer={data.content || ''} />
    ));

  const pathData = groupedData.find((data: GroupedData) => data.type === 'path');

  const otherComponents = groupedData
    .map((data: GroupedData, index: number) => {
      if (data.type === 'sourceBlock') {
        return <Sources key={`sourceBlock-${index}`} sources={data.items || []}/>;
      } else if (data.type === 'question') {
        return <Question key={`question-${index}`} question={data.content || ''} />;
      } else if (data.type === 'chat') {
        return <Answer key={`chat-${index}`} answer={data.content || ''} />;
      } else if (data.content === 'subqueries') {
        return (
          <SubQuestions
            key={`subqueries-${index}`}
            metadata={data.metadata}
            handleClickSuggestion={handleClickSuggestion}
          />
        );
      }
      return null;
    }).filter(Boolean);

  return (
    <>
      {otherComponents}
      {orderedData.length > 0 && <LogsSection logs={allLogs} />}
      {imageComponents}
      {reportComponents}
      {pathData && <AccessReport accessData={pathData.output} report={answer} />}
    </>
  );
}; 