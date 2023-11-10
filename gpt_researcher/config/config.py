# config file

class Config:
    def __init__(self):
        self.retriver = "tavily"
        self.llm_provider = "ChatOpenAI"
        self.fast_llm_model = "gpt-3.5-turbo-16k"
        self.smart_llm_model = "gpt-4"
        self.fast_token_limit = 2000
        self.smart_token_limit = 4000
        self.browse_chunk_max_length = 8192
        self.summary_token_limit = 700
        self.temperature = 1.0
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) " \
                            "Chrome/83.0.4103.97 Safari/537.36 "
        self.memory_backend = "local"



