# Models Guide

Why these models, and how to change them.

## Groups

The UI shows two groups:

- **Recommended for Hindi OCR** — the curated 4 we suggest starting with
- **Additional models** (collapsed by default) — other vision models available in Mumbai that can be useful for Hindi content

Both are defined in `models.py` as `DEFAULT_MODELS` and `ADDITIONAL_MODELS`. Move entries between lists or uncomment to change what shows up.

## Recommended set (four models, mixed providers)

| Model | Strength | Cost | When to use |
|---|---|---|---|
| **Claude Sonnet 4.5** | Best overall on Devanagari + handwriting | Medium | Default for any serious run |
| **Amazon Nova Pro** | AWS-native, fast, good on printed Hindi | Low-medium | Cheap AWS baseline |
| **Amazon Nova 2 Lite** | Next-gen Nova Lite architecture | Very low | Cost floor reference with improved accuracy vs v1 |
| **Mistral Large 3 (675B)** | Largest Mistral multimodal | Medium | Alternative provider benchmark |

Running all four on one image is typically a fraction of a US cent.

## Additional set

These are vision-capable models in Mumbai that are worth trying if the recommended set doesn't meet your accuracy bar:

- **Claude Opus 4.5** — highest Claude accuracy, use when Sonnet 4.5 still misses
- **Claude Opus 4.7** — newest Opus iteration
- **Claude Sonnet 4.6** — newer Sonnet, test head-to-head with 4.5
- **Claude Haiku 4.5** — fast, cheap Claude for printed text
- **Qwen3-VL 235B** — strong multilingual non-Anthropic option
- **Moonshot Kimi K2.5** — strong multilingual, mixed signals on Devanagari
- **Google Gemma 3 27B** — open-weights, reasonable on printed Hindi

## Why these weren't chosen

Quick notes on models available in Mumbai that are *not* in this playground:

- **Mistral Large / Ministral** — Latin-script focused, weak Hindi
- **NVIDIA Nemotron Nano** — text-focused benchmarks, not a top Hindi pick
- **Gemma 3 4B / 12B** — smaller Gemmas underperform the 27B; picked the best one

Add any of these to `models.py` if you want to benchmark.

## Inference profile prefixes

Bedrock model IDs come in three forms. Which one you use depends on the region.

| Prefix | Meaning | Example |
|---|---|---|
| `global.*` | Cross-region inference profile, routed globally | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `apac.*`, `us.*`, `eu.*` | Region-group profile (APAC includes Mumbai) | `apac.amazon.nova-pro-v1:0` |
| no prefix | Direct foundation model, region-local only | `qwen.qwen3-vl-235b-a22b` |

If you change regions, check `aws bedrock list-inference-profiles --region <region>` and adjust.

## List what's actually available to you

```bash
# All image-capable foundation models in your region
aws bedrock list-foundation-models --region ap-south-1 \
  --query 'modelSummaries[?contains(inputModalities, `IMAGE`)].[modelId,modelName]' \
  --output table

# All inference profiles (cross-region served) in your region
aws bedrock list-inference-profiles --region ap-south-1 \
  --query 'inferenceProfileSummaries[].[inferenceProfileId,inferenceProfileName,status]' \
  --output table
```

## Swapping or adding models

Open `models.py` and add or edit entries in `DEFAULT_MODELS` or `ADDITIONAL_MODELS`:

```python
ModelEntry(
    id="global.anthropic.claude-opus-4-7",
    label="Claude Opus 4.7",
    provider="Anthropic",
    group="additional",         # or "default"
    notes="Newest Opus iteration.",
),
```

Save — uvicorn auto-reloads — then refresh the browser.

## Switching regions

To run in a different region, set `AWS_REGION` and verify:

1. Your credentials work there (`aws sts get-caller-identity` should still work)
2. Model access is granted in that region (Bedrock console → Model access)
3. The inference profile prefixes in `models.py` match that region:
   - `ap-south-1` (Mumbai) → `apac.*` or `global.*`
   - `us-east-1` / `us-west-2` → `us.*` or `global.*`
   - `eu-west-1` / `eu-central-1` → `eu.*` or `global.*`

## Reading the outputs

For each model run you get:

- **Parsed JSON**: best-effort extraction of the first JSON object from the model's response
- **Raw output**: everything the model returned, untouched. Check this when parsed JSON is empty
- **Latency**: end-to-end time including network
- **Tokens in / out**: useful for cost estimation

The **Field agreement** panel (shown when 2+ models return valid JSON) colors each field:

- **Green**: all models agree on the value
- **Yellow**: models disagree — the field needs manual review
- **Grey / italic**: one or more models returned null

Use yellow cells as your "focus areas" when iterating on the prompt.
