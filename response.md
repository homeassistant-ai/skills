**Ministral 3 8B likely can't handle MCP tool calling reliably.** Small models often fail to generate proper `tool_calls` JSON and hallucinate responses instead. Quick fixes:

1. In OpenWebUI, switch function-calling mode from **Native** to **Default** (prompt-based).
2. Make sure ha-mcp tools are explicitly assigned to your model.
3. Look for the wrench icon in chat — if it's missing, tools aren't firing.
4. Try a larger model (Qwen 3 32B, or a cloud API) to confirm it's a model limitation.

HTTP 200 in logs just means the request completed — it doesn't mean tools were invoked.
