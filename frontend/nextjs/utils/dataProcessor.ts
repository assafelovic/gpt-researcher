import { Data } from '../types/data';

export const preprocessOrderedData = (data: Data[]) => {
  const groupedData: any[] = [];
  let currentAccordionGroup: any = null;
  let currentSourceGroup: any = null;
  let currentReportGroup: any = null;
  let finalReportGroup: any = null;
  let sourceBlockEncountered = false;
  let lastSubqueriesIndex = -1;

  data.forEach((item: any) => {
    const { type, content, metadata, output, link } = item;

    if (type === 'report') {
      if (!currentReportGroup) {
        currentReportGroup = { type: 'reportBlock', content: '' };
        groupedData.push(currentReportGroup);
      }
      currentReportGroup.content += output;
    } else if (type === 'logs' && content === 'research_report') {
      if (!finalReportGroup) {
        finalReportGroup = { type: 'reportBlock', content: '' };
        groupedData.push(finalReportGroup);
      }
      finalReportGroup.content += output.report;
    } 
    // ... rest of the preprocessing logic
  });

  return groupedData;
}; 