from gpt_researcher.master.agent import GPTResearcher
from fastapi import WebSocket

class BasicReport():
    def __init__(self, query: str, report_type: str, source_urls, config_path: str, websocket: WebSocket):
        self.query = query
        self.report_type = report_type
        self.source_urls = source_urls
        self.config_path = config_path
        self.websocket = websocket
        
    async def run(self):
        # Initialize researcher
        researcher = GPTResearcher(self.query, self.report_type, self.source_urls, self.config_path, self.websocket)
        
        # Run research
        await researcher.conduct_research()
        
        # and generate report        
        report = await researcher.write_report()
        
        return report