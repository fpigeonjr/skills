---
# USAi Model Sync — Reference & Failure Modes

## Failure Modes & Recovery

### API Key Missing / Invalid

**Symptom**: `401 Unauthorized` or `USAI_API_KEY` not set.

**Recovery**:
1. Check presence without printing the value: `[[ -n "${USAI_API_KEY:-${GSAI_API_KEY:-}}" ]]`.
2. If empty, ask the user to export `USAI_API_KEY` or its `GSAI_API_KEY` alias.
3. Retry fetch.

### Upstream Catalog Unreachable

**Symptom**: `curl` returns network error or 502/503.

**Recovery**:
1. Confirm DNS/TLS connectivity using a documented endpoint such as `<host>/openapi.json`.
2. Wait 30s, retry once.
3. If still down, report maintenance window; skip upstream sync, proceed with local validation only.

### Malformed JSON Response

**Symptom**: `jq` fails or response is truncated.

**Recovery**:
1. Save raw response to temp file: check size, character encoding.
2. Manually inspect for JSON syntax errors (unmatched braces, trailing commas).
3. If response is incomplete (e.g., truncated by timeout), retry with longer timeout: `curl -m 30 ...`.
4. If parsing still fails, report the status, content type, byte count, and a minimal sanitized error message; do not attach an arbitrary raw-response prefix.

### Smoke Test Failures

**Symptoms**: Non-streaming, streaming, or tool-use mode fails.

**Recovery per mode**:

- **Non-streaming chat fails**:
  - Confirm model ID matches catalog (typo?).
  - Check if model requires special auth scope (some need separate auth).
  - If 404, model is not callable (mark as unavailable, note in report).

- **Streaming fails** (no SSE chunks):
  - Confirm `stream: true` in request.
  - Check official docs for any explicit streaming limitation; `/models` does not publish capability flags.
  - Retry once with a normal timeout; if it still fails, record the exact mode as not callable.

