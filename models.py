"""Registry of Bedrock vision models available in the playground.

All models are invoked through the Converse API. Model IDs here are valid for
Mumbai (ap-south-1). If you change regions, check available profiles with:

    aws bedrock list-inference-profiles --region <region>

Two groups:
  DEFAULT_MODELS   : the curated 4 for side-by-side comparison.
  ADDITIONAL_MODELS: extras worth trying for deeper benchmarking.

The UI shows both groups, visually separated.

To add a model: append a ModelEntry and enable model access in the Bedrock
console for that model in your region.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEntry:
    id: str           # Bedrock model id or inference profile id
    label: str        # what to show in the UI
    provider: str     # grouping in UI
    group: str        # "default" or "additional"
    notes: str = ""


# ---------------------------------------------------------------------------
# DEFAULT SET — the four we recommend starting with. Mix of Anthropic (best
# accuracy on Devanagari), Amazon (cost-effective), and Mistral (alternative
# provider for benchmarking).
# ---------------------------------------------------------------------------
DEFAULT_MODELS: list[ModelEntry] = [
    ModelEntry(
        id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        label="Claude Sonnet 4.5",
        provider="Anthropic",
        group="default",
        notes="Top pick. Strongest on Devanagari + handwriting at balanced cost.",
    ),
    ModelEntry(
        id="apac.amazon.nova-pro-v1:0",
        label="Amazon Nova Pro",
        provider="Amazon",
        group="default",
        notes="AWS-native multimodal. Decent on printed Hindi, fast.",
    ),
    ModelEntry(
        id="global.amazon.nova-2-lite-v1:0",
        label="Amazon Nova 2 Lite",
        provider="Amazon",
        group="default",
        notes="Next-gen Nova Lite. Newer architecture, improved over v1.",
    ),
    ModelEntry(
        id="mistral.mistral-large-3-675b-instruct",
        label="Mistral Large 3 (675B)",
        provider="Mistral",
        group="default",
        notes="Mistral's largest multimodal model. Strong on Latin; test for Hindi.",
    ),
]


# ---------------------------------------------------------------------------
# ADDITIONAL SET — vision models available in Mumbai that can be useful for
# Hindi content to varying degrees. Enable model access before selecting.
# ---------------------------------------------------------------------------
ADDITIONAL_MODELS: list[ModelEntry] = [
    ModelEntry(
        id="global.anthropic.claude-opus-4-5-20251101-v1:0",
        label="Claude Opus 4.5",
        provider="Anthropic",
        group="additional",
        notes="Highest Claude accuracy. Use when Sonnet 4.5 still misses fields.",
    ),
    ModelEntry(
        id="global.anthropic.claude-opus-4-7",
        label="Claude Opus 4.7",
        provider="Anthropic",
        group="additional",
        notes="Newest Opus. Top end of the accuracy spectrum.",
    ),
    ModelEntry(
        id="global.anthropic.claude-sonnet-4-6",
        label="Claude Sonnet 4.6",
        provider="Anthropic",
        group="additional",
        notes="Newer Sonnet iteration. Test head-to-head vs 4.5.",
    ),
    ModelEntry(
        id="global.anthropic.claude-haiku-4-5-20251001-v1:0",
        label="Claude Haiku 4.5",
        provider="Anthropic",
        group="additional",
        notes="Fast and cheap Claude. Fair on printed Hindi; weaker on handwriting.",
    ),
    ModelEntry(
        id="qwen.qwen3-vl-235b-a22b",
        label="Qwen3-VL 235B",
        provider="Alibaba",
        group="additional",
        notes="Large multilingual vision model. Strong on Indic benchmarks.",
    ),
    ModelEntry(
        id="moonshotai.kimi-k2.5",
        label="Moonshot Kimi K2.5",
        provider="Moonshot",
        group="additional",
        notes="Strong multilingual model. Mixed signals on Devanagari.",
    ),
    ModelEntry(
        id="google.gemma-3-27b-it",
        label="Gemma 3 27B",
        provider="Google",
        group="additional",
        notes="Google open-weights. Reasonable on printed Hindi, weak on handwriting.",
    ),
]


# Combined list (used by the UI and run endpoint)
MODELS: list[ModelEntry] = DEFAULT_MODELS + ADDITIONAL_MODELS


def get_model(model_id: str) -> ModelEntry | None:
    for m in MODELS:
        if m.id == model_id:
            return m
    return None
