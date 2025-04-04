import { remark } from 'remark';
import html from 'remark-html';
import remarkGfm from 'remark-gfm';
import { Compatible } from "vfile";

/**
 * Adds target="_blank" and rel="noopener noreferrer" attributes to all links in HTML content
 * @param htmlContent - The HTML content containing links
 * @returns The processed HTML with target="_blank" added to all links
 */
export const addTargetBlankToLinks = (htmlContent: string): string => {
  return htmlContent.replace(
    /<a(.*?)href="(.*?)"(.*?)>/gi,
    '<a$1href="$2"$3 target="_blank" rel="noopener noreferrer">'
  );
};

/**
 * Fixes the list item paragraph issue in HTML content
 * This specifically addresses the problem where numbered list items with bold text
 * have an extra line break between the marker and content
 * @param htmlContent - The HTML content with possible list formatting issues
 * @returns The processed HTML with fixed list formatting
 */
export const fixListItemParagraphIssue = (htmlContent: string): string => {
  // This regex looks for list items with a paragraph immediately inside
  // and removes the paragraph tags while preserving the content
  return htmlContent.replace(
    /<li>\s*<p>([\s\S]*?)<\/p>/g,
    '<li>$1'
  );
};

/**
 * Converts markdown to HTML with GitHub Flavored Markdown support and adds target="_blank" to links
 * @param markdown - The markdown content to convert
 * @returns Promise with the HTML content
 */
export const markdownToHtml = async (markdown: Compatible | string): Promise<string> => {
  try {
    const result = await remark()
      .use(remarkGfm) // Add GitHub Flavored Markdown support (tables, strikethrough, etc.)
      .use(html, { sanitize: false })
      .process(markdown);
    
    // Get the HTML string
    let htmlString = result.toString();
    
    // Apply fixes
    htmlString = fixListItemParagraphIssue(htmlString);
    htmlString = addTargetBlankToLinks(htmlString);
    
    return htmlString;
  } catch (error) {
    console.error('Error converting Markdown to HTML:', error);
    return ''; // Handle error gracefully, return empty string or default content
  }
}; 