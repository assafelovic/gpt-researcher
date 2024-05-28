#worker.py

import os
import redis
import time
import requests
from rq import Worker, Queue, Connection
from sf_primary_agent import SFPrimaryAgent

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

def refresh_salesforce_token():
    url = "https://login.salesforce.com/services/oauth2/token?grant_type=password&client_id={}&client_secret={}&username={}&password={}".format(
        os.getenv('SALESFORCE_CLIENT_ID'),
        os.getenv('SALESFORCE_CLIENT_SECRET'),
        os.getenv('SALESFORCE_USERNAME'),
        os.getenv('SALESFORCE_PASSWORD')
    )
    headers = {
        'Authorization': 'Bearer 00DQy00000770H2!AQEAQC7f6uBPuNFd9dUOc2icQGMycxxDa_DNaLwGozxXf9wFAd1cMFhzu1G7G2nNnjp5cePLiGNWYQclmxRBJ1pB101WMrxX',
        'Cookie': 'BrowserId=Cw4X-1zQEe6mwN_5Z-AtVA; CookieConsentPolicy=0:0; LSKey-c$CookieConsentPolicy=0:0'
    }
    response = requests.post(url, headers=headers)
    
    print(f"Salesforce token refresh response - Status Code: {response.status_code}")
    print(f"Salesforce token refresh response - Content: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        token_expiration = time.time() + 3600  # Assuming token is valid for 1 hour
        redis_url = os.getenv('REDIS_URL')
        redis_client = redis.from_url(redis_url)
        redis_client.set('SALESFORCE_ACCESS_TOKEN', access_token)
        redis_client.set('SALESFORCE_TOKEN_EXPIRATION', token_expiration)
        return access_token
    else:
        raise Exception(f"Failed to refresh Salesforce token. Status code: {response.status_code}")

def send_to_salesforce(report, salesforce_id):
    print(f"Salesforce report: {report}")
    url = "https://fundpath-dev-ed.develop.my.salesforce.com/services/apexrest/compliance_report_response"
    
    redis_url = os.getenv('REDIS_URL')
    redis_client = redis.from_url(redis_url)
    token_expiration = float(redis_client.get('SALESFORCE_TOKEN_EXPIRATION') or 0)
    
    if time.time() >= token_expiration:
        access_token = refresh_salesforce_token()
    else:
        access_token = redis_client.get('SALESFORCE_ACCESS_TOKEN').decode('utf-8')
    
    print("access_token: ",access_token)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cookie": "BrowserId=Cw4X-1zQEe6mwN_5Z-AtVA; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1"
    }
    
    data = report.dict()
    data["salesforce_id"] = [salesforce_id]  # Wrap salesforce_id in a list
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Compliance report sent to the salesforce site successfully.")
    else:
        print(f"***Salesforce Failed to send compliance report to the salesforce site. Status code: {response.status_code}")
        print(f"***Salesforce response raw: {response.text}")


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
    researcher = SFPrimaryAgent(
        query=request["query"],
        namespace=request["salesforce_id"],
        source_urls=None,
        config_path="",
        directors=request["directors"],
        include_domains=request["include_domains"],
        exclude_domains=request["exclude_domains"],
        parent_sub_queries=request["parent_sub_queries"],
        child_sub_queries=request["child_sub_queries"],
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
    


with Connection(conn):
    worker = Worker(map(Queue, listen))
    worker.work()