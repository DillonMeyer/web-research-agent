from state import AgentState
from decisions import get_next_action
from tools import search_web, fetch_page

MAX_STEPS = 20

def run_agent(state: AgentState):

    while state.steps < MAX_STEPS:

        decision = get_next_action(state)

        if decision["action"] == "finish":
            return decision["answer"]

        try:
            if decision["action"] == "search":
                result = search_web(decision["query"])
                state.search_results.extend(result)
            elif decision["action"] == "fetch":
                result = fetch_page(decision["url"])
                state.sources.append({"url": decision["url"], **result})
        except RuntimeError as exc:
            # Let the model choose another query/page when a web request fails.
            result = {"error": str(exc)}

        state.messages.append({"decision": decision, "result": result})
        state.steps += 1

    return "Research stopped: the step limit was reached before a final brief was produced."
