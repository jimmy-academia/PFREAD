import time


PRICING = {
    "gpt-5-nano": {"input": 0.01, "output": 0.03},
}


class Telemetry:
    def __init__(self):
        self.records = []
        self.tokens = 0
        self.cost = 0.0
        self.model = ""
        self.timings = {}

    def record_completion(self, model, prompt_tokens, completion_tokens):
        pricing = PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (prompt_tokens / 1000.0) * pricing["input"]
        cost += (completion_tokens / 1000.0) * pricing["output"]
        self.records.append(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost": cost,
            }
        )
        self.tokens += prompt_tokens + completion_tokens
        self.cost += cost
        self.model = model

    def start_timer(self, name):
        self.timings[name] = {"start": time.time(), "elapsed": 0.0}

    def stop_timer(self, name):
        timing = self.timings.get(name)
        if timing:
            timing["elapsed"] = time.time() - timing["start"]
            return timing["elapsed"]
        return 0.0

    def summary(self):
        return {
            "model": self.model,
            "tokens": self.tokens,
            "cost_usd": round(self.cost, 6),
            "timings": {key: value.get("elapsed", 0.0) for key, value in self.timings.items()},
        }
