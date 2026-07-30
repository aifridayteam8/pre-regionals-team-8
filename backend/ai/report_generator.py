from typing import Dict, List, Optional
import json
import re
import logging
from datetime import datetime
from backend.config import Config

logger = logging.getLogger(__name__)

REPORT_FIELDS = [
    'executive_summary',
    'incident_overview',
    'timeline',
    'root_cause_analysis',
    'impact_assessment',
    'systems_affected',
    'resolution_steps',
    'recommendations',
    'preventive_actions',
    'lessons_learned',
]

# Calibrated against local hardware (~7.5 tok/s generation, ~25 tok/s prompt
# eval on a 3B model, CPU-only): a single combined call with a trimmed prompt
# and this output cap targets well under 2 minutes with margin, versus the
# previous design of 10 separate sequential calls (~30 minutes total).
MAX_REPORT_TOKENS = 380
GENERATION_TEMPERATURE = 0.3


class ReportGenerator:
    """Generate AI-powered incident reports."""

    # Prompt-size knobs: prompt-eval time scales with token count on this
    # (CPU-only) hardware almost as much as generation does, so trimming
    # context is as important as capping output for hitting a time budget.
    MAX_CONTEXT_EVENTS = 8
    MAX_EVENT_MESSAGE_CHARS = 80

    def __init__(self, config: Config):
        self.config = config
        self.client = self._get_client()

    def _get_client(self):
        """Get appropriate AI client based on configuration."""
        if self.config.USE_OPENAI and self.config.OPENAI_API_KEY:
            from .openai_client import OpenAIClient
            return OpenAIClient(self.config.OPENAI_API_KEY, self.config.OPENAI_MODEL)
        else:
            from .ollama_client import OllamaClient
            return OllamaClient(self.config.OLLAMA_BASE_URL, self.config.OLLAMA_MODEL)

    def generate_report(self, incident_data: Dict, events: List[Dict]) -> Dict:
        """Generate complete incident report with a single bounded LLM call."""
        start_time = datetime.now()

        try:
            context = self._prepare_context(incident_data, events)
            prompt = self._build_prompt(context)

            raw_response = self.client.generate(
                prompt,
                system_prompt=(
                    "You are an expert Site Reliability Engineer writing concise incident "
                    "reports. Respond with ONLY a single valid JSON object - no markdown "
                    "fences, no commentary before or after it."
                ),
                max_tokens=MAX_REPORT_TOKENS,
                temperature=GENERATION_TEMPERATURE,
            )

            sections = self._parse_sections(raw_response)

            report = {
                **sections,
                'ai_model_used': self._get_model_name(),
                'confidence_score': self._calculate_confidence_score(events, sections),
            }

            generation_time = (datetime.now() - start_time).total_seconds()
            report['generation_time'] = generation_time

            logger.info(f"Report generated in {generation_time:.2f} seconds")
            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def _prepare_context(self, incident_data: Dict, events: List[Dict]) -> str:
        """Prepare a compact context for AI generation."""
        context = (
            f"Incident: {incident_data.get('title', 'Unknown')} | "
            f"Severity: {incident_data.get('severity', 'Unknown')} | "
            f"Type: {incident_data.get('incident_type', 'Unknown')}\n"
            f"{len(events)} events total "
            f"({len([e for e in events if e.get('level') in ['error', 'critical']])} error/critical, "
            f"{len([e for e in events if e.get('level') == 'warning'])} warning)\n"
            "Key events:\n"
        )

        for event in events[:self.MAX_CONTEXT_EVENTS]:
            message = " ".join(str(event.get('message') or 'No message').split())[:self.MAX_EVENT_MESSAGE_CHARS]
            context += f"- [{event.get('timestamp', '?')}] {(event.get('level') or 'info').upper()}: {message}\n"

        return context

    def _build_prompt(self, context: str) -> str:
        """Build a single, compact prompt asking for every report section as bounded JSON."""
        return f"""{context}
Return ONLY a compact single-line JSON object (no pretty-printing, no markdown) with these keys, each value brief:
executive_summary (1-2 sentences), incident_overview (1-2 sentences), timeline (max 5 "- " bullets joined by \\n),
root_cause_analysis (1-2 sentences), impact_assessment (1-2 sentences), systems_affected (comma-separated list),
resolution_steps (max 3 "- " bullets joined by \\n), recommendations (max 3 "- " bullets joined by \\n),
preventive_actions (max 3 "- " bullets joined by \\n), lessons_learned (1-2 sentences).
Total response under 300 words."""

    def _parse_sections(self, raw_response: str) -> Dict[str, str]:
        """Parse the model's JSON response into report fields, tolerating minor formatting issues."""
        json_block = self._extract_json_block(raw_response)

        parsed = {}
        if json_block:
            try:
                parsed = json.loads(json_block)
            except json.JSONDecodeError:
                logger.warning("Report JSON failed to parse cleanly; falling back to per-field regex extraction")
                parsed = self._extract_fields_by_regex(json_block)

        sections = {}
        for field in REPORT_FIELDS:
            value = parsed.get(field) if isinstance(parsed, dict) else None
            if isinstance(value, list):
                value = "\n".join(f"- {item}" for item in value)
            sections[field] = (value or "").strip() if isinstance(value, str) else ""

        if not any(sections.values()):
            # Total parse failure: surface the raw model output rather than an empty report.
            logger.warning("Could not extract any report fields from model output; using raw text as summary")
            sections['executive_summary'] = raw_response.strip()[:2000]

        return sections

    @staticmethod
    def _extract_json_block(text: str) -> Optional[str]:
        """Pull the first balanced {...} block out of the model's response."""
        text = text.strip()
        # Strip ```json ... ``` or ``` ... ``` fences if present
        fence_match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        start = text.find('{')
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        # Unbalanced (likely truncated by max_tokens) - return what we have
        return text[start:]

    @staticmethod
    def _extract_fields_by_regex(json_block: str) -> Dict[str, str]:
        """Best-effort field extraction when the JSON is malformed/truncated."""
        fields = {}
        for field in REPORT_FIELDS:
            match = re.search(
                rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"',
                json_block,
                re.DOTALL,
            )
            if match:
                value = match.group(1)
                value = value.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                fields[field] = value
        return fields

    def _get_model_name(self) -> str:
        """Get the name of the AI model being used."""
        if self.config.USE_OPENAI:
            return f"OpenAI {self.config.OPENAI_MODEL}"
        else:
            return f"Ollama {self.config.OLLAMA_MODEL}"

    def _calculate_confidence_score(self, events: List[Dict], sections: Dict[str, str]) -> float:
        """Calculate confidence score from event volume and how many sections were filled."""
        filled = sum(1 for v in sections.values() if v)
        base = 0.5 + (filled / len(REPORT_FIELDS)) * 0.3
        event_bonus = min(len(events) * 0.005, 0.15)
        return round(min(base + event_bonus, 0.95), 2)
