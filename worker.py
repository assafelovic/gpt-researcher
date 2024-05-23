#worker.py

import os
import redis
from rq import Worker, Queue, Connection
from backend.report_type.custom_detailed_report.custom_detailed_report import CustomDetailedReport

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

import requests

def send_to_salesforce(report, salesforce_id):
    print(f"Salesforce report: {report}")
    url = "https://fundpath-dev-ed.develop.my.salesforce.com/services/apexrest/compliance_report_response"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 00DQy00000770H2!AQEAQC7f6uBPuNFd9dUOc2icQGMycxxDa_DNaLwGozxXf9wFAd1cMFhzu1G7G2nNnjp5cePLiGNWYQclmxRBJ1pB101WMrxX",
        "Cookie": "BrowserId=Cw4X-1zQEe6mwN_5Z-AtVA; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1"
    }
    data = report.dict()
    data["salesforce_id"] = [salesforce_id]  # Wrap salesforce_id in a list
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Compliance report sent to the salesforce site successfully.")
    else:
        print(f"***Salesforce Failed to send compliance report to the salesforce site. Status code: {response.status_code}")
        print(f"***Salesforce response raw: {response.text}")  # Use response.text instead of response

def send_to_webhook(report, salesforce_id):
    print(f"Webhook report: {report}")

    url = "	https://webhook.site/3f7ba1b7-80ab-44cf-98ef-214df078619a"
    headers = {"Content-Type": "application/json"}
    data = report.dict()
    data["salesforce_id"] = salesforce_id
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Compliance report sent to the test site successfully.")
    else:
        print(f"Failed to send compliance report to the test site. Status code: {response.status_code}")

async def process_compliance_report(request):
    researcher = CustomDetailedReport(
        query=request["query"],
        source_urls=None,
        config_path="",
        directors=request["directors"],
        include_domains=request["include_domains"],
        exclude_domains=request["exclude_domains"],
        parent_sub_queries=request["parent_sub_queries"],
        child_sub_queries=request["child_sub_queries"]
    )
    report = await researcher.run()
    print(f"Compliance report: {report}")
    print(f"Company: {report.company}")
    print(f"Directors: {report.directors}")
    print(f"Source URLs: {report.source_urls}")
    # Send the final response to the Salesforce endpoint
    salesforce_id=request["salesforce_id"],
    send_to_webhook(report, salesforce_id)
    send_to_salesforce(report, salesforce_id)
    

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()