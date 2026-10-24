# LiteLLM patches (Pi: /mnt/ssd/apps/librechat/litellm-patches)

`responses_transformation.py` replaces
`litellm/completion_extras/litellm_responses_transformation/transformation.py` inside the
`librechat-litellm` container (bind mount in docker-compose.yml; base: LiteLLM 1.106.2).

Why: the ChatGPT/Codex backend streams function calls without `response.function_call_arguments.delta`
events; arguments only arrive in `response.output_item.done`, where upstream emits an empty delta. With two
or more parallel tool calls every call reached LibreChat with empty arguments ("Missing required fields").
The patch forwards the arguments once on `output_item.done` when no deltas were streamed for that item.
Search for `_vr_` to see the changes. Re-check after every LiteLLM image update (diff against the upstream
file; drop the mount once upstream handles delta-less argument streaming). The mount path contains the
image's Python version (`/app/.venv/lib/python3.13/site-packages/...`).
