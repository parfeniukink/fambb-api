from pydantic_ai import Agent, TextOutput

from .value_objects import TransactionsFilter

agent_to_extract_transactions_filter = Agent(
    "openai:gpt-4o",
    output_type=TransactionsFilter,
    system_prompt=(
        "Deeply analyze User's prompt and try to extract filters according to "
        "the output structure. Make sure that all limitations and riscs are "
        "handled according to the structure's description."
    ),
)
