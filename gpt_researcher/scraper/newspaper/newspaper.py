from newspaper import Article


class NewspaperScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self) -> str:
        """
        This Python function scrapes an article from a given link, extracts the title and text content,
        and returns them concatenated with a colon.
        
        Returns:
          The `scrape` method returns a string that contains the title of the article followed by a
        colon and the text of the article. If the title or text is not present, an empty string is
        returned. If an exception occurs during the scraping process, an error message is printed and an
        empty string is returned.
        """
        try:
            article = Article(
                self.link,
                language="en",
                memoize_articles=False,
                fetch_images=False,
            )
            article.download()
            article.parse()

            title = article.title
            text = article.text

            # If title, summary are not present then return None
            if not (title and text):
                return ""

            return f"{title} : {text}"

        except Exception as e:
            print("Error! : " + str(e))
            return ""
