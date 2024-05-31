#worker.py

import os
import redis
import requests
from rq import Worker, Queue, Connection
from sf_primary_agent import SFComplianceReport
from sf_researcher.salesforce.salesforce_integration import send_to_salesforce

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)



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

async def process_report(request, main_report_type,child_report_type):
    researcher = SFComplianceReport(
        query=request["query"],
        namespace=request["salesforce_id"],
        source_urls=None,
        config_path="",
        contacts=request["contacts"],
        include_domains=request["include_domains"],
        exclude_domains=request["exclude_domains"],
        parent_sub_queries=request["parent_sub_queries"],
        child_sub_queries=request["child_sub_queries"],
        main_report_type=main_report_type,
        child_report_type=child_report_type
    )
    report = await researcher.run()
    print(f"Compliance report: {report}")
    print(f"Company: {report.company}")
    print(f"Contacts: {report.contacts}")
    print(f"Source URLs: {report.source_urls}")
    # Send the final response to the Salesforce endpoint
    salesforce_id=request["salesforce_id"],
    send_to_webhook(report, salesforce_id)
    send_to_salesforce(report, salesforce_id)
    


with Connection(conn):
    worker = Worker(map(Queue, listen))
    worker.work()