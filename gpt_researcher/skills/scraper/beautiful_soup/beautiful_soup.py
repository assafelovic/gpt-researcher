from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..utils import get_relevant_images, extract_title

class BeautifulSoupScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self):
        """
        This function scrapes content from a webpage by making a GET request, parsing the HTML using
        BeautifulSoup, and extracting script and style elements before returning the cleaned content.
        
        Returns:
          The `scrape` method is returning the cleaned and extracted content from the webpage specified
        by the `self.link` attribute. The method fetches the webpage content, removes script and style
        tags, extracts the text content, and returns the cleaned content as a string. If any exception
        occurs during the process, an error message is printed and an empty string is returned.
        """
        try:
            response = self.session.get(self.link, timeout=4)
            soup = BeautifulSoup(
                response.content, "lxml", from_encoding=response.encoding
            )

            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            raw_content = self.get_content_from_url(soup)
            lines = (line.strip() for line in raw_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = "\n".join(chunk for chunk in chunks if chunk)

            image_urls = get_relevant_images(soup, self.link)
            
            # Extract the title using the utility function
            title = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""

    def get_content_from_url(self, soup: BeautifulSoup) -> str:
        """Get the relevant text from the soup with improved filtering"""
        text_elements = []
        tags = ["h1", "h2", "h3", "h4", "h5", "p", "li", "div", "span"]

        for element in soup.find_all(tags):
            # Skip empty elements
            if not element.text.strip():
                continue

            # Skip elements with very short text (likely buttons or links)
            if len(element.text.split()) < 3:
                continue

            # Check if the element is likely to be navigation or a menu
            parent_classes = element.parent.get('class', [])
            if any(cls in ['nav', 'menu', 'sidebar', 'footer'] for cls in parent_classes):
                continue

            # Remove excess whitespace and join lines
            cleaned_text = ' '.join(element.text.split())

            # Add the cleaned text to our list of elements
            text_elements.append(cleaned_text)

        # Join all text elements with newlines
        return '\n\n'.join(text_elements)

    def get_relevant_images(self, soup: BeautifulSoup) -> list:
        """Extract relevant images from the page"""
        image_urls = []
        main_content = soup.find('main') or soup.find('article') or soup.find('body')

        if main_content:
            # Look for images in the main content area
            images = main_content.find_all('img', src=True)
            for img in images:
                # Check for common header image classes or IDs
                if any(cls in img.get('class', []) for cls in ['header', 'featured', 'hero', 'thumbnail']):
                    image_urls.append(urljoin(self.link, img['src']))
                # Check for images with certain dimensions (assuming header images are larger)
                elif img.get('width') and img.get('height'):
                    if int(img['width']) >= 600 and int(img['height']) >= 300:
                        image_urls.append(urljoin(self.link, img['src']))

        # If no images found in main content, look for the first large image on the page
        if not image_urls:
            first_large_image = soup.find('img', src=True, width=lambda x: x and int(x) >= 600)
            if first_large_image:
                image_urls.append(urljoin(self.link, first_large_image['src']))

        return image_urls[:3]  # Limit to top 3 most relevant images
