---
name: sync-usai-models
description: Audits and synchronizes a local USAi provider integration against the live catalog, callable deployments, OpenAPI, and official GSA references. Use when synchronizing USAi models, auditing provider configuration, validating availability after API changes, investigating listed-but-broken models, or checking upstream catalog drift.
argument-hint: "[optional: brief findings summary only]"
allowed-tools: Read Grep Glob Bash Edit Write
---

# Sync USAi Models

Periodically validate a local USAi provider integration against (1) live `/api/v1/models` catalog, (2) non-streaming/streaming/tool-use smoke tests, (3) OpenAPI schema at `https://api.gsa.usai.gov/openapi.json`, and (4) official GSA-TTS catalogs. Safely update model availability, metadata, fallbacks, tier choices, and tests/docs based on findings. Explicitly distinguish **catalog listing** (what the API advertises) from **callable deployment** (what actually works).

## Inputs / Preconditions

Before starting, have:

- **USAI_API_KEY** or **GSAI_API_KEY** set in environment (checked at start).
- Local provider config file(s) with model definitions, fallbacks, and tier mappings (e.g., `extensions/usai.ts`, `settings.json`, test fixtures).
- Clarity on scope: are you auditing one integration, or a full provider instance?
- No confidential secrets to log (the skill enforces sanitization).

If the API key is missing, stop and ask.

## 1. Gather Local State

Read all local configuration files:

```bash
grep -rl "usai\|USAI\|USAi" --include="*.ts" --include="*.js" --include="*.json" <repo-root>
```

