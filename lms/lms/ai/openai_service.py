# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

"""Backwards-compatible facade forwarding to the unified AI Provider Service."""

from lms.lms.ai.ai_service import (
	MODEL_PRICING,
	calculate_cost,
	call_ai_service as call_openai_json,
	call_ai_service,
	fallback_offline_engine,
	get_ai_settings,
	get_openai_api_key,
	log_generation,
	test_ai_connection,
)


def get_default_model() -> str:
	cfg = get_ai_settings()
	if cfg.get("provider") == "OpenAI":
		return cfg.get("openai_model") or "gpt-4o-mini"
	return cfg.get("ollama_model") or "llama3.2"
