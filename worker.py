import os
import redis
from rq import Worker, Queue, Connection
from backend.report_type.custom_detailed_report.custom_detailed_report import CustomDetailedReport

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

import requests

def send_to_salesforce(report, salesforce_id):
    url = "https://webhook.site/3f7ba1b7-80ab-44cf-98ef-214df078619a"
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
    # Send the final response to the Salesforce endpoint
    salesforce_id=request["salesforce_id"],
    send_to_salesforce(report, salesforce_id)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()