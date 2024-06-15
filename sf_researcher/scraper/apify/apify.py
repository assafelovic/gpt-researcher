# apify/apify.py

import os
from apify_client import ApifyClient

class ApifyScraper:
    def __init__(self):
        self.client = ApifyClient(os.getenv('APIFY_API_KEY'))
        self.actor_id = 'apify/website-content-crawler'

    def create_scraping_task(self, url):
        # Define the input for the actor
        run_input = {
            'startUrls': [{'url': url}],
            'maxCrawlingDepth': 0,
            'maxPagesPerCrawl': 1,
            'proxyConfiguration': {'useApifyProxy': True},
            'timeoutSecs': 60,
        }

        # Run the actor and wait for the result
        run = self.client.actor(self.actor_id).call(run_input=run_input)
        return run['defaultDatasetId']

    def fetch_results(self, dataset_id):
        # Fetch the results from the dataset
        dataset_items = self.client.dataset(dataset_id).list_items().items

        # Extract raw text content
        if dataset_items:
            raw_data = dataset_items[0].get('text', '')
            return raw_data
        else:
            return ''

    def scrape(self, url):
        dataset_id = self.create_scraping_task(url)
        return self.fetch_results(dataset_id)
