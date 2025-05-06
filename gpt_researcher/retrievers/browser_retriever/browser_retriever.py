from __future__ import annotations

import asyncio
import os
import time

from typing import TYPE_CHECKING, Any

import cv2
import numpy as np
import pytesseract

from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    from langchain.callbacks.manager import CallbackManagerForRetrieverRun
    from playwright.sync_api import Browser, Page
    from playwright.sync_api._generated import Playwright

logger: logging.Logger = get_formatted_logger(__name__)


class BrowserRetriever(BaseRetriever):
    def __init__(
        self,
        headless: bool = True,
        vision_threshold: float = 0.8,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        """
        Initialize browser session with vision capabilities.

        Args:
        ----
            headless: Run browser in headless mode.
            vision_threshold: Confidence threshold (0.0 to 1.0) for UI element detection.
        """
        self.browser: Browser | None = None
        self.headless: bool = headless
        self.page: Page | None = None
        self.vision_threshold: float = vision_threshold

    def _init_browser(self):
        """Initialize Playwright browser instance."""
        if self.browser is None:
            self.playwright: Playwright = sync_playwright().start()
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
        run_manager: CallbackManagerForRetrieverRun | None = None,
        max_results: int | None = None,
        timeout: int = 60000,
    ) -> list[Document]:
        """Execute visual web interaction flow:
            1. Navigate to target website.
            2. Detect interactive elements using OCR/vision.
            3. Perform human-like interactions (typed input, button clicks).
            4. Parse and validate results.
            5. Return Document objects with page content and metadata.

        Args:
        ----
            query: Natural language query to simulate input.
            run_manager: Callback manager for retrieval run.
            max_results: Maximum number of Document objects to return.
            timeout: Timeout for page load and interaction.

        Returns:
        -------
            List[Document]: List containing one Document with the page content.
        """
        # If max_results is the default, check environment variable
        if max_results is None:
            max_results = int(os.environ.get("MAX_SOURCES", 10))

        self._init_browser()
        try:
            # Navigate to a predetermined website (can be parameterized)
            assert self.page is not None, "Browser page not initialized"
            self.page.goto("https://example.com", timeout=timeout)

            # Implement retry logic for dynamic/AJAX content
            retries = 3
            for attempt in range(retries):
                # Wait for page stability
                time.sleep(2)
                screenshot: bytes = self.page.screenshot()
                elements: list[dict[str, Any]] = self._visual_element_detection(screenshot)
                if elements:
                    for element in elements:
                        _ = self._perform_semantic_action(element, query)
                    break
                elif attempt == retries - 1:
                    raise Exception("Dynamic content did not load properly after retries.")
                # Else retry the detection
                continue

            # Additional wait time for any AJAX-loaded content
            time.sleep(2)

            # Extract page content and build document with metadata
            content: str = self.page.content()
            metadata: dict[str, str] = {"url": self.page.url, "query": query}
            document = Document(page_content=content, metadata=metadata)
            return [document]
        except PlaywrightTimeoutError as e:
            raise Exception("Page load timed out.") from e
        finally:
            self._close_browser()

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
        max_results: int | None = None,
    ) -> list[Document]:
        """Asynchronous version of _get_relevant_documents.

        For demonstration purposes, this calls the synchronous version in a thread.

        Args:
        ----
            query: The query to search for.
            run_manager: The run manager for the retrieval.
            max_results: The maximum number of results to return.

        Returns:
        -------
            List[Document]: The list of documents.
        """
        # If max_results is the default, check environment variable
        if max_results is None:
            max_results = int(os.environ.get("MAX_SOURCES", 10))

        from functools import partial

        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        func = partial(self._get_relevant_documents, query=query, run_manager=run_manager, max_results=max_results)
        return await loop.run_in_executor(None, func)

    def _visual_element_detection(
        self,
        screenshot: bytes,
    ) -> list[dict]:
        """
        Core vision pipeline using OpenCV and Tesseract.

        Processes the screenshot to detect text regions and returns dummy representations
        of web elements with bounding box info.

        Args:
        ----
            screenshot: The screenshot image bytes.

        Returns:
        -------
            List[dict]: List of detected elements with text and positional data.
        """
        # Convert screenshot bytes to a NumPy array
        nparr = np.frombuffer(screenshot, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Convert image to grayscale and apply thresholding
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        # Use Tesseract OCR to detect text regions
        data: dict[str, Any] = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
        elements: list[dict[str, Any]] = []
        n_boxes: int = len(data["level"])
        for i in range(n_boxes):
            try:
                conf_str: str = data["conf"][i]
                confidence: float = float(conf_str) if conf_str != "-1" else 0.0
            except ValueError:
                confidence = 0.0
            # Multiply threshold by 100 because Tesseract confidence is out of 100
            if confidence >= self.vision_threshold * 100:
                element: dict[str, Any] = {
                    "text": data["text"][i],
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "confidence": confidence,
                }
                elements.append(element)
        return elements

    async def _perform_semantic_action(
        self,
        element: dict[str, Any],
        query: str,
    ):
        """Execute a human-like interaction with a detected element using Playwright.

        This function simulates user interactions such as clicking and typing,
        based on the detected element's properties.

        Args:
        ----
            element: A dictionary representing the detected UI element, including its
                    bounding box ('left', 'top', 'width', 'height') and text content ('text').
            query: The query text to be entered into the element, if applicable.
        """
        element_text: str = element.get("text", "").lower()
        left: int | None = element.get("left")
        top: int | None = element.get("top")
        width: int | None = element.get("width")
        height: int | None = element.get("height")

        if left is None or top is None or width is None or height is None:
            logger.warning("Element missing bounding box information. Skipping interaction.")
            return

        # Calculate the element's center coordinates for precise clicking
        center_x: int = left + width // 2
        center_y: int = top + height // 2

        try:
            # Move the mouse to the element's center and click
            assert self.page is not None, "Browser page not initialized"
            assert self.page.mouse is not None, "Mouse not initialized"
            self.page.mouse.move(center_x, center_y)
            self.page.mouse.click(center_x, center_y)

            # If the element is a search input or text area, simulate typing the query
            if not str(element_text).strip() or "search" in str(element_text) or str(element["element_type"]) in ["input", "textarea"]:
                assert self.page.keyboard is not None, "Keyboard not initialized"
                self.page.keyboard.type(query, delay=100)  # Simulate typing with a delay

                # If it's a search input, also press Enter to submit the query
                if element["element_type"] == "input":
                    self.page.keyboard.press("Enter")

            # Handle other element types (e.g., buttons, links) with specific actions
            elif element["element_type"] == "button":
                logger.info(f"Clicking button with text: {element_text}")
                self.page.click(f"text={element_text}")  # Use text selector for robustness
            elif element["element_type"] == "a":  # Handle links
                href: str | None = element.get("href")
                if href:
                    logger.info(f"Navigating to link: {href}")
                    self.page.goto(href)
                else:
                    logger.warning("Link has no href attribute.")

            logger.info(f"Interacted with element: {element_text[:50]}...")  # Log the interaction

        except Exception as e:
            logger.exception(f"Error interacting with element: {e.__class__.__name__}: {e}")