- **Tool-use fails** (model doesn't accept `tools` field):
  - Check official docs/OpenAPI for tool support; `/models` does not publish a `tool_use` capability.
  - If support is undocumented, test it and label the result as observed behavior.
  - If documented but failing, mark the deployment behavior as inconsistent with the contract.

**Action**: Do not stop the entire audit. Record failure, continue to gather all findings, then report with all failures listed.

### Rate Limit Exceeded

**Symptom**: `429 Too Many Requests`.

**Recovery**:
1. Backoff: wait 60s.
2. Retry only failed request (don't retry entire batch).
3. Slow down subsequent requests: space them ~400ms apart instead of ~333ms.
4. Report in findings: "rate limit hit during [stage], recovered."

### Local Config Ambiguous

**Symptom**: Model referenced in multiple places with conflicting tiers, or config file syntax is broken.

**Recovery**:
1. Ask user: "which model list is authoritative?" (point to specific file paths).
2. Ask: "what tier should [model] be in?" (get explicit answer).
3. Do not guess or pick arbitrarily.

### Tier Assignment Conflict

**Symptom**: Local config has instant tier, but upstream catalog says thinking; or tier is not listed upstream at all.

**Recovery**:
1. Treat tier assignment as local policy based on callable deployments, observed behavior, and user preference; do not infer it from model names.
2. Report conflict in findings.
3. Ask user for approval before changing local tier.
4. If tier is not in upstream catalog at all, it's likely user-defined (e.g., a local nickname); keep it as-is unless user says otherwise.

## Audit Completeness Checklist

Before closing the audit, confirm:

- [ ] API key was valid (at least one successful upstream call made)
- [ ] Upstream catalog was fetched and parsed
- [ ] OpenAPI schema was fetched and reviewed
- [ ] Local inventory was gathered from all relevant files
- [ ] All reconciliation checks completed (new, removed, tier, capability)
- [ ] Smoke tests ran (pass or fail, all recorded)
- [ ] Findings summary generated with no secrets
- [ ] User approval obtained before any local edits
- [ ] Changes validated; commit only if the user explicitly requested one

## Catalog vs Deployment Distinction

This is critical: **catalog listing** ≠ **callable deployment**.

- **Catalog listing** (from `/api/v1/models`): the model is advertised by the API. It does not currently publish availability or capability flags.
- **Callable deployment** (smoke test succeeds): the model is actually reachable and responds to requests.

A model can be listed but not callable if:
- Infrastructure is down (model service unreachable).
- Model is in "maintenance" state (not serving requests).
- Caller lacks permissions or auth scope.

Always verify with smoke tests. If a model is listed but not callable, flag it in findings as **available but unreachable** and escalate to USAi support.

## GSA-TTS References

### USAi Docs

Repository: https://github.com/GSA-TTS/usai-docs

Look for model naming examples, endpoint behavior, feature limitations, guardrails, and deprecation notices. Do not assume the docs define instant/thinking/pro tiers or a complete capability matrix.

### Agentic Coding Patterns

Repository: https://github.com/GSA-TTS/agentic-coding-patterns

Use `integrations/providers/usai/catalog.json` for enriched names, context/output limits, costs, and backend mapping. Record the fetched commit SHA because the committed catalog can lag the live gateway. Treat any tier policy as local policy, not upstream fact.

These are **guidance**, not authority. Live API catalog is always the source of truth for availability.

## OpenAPI Schema Inspection

The schema at `<host>/openapi.json` (host from `USAI_BASE_URL`) defines the API contract.

Key fields to extract:
- **The actual model-list schema** (currently `ModelList` and its item schema): use only fields declared there; do not assume availability, capability, or context metadata.
- **`paths[*]`**: each endpoint path; look for model parameters or model enumeration.
- **`securitySchemes`**: confirms Bearer token auth and token scope requirements.

If the schema lists a model field not present in upstream catalog, or if the schema and catalog schemas don't match (e.g., schema says `deprecated: boolean` but catalog lacks the field), note it as **schema drift** in findings.

## Findings Summary Fields

Ensure the audit report includes:

- **Timestamp** (ISO 8601, so it's clear when the audit ran).
- **Catalog sizes** (upstream count, local count, makes drift visible).
- **Drift summary** (quantified: N new, M removed, T tier changes, C capability mismatches).
- **New models** (list observed smoke-test results and leave tier placement for policy review).
- **Removed models** (list with deprecation flag, reason if available).
- **Tier drift** (old → new for each model, reason if known).
- **Smoke test results** (pass/fail per mode, no response bodies).
- **Warnings** (any deprecated models still in use, any blocked capabilities, any unverified tier assignments).
- **Actions needed** (explicit list of what the user should do next).
- **No secrets** (confirm that the report contains no API keys, auth headers, generated content, or unrelated response data; minimal sanitized provider errors may be included).

## Deterministic Helper Script

The skill does not include a bundled script. Instead, here's a bash snippet users can save and invoke if they want deterministic, repeatable audits:

```bash
#!/usr/bin/env bash
# usai-audit.sh: minimal USAi model sync helper
# Usage: USAI_API_KEY=xxx ./usai-audit.sh [local-config-dir]

set -eu

API_KEY="${USAI_API_KEY:-${GSAI_API_KEY:-}}"
if [ -z "$API_KEY" ]; then
  echo "Error: USAI_API_KEY or GSAI_API_KEY not set" >&2
  exit 1
fi
if [ -z "${USAI_BASE_URL:-}" ]; then
  echo "Error: USAI_BASE_URL not set" >&2
  exit 1
fi

LOCAL_DIR="${1:-.}"
TMPDIR="${TMPDIR:-/tmp}"

echo "=== Fetching upstream catalog ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$USAI_BASE_URL/models" \
  | jq '.' > "$TMPDIR/usai-models-live.json"
echo "Saved to $TMPDIR/usai-models-live.json"

echo "=== Fetching OpenAPI schema ==="
curl -s "${USAI_BASE_URL%/api/v*}/openapi.json" \
  | jq '.' > "$TMPDIR/usai-openapi.json"
echo "Saved to $TMPDIR/usai-openapi.json"

echo "=== Local model inventory ==="
grep -r "usai\|USAi" "$LOCAL_DIR" --include="*.ts" --include="*.js" --include="*.json" \
  | grep -i "model" | head -20
echo "(truncated; review manually for full list)"

echo ""
echo "=== Next steps ==="
echo "1. Review $TMPDIR/usai-models-live.json for new models"
echo "2. Run smoke tests: npm test -- --match '*usai*smoke*'"
echo "3. Compare local config against upstream catalog"
echo "4. Use skill for full audit and approval workflow"
```

Users should save this as `scripts/usai-audit.sh` (or similar) and invoke it only as a convenience; the skill itself runs all steps interactively.

## Rate Limit Strategy

The USAi API enforces **3 requests/second** globally. To stay under the limit:

1. **Batch upstream fetches**: combine model list + OpenAPI schema into 2–3 sequential requests, not 50+ individual model queries.
2. **Space requests**: after each request, wait ~400ms before the next (to stay well under 3/sec).
3. **Reuse cached responses**: if OpenAPI schema hasn't changed since last audit, skip fetching it again (assume cache is valid for ~1 week).
4. **Log request times**: record when each request was sent; if you approach the limit, slow down further or defer smoke tests to a separate session.

Never fire parallel requests without explicit backpressure; use a queue or sequential loop.

## Secret Sanitization

Before sharing any report, audit log, or curl output with USAi support:

- [ ] Remove or mask all Bearer token values (replace with `REDACTED`).
- [ ] Remove generated content and full successful response bodies.
- [ ] Keep exact public model IDs; they are necessary for support diagnosis and are not secrets.
- [ ] Keep timestamps needed to correlate incidents, but remove cookies and sensitive query parameters.
- [ ] Keep minimal provider error code/message text when necessary to reproduce a gateway defect; remove unrelated payload data.

Example safe log entry:

```
Request: GET /api/v1/models
Status: 200 OK
Latency: 145ms
Response: {count: 47, models: [... (47 entries, first 3 shown) ...]}
(full response saved to audit log, redacted for this report)
```

Example unsafe log entry:

```
Request: GET /api/v1/models
Authorization: Bearer sk_live_aBc123XyZ789...
Response: {"count": 47, "models": [{...full 10KB response...}]}
```
