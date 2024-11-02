import React from 'react';
import Question from './ResearchBlocks/Question';
import Answer from './ResearchBlocks/Answer';
import Sources from './ResearchBlocks/Sources';
import ImageSection from './ResearchBlocks/ImageSection';
import SubQuestions from './ResearchBlocks/elements/SubQuestions';
import LogsSection from './ResearchBlocks/LogsSection';
import AccessReport from './ResearchBlocks/AccessReport';
import { preprocessOrderedData } from '../utils/dataProcessing';
import { Data } from '../types/data';

interface ResearchResultsProps {
  orderedData: Data[];
  answer: string;
  allLogs: any[];
  handleClickSuggestion: (value: string) => void;
}

export const ResearchResults: React.FC<ResearchResultsProps> = ({
  orderedData,
  answer,
  allLogs,
  handleClickSuggestion
}) => {
  const groupedData = preprocessOrderedData(orderedData);
  const pathData = groupedData.find(data => data.type === 'path');
  const initialQuestion = groupedData.find(data => data.type === 'question');

  const chatComponents = groupedData
    .filter(data => {
      if (data.type === 'question' && data === initialQuestion) {
        return false;
      }
      return (data.type === 'question' || data.type === 'chat');
    })
    .map((data, index) => {
      if (data.type === 'question') {
        return <Question key={`question-${index}`} question={data.content} />;
      } else {
        return <Answer key={`chat-${index}`} answer={data.content} />;
      }
    });

  const sourceComponents = groupedData
    .filter(data => data.type === 'sourceBlock')
    .map((data, index) => (
      <Sources key={`sourceBlock-${index}`} sources={data.items}/>
    ));

  const imageComponents = groupedData
    .filter(data => data.type === 'imagesBlock')
    .map((data, index) => (
      <ImageSection key={`images-${index}`} metadata={data.metadata} />
    ));

  const initialReport = groupedData.find(data => data.type === 'reportBlock');
  const subqueriesComponent = groupedData.find(data => data.content === 'subqueries');

  return (
    <>
      {initialQuestion && <Question question={initialQuestion.content} />}
      {subqueriesComponent && (
        <SubQuestions
          metadata={subqueriesComponent.metadata}
          handleClickSuggestion={handleClickSuggestion}
        />
      )}
      {orderedData.length > 0 && <LogsSection logs={allLogs} />}
      {sourceComponents}
      {imageComponents}
      {initialReport && <Answer answer={initialReport.content} />}
      {pathData && <AccessReport accessData={pathData.output} report={answer} />}
      {chatComponents}
    </>
  );
}; 