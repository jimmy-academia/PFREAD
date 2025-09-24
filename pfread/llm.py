import json
import time

from pfread.utils.telemetry import Telemetry


class LLMClient:
    def __init__(self, model="gpt-5-nano", temperature=0.0, max_retries=2, fake=False, telemetry=None):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.fake = fake
        self.telemetry = telemetry or Telemetry()

    def complete_json(self, system, user, model=None, temperature=None, max_tokens=256):
        current_model = model or self.model
        current_temperature = temperature if temperature is not None else self.temperature
        attempts = 0
        last_error = None
        while attempts <= self.max_retries:
            try:
                if not self.fake:
                    raise RuntimeError("Real LLM mode is not configured")
                response = self._fake_response(system, user, current_model, current_temperature, max_tokens)
                payload = json.loads(json.dumps(response))
                prompt_tokens = len(user.split())
                completion_tokens = len(json.dumps(payload).split())
                self.telemetry.record_completion(current_model, prompt_tokens, completion_tokens)
                return payload
            except Exception as error:  # noqa: BLE001
                last_error = error
                time.sleep(0.05 * (2 ** attempts))
                attempts += 1
        raise RuntimeError(f"LLM request failed: {last_error}")

    def _fake_response(self, system, user, model, temperature, max_tokens):
        data = json.loads(user)
        task = data.get("task")
        if task == "proofread_sentence":
            return self._fake_sentence(data)
        if task == "cross_check_ambiguity":
            return {"status": "ok"}
        if task == "paragraph_diagnose":
            return self._fake_paragraph(data)
        if task == "paper_review":
            return self._fake_review(data)
        return {}

    def _fake_sentence(self, data):
        sentence = data.get("sentence", "")
        if "teh" in sentence:
            suggestion = sentence.replace("teh", "the")
            return {
                "status": "edit",
                "original": sentence,
                "suggestion": suggestion,
                "types": ["spelling"],
                "explanation": "Corrected spelling.",
            }
        if " alot" in sentence:
            suggestion = sentence.replace(" alot", " a lot")
            return {
                "status": "edit",
                "original": sentence,
                "suggestion": suggestion,
                "types": ["spelling"],
                "explanation": "Split common misspelling.",
            }
        return {"status": "ok"}

    def _fake_paragraph(self, data):
        paragraph = data.get("paragraph", "")
        issues = []
        if "maybe" in paragraph or "perhaps" in paragraph:
            span_start = paragraph.find("maybe")
            if span_start == -1:
                span_start = paragraph.find("perhaps")
            issues.append(
                {
                    "type": "hedging",
                    "severity": "minor",
                    "span": {"start": span_start, "end": span_start + 6},
                    "suggestion": "State the claim directly.",
                    "explanation": "Remove hedging for clarity.",
                }
            )
        sentences = [segment.strip() for segment in paragraph.split(".") if segment.strip()]
        for segment in sentences:
            if len(segment.split()) > 25:
                position = paragraph.find(segment)
                issues.append(
                    {
                        "type": "long_sentence",
                        "severity": "moderate",
                        "span": {"start": position, "end": position + len(segment)},
                        "suggestion": "Split into two sentences.",
                        "explanation": "Sentence is lengthy.",
                    }
                )
                break
        if "very very" in paragraph:
            position = paragraph.find("very very")
            issues.append(
                {
                    "type": "redundancy",
                    "severity": "minor",
                    "span": {"start": position, "end": position + 9},
                    "suggestion": "Remove repetition.",
                    "explanation": "Repeated intensifier.",
                }
            )
        return issues

    def _fake_review(self, data):
        skeleton = data.get("skeleton", "")
        sections = []
        for line in skeleton.splitlines():
            line = line.strip()
            if line.startswith("Section:"):
                sections.append(line.split(":", 1)[1].strip())
        return {
            "summary": "Concise overview of the paper.",
            "strengths": ["Clear structure"],
            "weaknesses": ["Needs deeper evaluation"],
            "top_fixes": [
                {
                    "section": sections[0] if sections else "Introduction",
                    "action": "Clarify main contribution",
                    "impact": "high",
                }
            ],
            "missing_refs": [],
        }
