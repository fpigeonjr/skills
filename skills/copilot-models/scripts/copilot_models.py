#!/usr/bin/env python3
"""Poll GitHub Copilot's live /models endpoint and compare it with Pi.

Reads the Copilot API token Pi stores in auth.json. The token is sent only to an
allowlisted Copilot host over HTTPS, redirects are refused, and the token is never
printed, logged, or written. Standard library only.

Usage:
  copilot_models.py [--agent-dir DIR] [--check REF ...] [--all] [--json] [--allow-host HOST]

REF is [github-copilot/]MODEL_ID[:THINKING], THINKING one of
off, minimal, low, medium, high, xhigh, max.

Exit codes: 0 ok, 2 auth/config problem, 3 network/API/response error.
"""

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

PROVIDER = "github-copilot"
ALLOWED_SUFFIX = ".githubcopilot.com"
INDIVIDUAL_HOST = "api.individual.githubcopilot.com"
DEFAULT_HOST = INDIVIDUAL_HOST  # Pi's fallback when the token has no proxy-ep
PI_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max")
HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")
REF_RE = re.compile(r"^(?:github-copilot/)?([A-Za-z0-9][A-Za-z0-9._-]*)(?::([a-z]+))?$")
HEADERS = {
    "Editor-Version": "vscode/1.99.0",
    "Editor-Plugin-Version": "copilot-chat/0.26.0",
    "Copilot-Integration-Id": "vscode-chat",
}


