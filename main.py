from state import AgentState
from agent import run_agent

state = AgentState()

state.question = input("Research topic: ")
result = run_agent(state)
print(result)