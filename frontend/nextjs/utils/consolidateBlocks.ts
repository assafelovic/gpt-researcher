export const consolidateSourceAndImageBlocks = (groupedData: any[]) => {
  // Consolidate sourceBlocks
  const consolidatedSourceBlock = {
    type: 'sourceBlock',
    items: groupedData
      .filter(item => item.type === 'sourceBlock')
      .flatMap(block => block.items || [])
      .filter((item, index, self) => 
        index === self.findIndex(t => t.url === item.url)
      )
  };

  // Consolidate imageBlocks
  const consolidatedImageBlock = {
    type: 'imagesBlock',
    metadata: groupedData
      .filter(item => item.type === 'imagesBlock')
      .flatMap(block => block.metadata || [])
  };

  // Remove all existing sourceBlocks and imageBlocks
  groupedData = groupedData.filter(item => 
    item.type !== 'sourceBlock' && item.type !== 'imagesBlock'
  );

  // Add consolidated blocks if they have items
  if (consolidatedSourceBlock.items.length > 0) {
    groupedData.push(consolidatedSourceBlock);
  }
  if (consolidatedImageBlock.metadata.length > 0) {
    groupedData.push(consolidatedImageBlock);
  }

  return groupedData;
};