from dataclasses import dataclass, field

MODEL_PRICING_PER_MTOK = {
    "openai/gpt-5.6-luna": {"input": 0.20, "output": 1.20},
    "openai/gpt-5.6-terra": {"input": 2.00, "output": 12.00},
    "openai/gpt-5.6-sol": {"input": 5.00, "output": 30.00},
    "openai/text-embedding-3-small": {"input": 0.02, "output": 0.0},
}


@dataclass
class CostTracker:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_usd: float = 0.0
    by_model: dict = field(default_factory=dict)

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        pricing = MODEL_PRICING_PER_MTOK.get(model)
        cost = 0.0
        if pricing:
            cost = (input_tokens / 1_000_000) * pricing["input"]
            cost += (output_tokens / 1_000_000) * pricing["output"]

        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_usd += cost

        entry = self.by_model.setdefault(
            model, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "usd": 0.0}
        )
        entry["calls"] += 1
        entry["input_tokens"] += input_tokens
        entry["output_tokens"] += output_tokens
        entry["usd"] += cost

    def record_response(self, model: str, response) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        input_tokens = getattr(usage, "input_tokens", None) or getattr(
            usage, "prompt_tokens", 0
        )
        output_tokens = getattr(usage, "output_tokens", None) or getattr(
            usage, "completion_tokens", 0
        )
        self.record(model, input_tokens, output_tokens)

    def summary(self) -> dict:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "usd": round(self.total_usd, 4),
        }