Extract:
- **Model list**: which models are configured, referenced, or tested locally
- **Tier mappings**: which models are instant/thinking/pro tiers
- **Fallbacks**: cascade logic (e.g., if a model fails, what's the fallback)
- **Test coverage**: smoke tests for non-streaming, streaming, tool-use modes
- **Documentation references**: any hardcoded model names in docs or README

Record these in a **local inventory** (in-memory is fine; note it for the report).

## 2. Fetch and Validate Upstream

### 2a. Live API Catalog

Fetch the live `/api/v1/models` endpoint (3 requests/second limit):

```bash
curl -s -H "Authorization: Bearer $USAI_API_KEY" \
  https://api.gsa.usai.gov/api/v1/models \
  | jq . > /tmp/usai-models-live.json
```

Parse only fields actually present. The current response normally provides `id`, `created`, `object`, and `owned_by`; do not invent availability flags, capabilities, limits, or tiers that the feed does not publish.

### 2b. OpenAPI Schema

Fetch the schema (single request, under rate limit):

```bash
curl -s https://api.gsa.usai.gov/openapi.json > /tmp/usai-openapi.json
```

Extract:
- **Declared model endpoints** (which paths reference models)
- **Request/response shapes** for each endpoint
- **Authentication method** (Bearer token type confirmation)

### 2c. GSA-TTS Catalog References

Check (offline / cached):
- https://github.com/GSA-TTS/usai-docs (model names and API behavior)
- https://github.com/GSA-TTS/agentic-coding-patterns (enriched USAi metadata and integration patterns)

These are **reference** catalogs; live API is authoritative. Note any discrepancies.

## 3. Smoke Tests

Do not modify local code yet. Run existing smoke tests against live API:

```bash
# Example: if repo has tests, run them
npm test -- --match "*usai*smoke*" 2>&1 | tee /tmp/usai-smoke.log
```

For each mode, confirm callable (no 404 or auth errors):
- **Non-streaming** (chat completion): send a small test prompt to a primary model
- **Streaming** (SSE): open a stream, confirm first chunk arrives
- **Tool-use** (function calling): send tool schema, confirm model accepts it

Record:
- Pass/fail per mode
- Latency (rough, not precise — order of magnitude only)
- Any model-specific errors (e.g., model X doesn't support streaming)

Never include keys or authorization headers. Use a harmless fixed prompt, retain only the minimum sanitized error body needed to diagnose protocol failures, and do not include generated content in the report.

## 4. Reconcile Catalog vs Local

Compare upstream catalog (step 2a) with local inventory (step 1):

| Check | Action if Mismatch |
|-------|-------------------|
| Model ID in upstream but not local | Note as **new upstream model** |
| Model ID in local but not upstream | Note as **not currently advertised**; check official docs for a deprecation notice |
| Listed model fails a smoke test | Note as **listed but not callable**, including sanitized status/code |
| Local metadata differs from the official catalog | Note as **metadata drift** and record catalog revision |
| Live model is absent from the official catalog | Keep conservative metadata and note **enrichment pending** |
| Tier assignment no longer matches callable models | Note as **tier policy review**; do not infer rank from names alone |

## 5. Validation & Findings

Generate a **findings summary** (suitable for USAi support, no secrets):

```
### Audit Report: USAi Models Sync
Date: [ISO 8601 timestamp]
Upstream catalog size: [N] models
Local inventory size: [M] models
Drift: [S] new, [R] removed, [T] tier changes, [C] capability changes

#### New Models (in upstream, not local)
- [model-id-1] (tier: ?, streaming: ?, tools: ?)
- [model-id-2] (tier: ?, streaming: ?, tools: ?)

#### Removed Models (in local, not upstream)
- [model-id-3] (deprecation documented: yes/no, evidence: ?)

#### Tier Drift
- [model-id-4]: was instant, now thinking (reason?)

#### Smoke Tests
✓ Non-streaming: PASS (latency ~[Nms])
✓ Streaming: PASS (first chunk ~[Nms])
✓ Tool-use: PASS
✗ [any failures]: [brief description, no response body]

#### Warnings & Actions Needed
- [if any deprecated models are still in local config]
- [if any tier reassignments conflict with local doc/comments]
- [if smoke tests indicate a capability is broken]

#### No Secrets Included
- Prompts, API responses, and keys are scrubbed.
- This report is suitable for sharing with USAi support.
```

## 6. Apply Changes (Optional, Requires Approval)

If the invocation already authorizes synchronization or patches, apply bounded changes. Otherwise present the findings and ask before editing.

For each approved change:

### Add New Model

1. Identify tier, capability, and fallback chain from findings.
2. Add to local model list with confidence note.
3. Add smoke test if new tier/capability not yet covered.

### Mark Model Deprecated

1. Add deprecation comment in local config with date and suggested replacement.
2. Update related docs/README.
3. Do not remove — keep for compatibility until next major version.

### Update Fallback Chain

1. If a fallback model was removed, reassign.
2. Verify fallback chain terminates at a live model.

### Adjust Tier Assignment

1. Use callable deployments, verified capability, and user preference; never infer rank from names alone.
2. Document the local policy reason in a comment.

Never commit without explicit user approval and a clear understanding of impact.

## 7. Report & Close

Print the **findings summary** (from step 5). State:

- **Audit completed**: local state validated against upstream on [timestamp]
- **No changes applied** (or: changes applied and committed as [SHA] if approved)
- **Recommendations**: if model removal, deprecation, or tier change is flagged, suggest next steps
- **Next sync**: recommend re-run if major GSA-TTS catalog release or if model availability alerts are raised

Example close:

```
✓ Audit complete. Local config matches upstream catalog (S new, R removed).
  Smoke tests: all modes pass. No immediate changes needed.
  Recommended: review new models [list] and decide tier placement.
  Next sync: [date or event trigger].
```

## Rate Limit & Respect

- Respect 3 chat/model calls/sec globally (space requests ~333ms apart).
- Batch catalog fetches (fewer separate requests where possible).
- Never print API keys or auth headers. Do not retain generated content or full successful bodies; preserve only minimal sanitized error evidence needed for support.
- Always sanitize logs before sharing with support.

## Failure / Stop Conditions

Stop and report (do not guess) if:

- API key is missing or invalid (401 response)
- Upstream catalog is unreachable or returns malformed JSON
- OpenAPI schema cannot be fetched
- Smoke tests fail after all requested models and modes have been checked (record all failures, then stop before tier promotion)
- Local config is ambiguous or missing (stop and ask)
- Rate limit is exceeded (backoff, report, retry)

See [REFERENCE.md](REFERENCE.md) for detailed failure modes and recovery steps.