def die(code, msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def obj(x):
    return x if isinstance(x, dict) else {}


def lst(x):
    return x if isinstance(x, list) else []


def num(x):
    ok = isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0
    return x if ok else None


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        die(2, f"cannot read {os.path.basename(path)} as JSON")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # urllib then raises HTTPError for the 3xx; the token never follows a redirect


def resolve_host(token, allow_hosts):
    m = re.search(r"(?:^|;)proxy-ep=([^;]*)", token)
    if not m:
        return DEFAULT_HOST
    proxy = m.group(1).strip().lower()
    host = "api." + proxy[len("proxy."):] if proxy.startswith("proxy.") else proxy
    if not HOST_RE.match(host):
        die(2, "token proxy-ep is not a plain hostname; refusing to send the token")
    if not (host.endswith(ALLOWED_SUFFIX) or host in allow_hosts):
        die(2, f"token proxy-ep resolves to {host}, outside *{ALLOWED_SUFFIX}; "
               "rerun with --allow-host only if this is your known GitHub Enterprise Copilot host")
    return host


def fetch_live(auth, allow_hosts):
    tok = auth.get("access")
    if not isinstance(tok, str) or not tok:
        die(2, "no github-copilot access token in auth.json; log in to GitHub Copilot in Pi")
    if any(ord(c) < 0x21 or ord(c) > 0x7E for c in tok):
        die(2, "github-copilot access token is malformed; log in to GitHub Copilot in Pi again")
    exp = num(auth.get("expires")) or 0
    exp = exp / 1000 if exp > 1e12 else exp
    if exp and exp < time.time():
        die(2, "Copilot token expired; start a Pi session on any github-copilot model to refresh it, then rerun")
    host = resolve_host(tok, allow_hosts)
    req = urllib.request.Request(f"https://{host}/models", headers={"Authorization": f"Bearer {tok}", **HEADERS})
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        die(2 if e.code in (401, 403) else 3, f"GET https://{host}/models failed: HTTP {e.code}")
    except urllib.error.URLError as e:
        die(3, f"GET https://{host}/models failed: {type(e.reason).__name__}")
    except (TimeoutError, OSError):
        die(3, f"GET https://{host}/models failed: timeout or connection error")
    except json.JSONDecodeError:
        die(3, "GET /models returned invalid JSON")
    except ValueError:
        die(3, "GET /models request could not be built or decoded")
    data = obj(body).get("data")
    if not isinstance(data, list):
        die(3, "GET /models returned an unexpected shape (no data list)")
    return host, [m for m in data if isinstance(m, dict) and isinstance(m.get("id"), str)]


def available_ids(data, host):
    """Mirror Pi's availability rule (pi-ai github-copilot OAuth catalog parsing)."""
    usable = [m for m in data if obj(obj(m.get("capabilities")).get("supports")).get("tool_calls") is not False]
    picker = [m["id"] for m in usable
              if m.get("model_picker_enabled") is True and obj(m.get("policy")).get("state") != "disabled"]
    if picker or host != INDIVIDUAL_HOST:
        return set(picker)
    return {m["id"] for m in usable if obj(m.get("policy")).get("state") == "enabled"}


def pi_registry(agent_dir):
    """(ids, status): selectable Copilot IDs per `pi --list-models` for this agent dir.

    ids is None when the check could not run; an empty set is a real, successful result.
    """
    if not shutil.which("pi"):
        return None, "not checked: `pi` not on PATH"
    env = {**os.environ, "PI_CODING_AGENT_DIR": agent_dir}
    try:
        proc = subprocess.run(["pi", "--list-models", PROVIDER], capture_output=True, text=True, timeout=60, env=env)
    except (OSError, subprocess.SubprocessError):
        return None, "check failed: `pi --list-models` did not run"
    if proc.returncode != 0:
        return None, f"check failed: `pi --list-models` exited {proc.returncode}"
    rows = (line.split() for line in proc.stdout.splitlines())
    return {p[1] for p in rows if len(p) > 1 and p[0] == PROVIDER}, "checked"


def summarize(m, avail, cache):
    caps = obj(m.get("capabilities"))
    lim = obj(caps.get("limits"))
    sup = obj(caps.get("supports"))
    cost = obj(obj(cache).get("cost"))
    return {
        "id": m["id"],
        "vendor": str(m.get("vendor") or ""),
        "category": str(m.get("model_picker_category") or "-"),
        "available": m["id"] in avail,
        "picker": m.get("model_picker_enabled") is True,
        "preview": m.get("preview") is True,
        "policy": str(obj(m.get("policy")).get("state") or "-"),
        "tool_calls": sup.get("tool_calls") is not False,
        "type": str(caps.get("type") or ""),
        "context": num(lim.get("max_context_window_tokens")),
        "max_output": num(lim.get("max_output_tokens")),
        "efforts": [e for e in lst(sup.get("reasoning_effort")) if isinstance(e, str)],
        "cost_in": num(cost.get("input")),
        "cost_out": num(cost.get("output")),
        "in_cache": cache is not None,
        "cache_context": num(obj(cache).get("contextWindow")),
        "cache_max_output": num(obj(cache).get("maxTokens")),
        "cache_reasoning": obj(cache).get("reasoning") if cache is not None else None,
        "thinking_map": obj(obj(cache).get("thinkingLevelMap")),
    }


def pi_thinking_levels(r):
    """Pi's getSupportedThinkingLevels rule (pi-ai models.js), applied to cached metadata; None if unknown."""
    if r["cache_reasoning"] is None:
        return None
    if not r["cache_reasoning"]:
        return ["off"]
    tmap = r["thinking_map"]
    return [lv for lv in PI_LEVELS if not (lv in tmap and tmap[lv] is None)
            and (lv not in ("xhigh", "max") or tmap.get(lv) is not None)]


def check_ref(ref, by_id, registry, snapshot):
    m = REF_RE.match(ref)
    if not m or (m.group(2) and m.group(2) not in PI_LEVELS):
        return None, f"BAD-REF (expected [{PROVIDER}/]ID[:{'|'.join(PI_LEVELS)}])"
    mid, level = m.group(1), m.group(2)
    r = by_id.get(mid)
    if not r:
        return None, "MISSING (not in live Copilot catalog)"
    if not r["available"]:
        why = "no tool calls" if not r["tool_calls"] else f"picker={r['picker']}, policy={r['policy']}"
        return r, f"UNAVAILABLE ({why})"
    if registry is not None and mid not in registry:
        if snapshot is not None and mid not in snapshot:
            return r, "NOT-IN-PI (Pi's saved account availability excludes it; log in to GitHub Copilot in Pi again)"
        return r, "NOT-IN-PI (absent from Pi's model catalog; try `pi update --models`)"
    if level:
        levels = pi_thinking_levels(r)
        if levels is None:
            return r, f"VERIFY-THINKING (no cached Pi metadata to confirm {level})"
        if level not in levels:
            return r, f"UNSUPPORTED-THINKING (Pi supports {','.join(levels)}; it clamps {level})"
        wire = r["thinking_map"].get(level) or ("none" if level == "off" else level)
        if level != "off" and r["efforts"] and wire not in r["efforts"]:
            return r, f"VERIFY-THINKING (Pi sends {wire}; live advertises {','.join(r['efforts'])})"
    if r["preview"]:
        return r, "PREVIEW"
    return r, "ok"


def fmt_k(n):
    if not n:
        return "?"
    return f"{n / 1_000_000:.2g}M" if n >= 1_000_000 else f"{round(n / 1000)}k"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent-dir", default=os.environ.get("PI_CODING_AGENT_DIR") or os.path.expanduser("~/.pi/agent"))
    ap.add_argument("--check", nargs="*", default=[], metavar="REF", help="model refs to validate")
    ap.add_argument("--all", action="store_true", help="include unavailable models (legacy, embeddings, disabled)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--allow-host", action="append", default=[], metavar="HOST",
                    help="extra exact API host to trust (GitHub Enterprise only)")
    ap.add_argument("--no-pi", action="store_true", help="skip the `pi --list-models` registry check")
    a = ap.parse_args()

    auth = obj(obj(load_json(os.path.join(a.agent_dir, "auth.json"))).get(PROVIDER))
    if not auth:
        die(2, f"no {PROVIDER} entry in {a.agent_dir}/auth.json")
    store = obj(load_json(os.path.join(a.agent_dir, "models-store.json"))).get(PROVIDER)
    cache_ok = isinstance(store, dict) and isinstance(store.get("models"), list)
    cache = {m["id"]: m for m in lst(obj(store).get("models")) if isinstance(m, dict) and isinstance(m.get("id"), str)}
    raw_snapshot = auth.get("availableModelIds")
    snapshot = {x for x in raw_snapshot if isinstance(x, str)} if isinstance(raw_snapshot, list) else None

    host, data = fetch_live(auth, {h.strip().lower() for h in a.allow_host})
    avail = available_ids(data, host)
    rows = [summarize(m, avail, cache.get(m["id"])) for m in data]
    by_id = {r["id"]: r for r in rows}
    registry, registry_status = (None, "not checked: --no-pi") if a.no_pi else pi_registry(a.agent_dir)
    shown = rows if a.all else [r for r in rows if r["available"]]

    billing = sorted({m["warning_message"] for m in data if isinstance(m.get("warning_message"), str)})
    drift = {
        "registry_status": registry_status,
        "available_not_in_pi": sorted(avail - registry) if registry is not None else None,
        "pi_not_available": sorted(registry - avail) if registry is not None else None,
        "stale_account_snapshot": sorted(avail ^ snapshot) if snapshot is not None else None,
        "cache_present": cache_ok,
        "limit_diffs": [],
    }
    for r in rows:
        if not (r["available"] and r["in_cache"]):
            continue
        for field, cached, live in (("context", r["cache_context"], r["context"]),
                                    ("max_output", r["cache_max_output"], r["max_output"])):
            if cached and live and cached != live:
                drift["limit_diffs"].append({"id": r["id"], "field": field, "pi": cached, "live": live,
                                             "pi_larger": cached > live})

    checks = []
    for ref in a.check:
        r, status = check_ref(ref, by_id, registry, snapshot)
        checks.append({"ref": ref, "status": status, "category": r["category"] if r else None,
                       "cost_out": r["cost_out"] if r else None})

    if a.json:
        out = [{**{k: v for k, v in r.items() if k != "thinking_map"}, "pi_thinking_levels": pi_thinking_levels(r)}
               for r in shown]
        json.dump({"host": host, "fetched_at": int(time.time()), "billing_notes": billing,
                   "models": out, "drift": drift, "checks": checks}, sys.stdout, indent=1, allow_nan=False)
        print()
        return

    print(f"# Copilot live models: {host}, {len(avail)} available to this account of {len(rows)} listed\n")
    for note in billing:
        print(f"> billing (from API): {note}\n")
    print("| id | vendor | category | context | max out | reasoning | Pi list $in/$out per Mtok | flags |")
    print("|---|---|---|---|---|---|---|---|")
    order = {"lightweight": 0, "versatile": 1, "powerful": 2}
    for r in sorted(shown, key=lambda r: (order.get(r["category"], 9), r["cost_out"] if r["cost_out"] is not None
                                          else float("inf"), r["id"])):
        flags = [f for f, on in [("preview", r["preview"]), ("unavailable", not r["available"]),
                                 ("not-in-pi", registry is not None and r["available"] and r["id"] not in registry)]
                 if on]
        cost = f"{r['cost_in']}/{r['cost_out']}" if r["cost_out"] is not None else "-"
        print(f"| {r['id']} | {r['vendor']} | {r['category']} | {fmt_k(r['context'])} | {fmt_k(r['max_output'])} "
              f"| {','.join(r['efforts']) or '-'} | {cost} | {','.join(flags)} |")

    print("\n## Drift\n")
    if registry is None:
        print(f"- Pi registry: {registry_status}; selectability unverified")
    else:
        print(f"- available, not selectable in Pi: {', '.join(drift['available_not_in_pi']) or 'none'}")
        print(f"- in Pi, not available to this account: {', '.join(drift['pi_not_available']) or 'none'}")
    if snapshot is not None:
        print(f"- Pi's saved account availability differs on: {', '.join(drift['stale_account_snapshot']) or 'none'}")
    if not cache_ok:
        print("- Pi catalog cache (models-store.json): absent for this provider; prices and limit diffs unavailable")
    elif drift["limit_diffs"]:
        print("- limit diffs, Pi catalog cache → live:")
        for d in drift["limit_diffs"]:
            note = ""
            if d["pi_larger"]:
                note = (" (Pi larger: compaction may trigger late)" if d["field"] == "context"
                        else " (Pi larger: requests may ask for more output than Copilot advertises)")
            print(f"  - {d['id']} {d['field']}: {fmt_k(d['pi'])} → {fmt_k(d['live'])}{note}")
    else:
        print("- limit diffs: none")

    if checks:
        print("\n## Checked refs\n")
        print("| ref | status | category | Pi list $out |")
        print("|---|---|---|---|")
        for c in checks:
            cost = c["cost_out"] if c["cost_out"] is not None else "-"
            print(f"| {c['ref']} | {c['status']} | {c['category'] or '-'} | {cost} |")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # never echo exception text: it can embed request headers
        die(3, f"unexpected {type(e).__name__}")
