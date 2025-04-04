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
    
    // Process the HTML to add target="_blank" to all links
    return addTargetBlankToLinks(result.toString());
  } catch (error) {
    console.error('Error converting Markdown to HTML:', error);
    return ''; // Handle error gracefully, return empty string or default content
  }
}; 