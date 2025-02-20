import time
import cv2
import pytesseract
import numpy as np
from typing import List
from langchain.schema import Document
from langchain.retrievers import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Browser, Page

class BrowserRetriever(BaseRetriever):
    def __init__(self, headless: bool = True, vision_threshold: float = 0.8):
        """
        Initialize browser session with vision capabilities.
        
        Args:
            headless: Run browser in headless mode.
            vision_threshold: Confidence threshold (0.0 to 1.0) for UI element detection.
        """
        self.headless: bool = headless
        self.vision_threshold: float = vision_threshold
        self.browser: Browser | None = None
        self.page: Page | None = None

    def _init_browser(self):
        """Initialize Playwright browser instance."""
        if self.browser is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()

    def _close_browser(self):
        """Close and cleanup the browser session."""
        if self.browser:
            self.browser.close()
            self.playwright.stop()
            self.browser = None
            self.page = None

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        max_results: int = 5,
    ) -> List[Document]:
        """
        Execute visual web interaction flow:
          1. Navigate to target website.
          2. Detect interactive elements using OCR/vision.
          3. Perform human-like interactions (typed input, button clicks).
          4. Parse and validate results.
          5. Return Document objects with page content and metadata.
        
        Args:
            query: Natural language query to simulate input.
            run_manager: Callback manager for retrieval run.
            max_results: Maximum number of Document objects to return.
        
        Returns:
            List[Document]: List containing one Document with the page content.
        """
        self._init_browser()
        try:
            # Navigate to a predetermined website (can be parameterized)
            self.page.goto("https://example.com", timeout=60000)
            
            # Implement retry logic for dynamic/AJAX content
            retries = 3
            for attempt in range(retries):
                # Wait for page stability
                time.sleep(2)
                screenshot = self.page.screenshot()
                elements = self._visual_element_detection(screenshot)
                if elements:
                    for element in elements:
                        self._perform_semantic_action(element, query)
                    break
                elif attempt == retries - 1:
                    raise Exception("Dynamic content did not load properly after retries.")
                # Else retry the detection
                continue

            # Additional wait time for any AJAX-loaded content
            time.sleep(2)

            # Extract page content and build document with metadata
            content = self.page.content()
            metadata = {"url": self.page.url, "query": query}
            document = Document(page_content=content, metadata=metadata)
            return [document]
        except PlaywrightTimeoutError as e:
            raise Exception("Page load timed out.") from e
        finally:
            self._close_browser()

    async def _aget_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun, max_results: int = 5) -> List[Document]:
        """
        Asynchronous version of _get_relevant_documents.
        
        For demonstration purposes, this calls the synchronous version in a thread.
        """
        import asyncio
        from functools import partial

        loop = asyncio.get_event_loop()
        func = partial(self._get_relevant_documents, query=query, run_manager=run_manager, max_results=max_results)
        return await loop.run_in_executor(None, func)

    def _visual_element_detection(self, screenshot: bytes) -> List[dict]:
        """
        Core vision pipeline using OpenCV and Tesseract.
        
        Processes the screenshot to detect text regions and returns dummy representations
        of web elements with bounding box info.
        
        Args:
            screenshot: The screenshot image bytes.
        
        Returns:
            List[dict]: List of detected elements with text and positional data.
        """
        # Convert screenshot bytes to a NumPy array
        nparr = np.frombuffer(screenshot, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Convert image to grayscale and apply thresholding
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        # Use Tesseract OCR to detect text regions
        data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
        elements = []
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            try:
                conf_str = data['conf'][i]
                confidence = float(conf_str) if conf_str != '-1' else 0.0
            except ValueError:
                confidence = 0.0
            # Multiply threshold by 100 because Tesseract confidence is out of 100
            if confidence >= self.vision_threshold * 100:
                element = {
                    "text": data['text'][i],
                    "left": data['left'][i],
                    "top": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i],
                    "confidence": confidence
                }
                elements.append(element)
        return elements

    async def _perform_semantic_action(self, element: dict, query: str):
        """
        Execute a human-like interaction with a detected element using Playwright.

        This function simulates user interactions such as clicking and typing,
        based on the detected element's properties.

        Args:
            element: A dictionary representing the detected UI element, including its
                     bounding box ('left', 'top', 'width', 'height') and text content ('text').
            query: The query text to be entered into the element, if applicable.
        """
        element_text = element.get("text", "").lower()
        left = element.get("left")
        top = element.get("top")
        width = element.get("width")
        height = element.get("height")

        if left is None or top is None or width is None or height is None:
            logger.warning("Element missing bounding box information. Skipping interaction.")
            return

        # Calculate the element's center coordinates for precise clicking
        center_x = left + width // 2
        center_y = top + height // 2

        try:
            # Move the mouse to the element's center and click
            await self.page.mouse.move(center_x, center_y)
            await self.page.mouse.click(center_x, center_y)

            # If the element is a search input or text area, simulate typing the query
            if element_text.strip() == "" or "search" in element_text or element['element_type'] in ['input', 'textarea']:
                await self.page.keyboard.type(query, delay=100)  # Simulate typing with a delay

                # If it's a search input, also press Enter to submit the query
                if element['element_type'] == 'input':
                    await self.page.keyboard.press("Enter")

            # Handle other element types (e.g., buttons, links) with specific actions
            elif element['element_type'] == 'button':
                logger.info(f"Clicking button with text: {element_text}")
                await self.page.click(f"text={element_text}")  # Use text selector for robustness
            elif element['element_type'] == 'a':  # Handle links
                href = element.get("href")
                if href:
                    logger.info(f"Navigating to link: {href}")
                    await self.page.goto(href)
                else:
                    logger.warning("Link has no href attribute.")

            logger.info(f"Interacted with element: {element_text[:50]}...")  # Log the interaction

        except Exception as e:
            logger.error(f"Error interacting with element: {e}")

        # Example of storing interaction history (optional)
        if not hasattr(self, 'interaction_history'):
            self.interaction_history = []
        self.interaction_history.append({"element": element, "query": query})