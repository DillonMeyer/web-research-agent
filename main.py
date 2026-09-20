import sys

from state import AgentState
from agent import run_agent


def main():
    try:
        state = AgentState()
        state.question = input("Research topic: ")
        print(run_agent(state))
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nResearch cancelled.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
