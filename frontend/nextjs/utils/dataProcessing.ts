import { Data } from '../types/data';
import { consolidateSourceAndImageBlocks } from './consolidateBlocks';

export const preprocessOrderedData = (data: Data[]) => {
  let groupedData: any[] = [];
  let currentAccordionGroup: any = null;
  let currentSourceGroup: any = null;
  let currentReportGroup: any = null;
  let finalReportGroup: any = null;
  let sourceBlockEncountered = false;
  let lastSubqueriesIndex = -1;
  const seenUrls = new Set<string>();
  // console.log('websocket data before its processed',data)

  data.forEach((item: any) => {
    const { type, content, metadata, output, link } = item;

    if (type === 'question') {
      groupedData.push({ type: 'question', content });
    } else if (type === 'report') {
      // Start a new report group if we don't have one
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
        }
      
        if (!seenUrls.has(metadata)) {
          seenUrls.add(metadata);
          let hostname = "";
          try {
            if (typeof metadata === 'string') {
              hostname = new URL(metadata).hostname.replace('www.', '');
            }
          } catch (e) {
            hostname = "unknown";
          }
          currentSourceGroup.items.push({ name: hostname, url: metadata });
        }
      
        // Add this block to ensure the source group is added to groupedData
        if (currentSourceGroup.items.length > 0 && !groupedData.includes(currentSourceGroup)) {
          groupedData.push(currentSourceGroup);
          sourceBlockEncountered = true;
        }
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
        if (currentReportGroup) {
          // Find and remove the previous reportBlock
          const reportBlockIndex = groupedData.findIndex(
            item => item === currentReportGroup
          );
          if (reportBlockIndex !== -1) {
            groupedData.splice(reportBlockIndex, 1);
          }
          currentReportGroup = null;  // Reset the current report group
        }
        groupedData.push(item);
      }
    }
  });

  groupedData = consolidateSourceAndImageBlocks(groupedData);
  return groupedData;
}; 