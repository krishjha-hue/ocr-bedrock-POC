"""Default prompts for the OCR comparison playground.

Keep these short so iteration is fast. Edit in the UI per-run; the defaults
are just starting points.
"""

DEFAULT_SYSTEM_PROMPT = """You are an expert at reading Indian agricultural input licenses (insecticides, seeds, fertilizers) in English and Hindi, printed or handwritten. Extract only what the document clearly shows. When unsure, return null."""

DEFAULT_USER_PROMPT = """Extract fields from this Indian agri-input license. Return ONE JSON object, no prose, no markdown.

Fields:
- prop_name: proprietor/owner (person). Labels: Proprietor, Licensee, श्री, नाम. Keep honorifics and S/O, D/O, W/O.
- firm_name: business/shop name. Labels: M/s, Firm Name, फर्म का नाम. Usually contains KRISHI, SEVA, KENDRA, AGRO, TRADERS, BEEJ BHANDAR.
- license_number: alphanumeric id like "406/2024" or "FER/MP/2023/1234". Preserve slashes.
- license_type: one of ["insecticides","seeds","fertilizers"]. Infer from the Act cited: Insecticides Act 1968 -> insecticides; Seeds Act 1966 -> seeds; Fertiliser Control Order 1985 -> fertilizers.
- state: full English name. Expand abbreviations (M.P.->Madhya Pradesh, U.P.->Uttar Pradesh, Raj.->Rajasthan). Infer from state seal or department header if not explicit.
- expiry_date: "YYYY-MM-DD". Use explicit expiry if printed. Else, ONLY if document states validity period AND issue date, compute issue_date + N years. Else null. Never default.

Rules:
- If illegible or missing, use null. Do not guess.
- Transcribe handwriting exactly, no corrections.
- confidence (0-1): 1.0 clean printed, 0.8 clean handwritten, 0.6 smudged, 0.3 inferred, 0 missing. Output the mean.
- needs_manual_review=true if confidence<0.7 or any of prop_name/firm_name/license_number/state is null.
- reasons: short comma-separated notes on what was unclear. Empty if clean.

Output schema (exact keys):
{"prop_name":null,"firm_name":null,"license_number":null,"license_type":null,"state":null,"expiry_date":null,"confidence":0,"needs_manual_review":true,"reasons":""}
"""
