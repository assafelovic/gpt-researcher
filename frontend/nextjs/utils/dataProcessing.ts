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

    if (type === 'question') {
      groupedData.push({ type: 'question', content });
    } else if (type === 'report') {
      if (!currentReportGroup) {
        currentReportGroup = { type: 'reportBlock', content: '' };
        groupedData.push(currentReportGroup);
      }
      currentReportGroup.content += output;
    } else if (content === 'selected_images') {
      groupedData.push({ type: 'imagesBlock', metadata });
    } else if (type === 'logs' && content === 'research_report') {
      if (!finalReportGroup) {
        finalReportGroup = { type: 'reportBlock', content: '' };
        groupedData.push(finalReportGroup);
      }
      finalReportGroup.content += output.report;
    } else if (type === 'langgraphButton') {
      groupedData.push({ type: 'langgraphButton', link });
    } else if (type === 'chat') {
      groupedData.push({ type: 'chat', content: content });
    } else {
      if (currentReportGroup) {
        currentReportGroup = null;
      }

      if (content === 'subqueries') {
        if (currentAccordionGroup) {
          currentAccordionGroup = null;
        }
        if (currentSourceGroup) {
          groupedData.push(currentSourceGroup);
          currentSourceGroup = null;
        }
        groupedData.push(item);
        lastSubqueriesIndex = groupedData.length - 1;
      } else if (type === 'sourceBlock') {
        currentSourceGroup = item;
        if (lastSubqueriesIndex !== -1) {
          groupedData.splice(lastSubqueriesIndex + 1, 0, currentSourceGroup);
          lastSubqueriesIndex = -1;
        } else {
          groupedData.push(currentSourceGroup);
        }
        sourceBlockEncountered = true;
        currentSourceGroup = null;
      } else if (content === 'added_source_url') {
        if (!currentSourceGroup) {
          currentSourceGroup = { type: 'sourceBlock', items: [] };
          if (lastSubqueriesIndex !== -1) {
            groupedData.splice(lastSubqueriesIndex + 1, 0, currentSourceGroup);
            lastSubqueriesIndex = -1;
          } else {
            groupedData.push(currentSourceGroup);
          }
          sourceBlockEncountered = true;
        }
        let hostname = "";
        try {
          if (typeof metadata === 'string') {
            hostname = new URL(metadata).hostname.replace('www.', '');
          }
        } catch (e) {
          hostname = "unknown";
        }
        currentSourceGroup.items.push({ name: hostname, url: metadata });
      } else if (type !== 'path' && content !== '') {
        if (sourceBlockEncountered) {
          if (!currentAccordionGroup) {
            currentAccordionGroup = { type: 'accordionBlock', items: [] };
            groupedData.push(currentAccordionGroup);
          }
          currentAccordionGroup.items.push(item);
        } else {
          groupedData.push(item);
        }
      } else {
        if (currentAccordionGroup) {
          currentAccordionGroup = null;
        }
        if (currentSourceGroup) {
          currentSourceGroup = null;
        }
        groupedData.push(item);
      }
    }
  });

  return groupedData;
}; 