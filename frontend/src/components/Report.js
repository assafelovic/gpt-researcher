import React from 'react';
import MarkdownView from 'react-showdown';

export default function Report() {
  const markdown = `
        # Welcome to React Showdown :+1:

        To get started, edit the markdown in \`example/src/App.tsx\`.

        | Column 1 | Column 2 |
        |----------|----------|
        | A1       | B1       |
        | A2       | B2       |
  `;

  return (
    <MarkdownView
      markdown={markdown}
      options={{ tables: true, emoji: true }}
    />
  );
};