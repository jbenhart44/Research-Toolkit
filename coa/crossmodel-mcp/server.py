#!/usr/bin/env python3
"""
Cross-Model MCP Server for Council of Agents (CoA)

Routes prompts to external LLM APIs (Gemini, OpenAI, Perplexity).
Used by the /coa Clerk to give council seats access to non-Claude models.

Usage:
  1. Set API keys as environment variables:
     export GEMINI_API_KEY=your_key
     export OPENAI_API_KEY=your_key
     export PERPLEXITY_API_KEY=your_key
  2. Register via: claude mcp add crossmodel -- python3 /home/jbenhart/crossmodel-mcp/server.py
  3. The Clerk calls: mcp__crossmodel__query_model(model, system_prompt, user_prompt)
"""

import json
import os
import sys
import urllib.request
import urllib.error

# MCP protocol implementation (stdio transport, minimal)
def read_message():
    """Read a JSON-RPC message from stdin."""
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)

def write_message(msg):
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Call Google Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "ERROR: GEMINI_API_KEY not set. Run: export GEMINI_API_KEY=your_key"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.7}
    }
    return _post_json(
        url, payload,
        extract_path=["candidates", 0, "content", "parts", 0, "text"],
        meta_path=["candidates", 0, "finishReason"],
    )

def call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI API (GPT-4o-mini default)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "ERROR: OPENAI_API_KEY not set. Run: export OPENAI_API_KEY=your_key"

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.7
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    return _post_json(
        url, payload, headers=headers,
        extract_path=["choices", 0, "message", "content"],
        meta_path=["choices", 0, "finish_reason"],
    )

def call_perplexity(system_prompt: str, user_prompt: str) -> str:
    """Call Perplexity API (sonar model)."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return "ERROR: PERPLEXITY_API_KEY not set. Run: export PERPLEXITY_API_KEY=your_key"

    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.7
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    return _post_json(
        url, payload, headers=headers,
        extract_path=["choices", 0, "message", "content"],
        meta_path=["choices", 0, "finish_reason"],
    )

def _navigate(obj, path):
    """Walk an object via a path of keys/indices; return None on any miss."""
    cur = obj
    try:
        for key in path:
            cur = cur[key]
        return cur
    except (KeyError, IndexError, TypeError):
        return None


def _post_json(url: str, payload: dict, headers: dict = None, extract_path: list = None,
               meta_path: list = None) -> str:
    """POST JSON to a URL and extract the response text.

    If meta_path is provided, also extracts the finish_reason (or equivalent
    truncation indicator) and prepends it to the returned text as a single
    [META: finish_reason=<value>] line followed by a blank line. This is
    backwards-compatible: callers that don't parse the [META] prefix simply
    see it as part of the text. The Clerk's crossmodel-logging template
    uses this to capture finish_reason in CC_Workflow/evidence/crossmodel_attempts.csv.

    Added 2026-05-05 (queued for next-restart activation) to enable the
    "symptom-vs-cause" diagnosis on Gemini truncation: if finish_reason
    consistently shows MAX_TOKENS, raising maxOutputTokens is the right fix;
    if it shows STOP with truncated text, the cause is upstream (thinking-
    token budget on Flash 2.5, or response-streaming truncation in this
    server's URL fetch).
    """
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = _navigate(result, extract_path or [])
            text_str = str(text) if text is not None else f"ERROR: extract_path miss; raw response keys={list(result.keys())[:5]}"
            if meta_path:
                meta = _navigate(result, meta_path)
                if meta is not None:
                    return f"[META: finish_reason={meta}]\n\n{text_str}"
            return text_str
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return f"ERROR: HTTP {e.code} from {url}: {body}"
    except urllib.error.URLError as e:
        return f"ERROR: Connection failed to {url}: {e.reason}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"

# Model registry
MODELS = {
    "gemini": call_gemini,
    "gemini-2.5-flash": call_gemini,
    "openai": call_openai,
    "gpt-4o-mini": call_openai,
    "perplexity": call_perplexity,
    "sonar": call_perplexity,
}

def handle_initialize(msg_id):
    """Handle MCP initialize request."""
    write_message({
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "crossmodel", "version": "1.0.0"}
        }
    })

def handle_tools_list(msg_id):
    """Handle tools/list request."""
    write_message({
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "tools": [
                {
                    "name": "query_model",
                    "description": "Send a prompt to an external LLM (Gemini, OpenAI, Perplexity). Returns the model's text response. Use this to get a non-Claude perspective on a question.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "model": {
                                "type": "string",
                                "description": "Model to query. Options: gemini, openai, perplexity (or specific: gemini-2.5-flash, gpt-4o-mini, sonar)",
                                "enum": ["gemini", "gemini-2.5-flash", "openai", "gpt-4o-mini", "perplexity", "sonar"]
                            },
                            "system_prompt": {
                                "type": "string",
                                "description": "System/persona prompt (e.g., the council member's role and reasoning mode)"
                            },
                            "user_prompt": {
                                "type": "string",
                                "description": "The question or task for the model to analyze"
                            }
                        },
                        "required": ["model", "system_prompt", "user_prompt"]
                    }
                },
                {
                    "name": "list_available_models",
                    "description": "Check which external models have API keys configured and are ready to use.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    })

def handle_tool_call(msg_id, tool_name, arguments):
    """Handle tools/call request."""
    if tool_name == "query_model":
        model = arguments.get("model", "gemini")
        system_prompt = arguments.get("system_prompt", "")
        user_prompt = arguments.get("user_prompt", "")

        if model not in MODELS:
            text = f"ERROR: Unknown model '{model}'. Available: {', '.join(MODELS.keys())}"
        else:
            text = MODELS[model](system_prompt, user_prompt)

        write_message({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": text}]
            }
        })

    elif tool_name == "list_available_models":
        available = []
        for name, env_var in [("gemini", "GEMINI_API_KEY"), ("openai", "OPENAI_API_KEY"), ("perplexity", "PERPLEXITY_API_KEY")]:
            key = os.environ.get(env_var)
            status = "READY" if key else "NOT CONFIGURED"
            available.append(f"- {name}: {status} (env: {env_var})")

        text = "Cross-Model MCP Server — Available Models:\n" + "\n".join(available)
        text += "\n\nTo configure: export <ENV_VAR>=your_api_key"

        write_message({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": text}]
            }
        })
    else:
        write_message({
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
        })

def main():
    """Main MCP server loop (stdio transport)."""
    while True:
        msg = read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            handle_initialize(msg_id)
        elif method == "notifications/initialized":
            pass  # Client acknowledgment, no response needed
        elif method == "tools/list":
            handle_tools_list(msg_id)
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            handle_tool_call(msg_id, tool_name, arguments)
        elif msg_id is not None:
            write_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })

if __name__ == "__main__":
    main()
