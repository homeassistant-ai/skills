---
name: debug-mcp-model
description: >
  Diagnoses MCP integration failures where the LLM returns fabricated data
  instead of real Home Assistant state, and guides model selection for
  MCP tool-calling workloads.

  TRIGGER THIS SKILL WHEN:
  - Agent receives hallucinated or synthetic smart-home data instead of live entity states
  - MCP server logs show HTTP 200/202 but responses contain no real HA data
  - Tools appear connected in OpenWebUI but the model never invokes them
  - User asks whether a specific LLM is capable enough for ha-mcp
  - Automations created via MCP claim success but do not appear in HA

  SYMPTOMS THAT TRIGGER THIS SKILL:
  - LLM responds with plausible but fabricated sensor values or entity states
  - Chat responses lack the tool-call indicator (wrench icon / collapsible section)
  - ha-mcp logs show only discovery requests, not tool invocations
  - Model responds as if no tools are available despite correct MCP configuration
  - "No source specified" in responses while other MCP tools show sources
metadata:
  version: "1.0.0"
---

# Debugging MCP Integration and Model Selection

**Core principle:** When an LLM returns fabricated smart-home data, the problem is almost always that the model failed to invoke MCP tools and hallucinated a response instead. Diagnose tool invocation first, then evaluate model capability.

## Diagnostic Workflow

Follow these steps in order. Stop as soon as you identify the failure point.

### 1. Confirm tool invocation is happening

Check whether the model is actually calling MCP tools or just generating text:

| Check | How | Failure indicator |
|-------|-----|-------------------|
| Chat UI tool indicator | Look for wrench icon or collapsible tool-call section in the response | Missing = tools never called |
| ha-mcp debug logs | Enable debug logging; look for specific tool names (`ha_get_entity_state`, `ha_search_entities`, `ha_call_service`) | Only `POST /mcp` with no tool names = only discovery, no invocation |
| Ollama debug logs | Set `OLLAMA_DEBUG=1`; inspect whether response JSON contains `tool_calls` | Plain text response without `tool_calls` = model ignoring tools |

If tools are never invoked, proceed to Step 2. If tools are invoked but return empty/wrong data, skip to Step 5.

### 2. Check function-calling mode in OpenWebUI

OpenWebUI supports two tool-calling modes. The wrong mode for your model causes silent failures.

| Mode | How it works | Best for |
|------|-------------|----------|
| **Native** | Model uses built-in function-calling tokens | Frontier models, large local models (30B+) with native tool support |
| **Default** (prompt-based) | OpenWebUI injects a prompt template guiding tool selection | Small local models, models without native function-calling |

**Action:** In Admin > Settings > Models > select model > Advanced Params, try switching between Native and Default mode. For models under 30B parameters, **Default mode is almost always more reliable**.

### 3. Verify tool assignment

Tools must be explicitly enabled for the model in OpenWebUI:

- Go to Workspace > Models > select your model
- Confirm ha-mcp tools are listed and enabled
- If multiple tool servers are configured via config file, test with only ha-mcp enabled (known issue: multiple tool configs can cause tools to be ignored)

### 4. Evaluate model capability

See `references/model-requirements.md` for the full model selection guide.

**Quick assessment — minimum requirements for reliable MCP tool calling:**

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Parameters | 30B+ | 70B+ or frontier API |
| Native function calling | Required for Native mode | Required |
| Context window | 8K+ | 32K+ (ha-mcp exposes many tools) |
| Quantization (local) | Q5_K_M or higher | FP16 / Q8 |

**Models known to work reliably with ha-mcp:**

- Cloud: Claude 4.5 Sonnet, GPT-4o, Gemini 2.5 Flash
- Local: Qwen 3 32B, Llama 3.3 70B (with sufficient VRAM)

**Models that frequently fail:**

- Any model under 14B parameters in Native mode
- Ministral 3 8B (message ordering bug with tool results)
- Older Mistral/Ministral variants via Ollama OpenAI-compatible endpoint

### 5. Verify ha-mcp backend connectivity

If tools are invoked but return empty or wrong data:

```bash
# Test HA API access from the ha-mcp host
curl -s -H "Authorization: Bearer <LONG_LIVED_TOKEN>" \
  http://<HA_HOST>:8123/api/ | head -c 200

# Test entity access
curl -s -H "Authorization: Bearer <LONG_LIVED_TOKEN>" \
  http://<HA_HOST>:8123/api/states | head -c 500
```

Verify:
- Long-lived access token has admin privileges
- HA instance is reachable from the ha-mcp container/host
- No firewall or reverse proxy stripping auth headers

### 6. Reduce context pressure

ha-mcp exposes many tools. Small models may choke on the tool schema alone:

- Reduce exposed entities via ha-mcp configuration (area/domain filters)
- Remove knowledge bases attached to the model in OpenWebUI
- Simplify the system prompt

---

## Common Failure Patterns

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Plausible but fake sensor values | Model hallucinating instead of calling tools | Switch to Default mode or use a larger model |
| "No source specified" in response | Tool never invoked | Verify tool assignment and function-calling mode |
| Logs show 200/202 but no real data | Only tool discovery happened, not invocation | Enable debug logging to distinguish discovery from calls |
| Official HA MCP works but ha-mcp does not | ha-mcp exposes more tools, overwhelming the model | Use a larger model or reduce exposed tools |
| Automation "created" but not in HA | Tool call succeeded but HA API returned an error silently | Check ha-mcp debug logs for API error responses |
| Mistral model errors after tool result | Message ordering bug: system message after tool role | Use Default mode or a non-Mistral model |

---

## Reference Files

| File | When to read |
|------|-------------|
| `references/model-requirements.md` | Choosing or evaluating a model for MCP tool calling |
