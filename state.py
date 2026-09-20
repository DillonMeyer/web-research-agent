class AgentState:
    def __init__(self):
        self.question: str = ""
        self.messages: list = []
        self.search_results: list = []
        self.sources: list = []
        self.steps: int = 0
