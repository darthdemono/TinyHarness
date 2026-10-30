"""Problem 1: explain an official letter in plain language using only a local folder of rules.

    python examples/letter_explainer.py letter.txt ./rules
"""
import sys

from tinyharness.agent import Agent
from tinyharness.client import Client
from tinyharness.tools import folder_tools

SYSTEM = (
    "You explain official letters in plain language. Search the rules folder before answering, "
    "say what the letter asks, by when, and what happens if ignored. If the rules do not cover it, say so."
)


def explain(letter_path, rules_dir, client=None):
    agent = Agent(client or Client(), system=SYSTEM)
    agent.add_tools(folder_tools(rules_dir))
    with open(letter_path, encoding="utf-8") as f:
        return agent.run("Explain this letter:\n\n" + f.read())


if __name__ == "__main__":
    print(explain(sys.argv[1], sys.argv[2]))
