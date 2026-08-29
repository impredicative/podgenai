from pathlib import Path

from podgenai.util.openai import MODELS
from podgenai.util.tiktoken import get_token_count

model = MODELS["knowledge"]["name"]

costs = {  # Cost in USD per million input tokens.
    "gpt-5.6-sol": 4,  # Ref: https://developers.openai.com/api/docs/models/gpt-5.6-sol
}
model_cost = costs[model]

sources = list(Path("sources/").glob("*.md"))
for source in sources:
    content = source.read_text()
    num_tokens = get_token_count(content, model=model)
    cost = num_tokens * model_cost / 1_000_000
    print(f"{source.name}: tokens={num_tokens:,} cost=${cost:.2f}")
