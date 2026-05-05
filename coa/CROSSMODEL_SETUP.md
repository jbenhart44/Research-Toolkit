# Cross-Model Verification Setup for /coa (Optional but Recommended)

`/coa` runs a council of Claude-backed council members. By default, every member runs on the same model family (Claude), so when they agree, you get **breadth-of-framing** validation — but not **independent-model** confirmation. Adding a single Gemini cross-check at session time turns that same-model caveat into a genuinely cross-vendor signal.

This guide walks a new toolkit user through the cheapest path: Google's free Gemini API tier.

---

## Why bother

A 2026-05-01 /coa session classified a real Anthropic Claude Code feature (`.claude/rules/*.md` with `paths:` glob frontmatter) as `FABRICATED` with HIGH conviction across 3 Claude council members + a same-family Sonnet fallback. The feature was fully documented; the council had simply never seen it. Training-data absence is not feature absence — and same-model councils confidently reject things they don't recognize. A different vendor's model with different training data catches exactly this failure mode.

Cost of adding the cross-check: one free API key, two minutes, no credit card.

---

## Step 1 — Get a free Gemini API key

1. **Visit Google AI Studio** — <https://aistudio.google.com>
2. **Sign in** with a standard Google account.
3. **Accept the Generative AI Terms of Service** (first time only).
4. **Generate the key**:
   - Click **"Get API key"** in the left sidebar.
   - Click **"Create API key in new project"** (or pick an existing Google Cloud project if you have one).
   - Copy the generated key.
5. **Store the key as an environment variable** named `GEMINI_API_KEY` (this is the variable name `/coa` looks for):

   ```bash
   export GEMINI_API_KEY="your_key_here"
   echo 'export GEMINI_API_KEY="your_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

That's it for Gemini side. The key is now in your shell.

---

## Free-tier limits (good enough for /coa use)

| Model | Requests / min | Requests / day | Context window |
|---|---|---|---|
| `gemini-2.5-flash` (current default) | ~10 | ~250 | 1M+ tokens |

A typical `/coa` session uses 1–2 cross-model calls. Free-tier limits are well above that unless you're running councils all day.

**Privacy note**: Google may use de-identified inputs and outputs to improve their models on the free tier. For typical /coa questions (strategic decisions, public research) this is fine. If you're sending proprietary content, upgrade to pay-as-you-go (data stays private there).

---

## Step 2 — Register the cross-model MCP server

The toolkit invokes Gemini through an MCP server (`mcp__crossmodel__query_model`). A reference implementation is bundled at `coa/crossmodel-mcp/server.py` (zero dependencies, pure Python stdlib, ~290 lines). It supports Gemini, OpenAI, and Perplexity, and prefixes every response with `[META: finish_reason=<value>]` so the /coa skill can detect and diagnose truncation.

Register it with Claude Code:

```bash
# From the directory where you cloned the toolkit:
TOOLKIT_DIR="$(pwd)"
claude mcp add crossmodel \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -- python3 "$TOOLKIT_DIR/coa/crossmodel-mcp/server.py"
```

**IMPORTANT**: After `claude mcp add`, you must **`/exit` and relaunch Claude Code** for the new MCP registration to load. MCP servers register at session start.

If you have multiple API keys set, pass them all to one registration so the /coa skill can cascade between providers when one truncates or rate-limits:

```bash
claude mcp add crossmodel \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY" \
  -- python3 "$TOOLKIT_DIR/coa/crossmodel-mcp/server.py"
```

---

## Step 3 — Verify it works

In a fresh Claude Code session (post-restart):

```
mcp__crossmodel__list_available_models
```

Expected output:

```
- gemini: READY (env: GEMINI_API_KEY)
- openai: NOT CONFIGURED (env: OPENAI_API_KEY)
- perplexity: NOT CONFIGURED (env: PERPLEXITY_API_KEY)
```

Smoke test (single 1-word query — should return a `[META: finish_reason=STOP]` prefix and one word of response):

```
mcp__crossmodel__query_model(
  model="gemini",
  system_prompt="You are a 1-word answerer.",
  user_prompt="Say hello in one word."
)
```

If you see the `[META: ...]` prefix and a clean 1-word response, you're set. The next `/coa` run will automatically include a Gemini cross-check.

---

## Without the MCP server

If you skip MCP setup entirely, /coa still runs — it just operates as a same-model council (no cross-vendor signal). The skill explicitly handles this case: cross-model checks are skipped, the same-model caveat is noted in the Chair synthesis, and no errors are thrown. This is a fully supported degraded mode; you only lose the cross-vendor disagreement signal.

---

## Optional: OpenAI and Perplexity

The same MCP server supports OpenAI (`OPENAI_API_KEY`, requires billing) and Perplexity (`PERPLEXITY_API_KEY`, free tier available). The skill cascades through configured models if Gemini truncates or rate-limits:

```bash
export OPENAI_API_KEY="..."        # https://platform.openai.com/api-keys
export PERPLEXITY_API_KEY="..."    # https://www.perplexity.ai/settings/api
```

Re-register the MCP after adding new keys (`claude mcp remove crossmodel; claude mcp add crossmodel -e ... -- python3 ...`) and restart.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `gemini: NOT CONFIGURED` | Env var not visible to the MCP server | Re-export `GEMINI_API_KEY` and restart Claude Code |
| HTTP 429 | Free-tier daily quota exhausted | Wait for daily reset, or upgrade to paid tier |
| HTTP 401 | Invalid key | Re-check key from <https://aistudio.google.com/apikey> |
| Response truncated mid-sentence | Gemini's `maxOutputTokens` cap was hit (default 2048 in reference server.py) | Bump to 8192 in `call_gemini()` config and restart |
| `[META: finish_reason=SAFETY]` | Gemini safety filter blocked output | Rephrase the prompt, or route the seat to OpenAI/Perplexity |
| No `[META]` prefix in response | Server.py edits not loaded | Restart Claude Code so the MCP server re-reads the file |

---

## Reference

- Gemini API console: <https://aistudio.google.com>
- /coa command source: `shared/commands/coa.md` (in this toolkit)
- MCP server source: `coa/crossmodel-mcp/server.py` (in this toolkit)
