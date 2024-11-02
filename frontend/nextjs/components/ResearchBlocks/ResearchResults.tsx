import React from 'react';
import Answer from './Answer';
import Sources from './Sources';
import Question from './Question';
import SubQuestions from './elements/SubQuestions';
import LogsSection from './LogsSection';
import ImageSection from './ImageSection';
import AccessReport from '../Task/AccessReport';

interface ResearchResultsProps {
  groupedData: any[];
  allLogs: any[];
  answer: string;
  handleClickSuggestion: (value: string) => void;
}

export const ResearchResults: React.FC<ResearchResultsProps> = ({
  groupedData,
  allLogs,
  answer,
  handleClickSuggestion,
}) => {
  const imageComponents = groupedData
    .filter(data => data.type === 'imagesBlock')
    .map((data, index) => (
      <ImageSection key={`images-${index}`} metadata={data.metadata} />
    ));

  const reportComponents = groupedData
    .filter(data => data.type === 'reportBlock')
    .map((data, index) => (
      <Answer key={`reportBlock-${index}`} answer={data.content} />
    ));

  const pathData = groupedData.find(data => data.type === 'path');

  const otherComponents = groupedData
    .map((data, index) => {
      if (data.type === 'sourceBlock') {
        return <Sources key={`sourceBlock-${index}`} sources={data.items}/>;
      } else if (data.type === 'question') {
        return <Question key={`question-${index}`} question={data.content} />;
      } else if (data.type === 'chat') {
        return <Answer key={`chat-${index}`} answer={data.content} />;
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
      {groupedData.length > 0 && <LogsSection logs={allLogs} />}
      {imageComponents}
      {reportComponents}
      {pathData && <AccessReport accessData={pathData.output} report={answer} />}
    </>
  );
}; 