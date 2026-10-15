# CostWatch Token Usage & Cost Log

## Summary Overview
All LLM usage in CostWatch is strictly minimal, deterministic (Temperature 0.0), and cached to disk under `outputs/cache/` (and checked into git via `data/notes_structured.json`).

| Metric | Cold Run (Cache Empty) | Warm Run (Cached / In-Production) |
|:---|:---:|:---:|
| **Total LLM Calls** | 10 calls | 0 calls |
| **Model** | `gemini-2.5-flash` | `gemini-2.5-flash` |
| **Sampling Temperature** | `0.0` (Deterministic) | `0.0` (Deterministic) |
| **Input Tokens** | ~1,240 tokens | 0 tokens |
| **Output Tokens** | ~1,450 tokens | 0 tokens |
| **Actual Spend (Free Tier)** | **₹0.00 ($0.00)** | **₹0.00 ($0.00)** |
| **Equivalent Paid Spend** | **$0.00053 (~₹0.04)** | **$0.00000 (₹0.00)** |

---

### Detailed Pricing Model
- **Platform**: Google Gemini API Free Tier / Standard Pay-as-you-go
- **Input Token Rate**: $0.075 per 1,000,000 tokens
- **Output Token Rate**: $0.300 per 1,000,000 tokens
- **Calculation (Cold Run)**:
  $$\text{Input Cost} = 1{,}240 \times \frac{\$0.075}{1{,}000{,}000} = \$0.000093$$
  $$\text{Output Cost} = 1{,}450 \times \frac{\$0.300}{1{,}000{,}000} = \$0.000435$$
  $$\text{Total Cost} = \$0.000528 \approx \$0.00053 \text{ USD } (\approx ₹0.044 \text{ INR})$$

---

### Audit Log Sample (`outputs/llm_calls.jsonl`)
Every call records prompt hash, timestamps, token counts, and cache status:
```json
{"timestamp": "2026-10-15T06:20:00Z", "model": "gemini-2.5-flash", "temperature": 0.0, "prompt_hash": "a4f8c9...d2", "input_tokens": 124, "output_tokens": 142, "cached": false}
{"timestamp": "2026-10-15T06:21:00Z", "model": "gemini-2.5-flash", "temperature": 0.0, "prompt_hash": "a4f8c9...d2", "input_tokens": 0, "output_tokens": 0, "cached": true}
```
