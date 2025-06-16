import { Data } from '../types/data';
import { consolidateSourceAndImageBlocks } from './consolidateBlocks';
import { logSystem, logAgentWork, logResearchProgress, generateRequestId } from './terminalLogger';

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

export const addData = (
  data: Data,
  setOrderedData: (value: Data[] | ((prevVar: Data[]) => Data[])) => void
) => {
  // console.log('websocket data before its processed',data)

  const requestId = generateRequestId();
  logSystem('Processing WebSocket data', data, requestId);

  setOrderedData((prevOrder) => [...prevOrder, data]);
};

export const processWebSocketData = (
  data: any,
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>
): Data[] | undefined => {
  const requestId = generateRequestId();

  try {
    // Log the incoming data
    logSystem('Processing WebSocket message', {
      type: data.type,
      hasOutput: !!data.output,
      hasContent: !!data.content
    }, requestId);

    // Extract agent information if present
    if (data.agent || data.agent_type) {
      const agentType = data.agent || data.agent_type;
      const task = data.task || data.content || 'Processing';
      logAgentWork(agentType, task, undefined, requestId);
    }

    // Process different message types
    switch (data.type) {
      case 'logs':
        logSystem(`Research Log: ${data.output}`, undefined, requestId);
        break;

      case 'report':
        logSystem('Received research report', {
          length: data.output?.length,
          preview: data.output?.substring(0, 100)
        }, requestId);

        if (data.output) {
          setAnswer((prev: string) => prev + data.output);
        }
        break;

      case 'path':
      case 'chat':
        logResearchProgress('Research completed', 100, { type: data.type }, requestId);
        break;

      case 'agent_work':
        const progress = data.progress || undefined;
        logAgentWork(data.agent_type || 'Unknown', data.task || 'Processing', progress, requestId);
        break;

      default:
        logSystem(`Unknown message type: ${data.type}`, data, requestId);
    }

    // Add to ordered data if it has content
    if (data.content || data.output || data.type) {
      const contentAndType = `${data.content || data.output || ''}-${data.type || 'unknown'}`;
      const processedData = { ...data, contentAndType };

      setOrderedData((prevOrder) => {
        const newOrder = [...prevOrder, processedData];
        logSystem(`Updated data order, total items: ${newOrder.length}`, undefined, requestId);
        return newOrder;
      });

      return [processedData];
    }

    return undefined;

  } catch (error) {
    logSystem('Error processing WebSocket data', error, requestId);
    return undefined;
  }
};
