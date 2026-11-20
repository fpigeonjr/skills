#!/usr/bin/env python3
"""Read-only worktree inventory for the cleanup-machine skill.

Discovers Git repositories under configured roots, enumerates their linked
worktrees (including agent-managed ones elsewhere on disk), and classifies each
one. It never deletes, prunes, fetches, or edits a repository, and runs Git with
optional locks disabled so `git status` does not refresh indexes. Its only
writes are manifest.jsonl (the approval authority, digest-pinned, including the
scan settings) and inventory.json (informational) in a new owner-only run
directory.

  scan:     cleanup_inventory.py scan --root ~/Code --depth 3 --agent-root DIR --integration REF
  recheck:  cleanup_inventory.py recheck --run RUN_DIR --digest SHA256 --rows 1-4,7 [--approve-ignored]

Python 3 stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Conventional build-output directory names. Matching one is a reporting hint for
# grouping, NOT evidence that the contents can be regenerated: worktrees holding
# only such directories are classified `ignored-conventional`, which is executable
# only when the user explicitly approves losing the exact listed paths.
CONVENTIONAL_OUTPUT = {
    "node_modules", ".angular", ".nx", "dist", "out-tsc", "coverage", "storybook-static",
    "test-results", "playwright-report", "blob-report",
}
SKIP_WALK = {"node_modules", ".git", ".angular", ".nx", "dist"}
CLASSES = ("safe", "ignored-conventional", "recent", "ignored-other", "unreachable", "dirty", "held", "prunable", "error")
EXECUTABLE = {"safe": False, "ignored-conventional": True}   # class -> needs --approve-ignored
MANIFEST_SCHEMA = "cleanup-machine/manifest/v2"
GIT_ENV = {"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}


class InspectError(Exception):
    """A safety-relevant inspection failed; the target must be classified `error`."""


def git(args, cwd, timeout=120, ok=(0,)):
    """Run a read-only git command. Return (rc, stdout); raise InspectError unless rc is in `ok`."""
    env = dict(os.environ, **GIT_ENV)
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InspectError(f"git {args[0]}: {type(exc).__name__}") from exc
    if r.returncode not in ok:
        raise InspectError(f"git {args[0]} exited {r.returncode}")
    return r.returncode, r.stdout.rstrip("\n")


LSOF = ["lsof", "-w", "-a", "-d", "cwd", "-Fn"]


def cwd_holders(cmd=None):
    """Set of process working directories, or None if the inspection failed."""
    try:
        r = subprocess.run(cmd or LSOF, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0 or not r.stdout:
        return None
    return {l[1:] for l in r.stdout.splitlines() if l.startswith("n")}


def find_repos(roots, depth, errors=None):
    """Principal checkouts (a .git directory) under each root, to the given depth."""
    found = []
    errors = [] if errors is None else errors
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            errors.append({"root": str(root), "error": "root missing"})
            continue
        stack = [(root, 0)]
        while stack:
            d, lvl = stack.pop()
            if (d / ".git").is_dir():
                found.append(d.resolve())
            if lvl >= depth:
                continue
            try:
                kids = [k for k in d.iterdir() if k.is_dir() and not k.is_symlink() and k.name not in SKIP_WALK]
            except OSError as exc:
                errors.append({"root": str(d), "error": f"unreadable: {type(exc).__name__}"})
                continue
            stack.extend((k, lvl + 1) for k in kids)
    return sorted(set(found))


def repos_from_agent_roots(agent_roots, errors=None):
    """Principal checkouts owning worktrees at <agent-root>/<repo>/<name> (.git file -> gitdir)."""
    owners = set()
    errors = [] if errors is None else errors
    for root in agent_roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            errors.append({"root": str(root), "error": "agent root missing"})
            continue
        for gitfile in root.glob("*/*/.git"):
            try:
                line = gitfile.read_text().strip() if gitfile.is_file() else ""
            except OSError as exc:
                errors.append({"root": str(gitfile.parent), "error": f"unreadable: {type(exc).__name__}"})
                continue
            if not line.startswith("gitdir:"):
                continue
            gitdir = Path(line.split(":", 1)[1].strip())
            if not gitdir.is_absolute():
                gitdir = (gitfile.parent / gitdir).resolve()
            if gitdir.parent.name == "worktrees" and gitdir.parent.parent.name == ".git":
                owners.add(gitdir.parent.parent.parent.resolve())
    return sorted(owners)


def parse_worktrees(porcelain):
    """Parse `git worktree list --porcelain -z`."""
    blocks, cur = [], {}
    for field in porcelain.split("\0"):
        if not field:
            if cur:
                blocks.append(cur)
            cur = {}
            continue
        key, _, val = field.partition(" ")
        cur[key] = val if val else True
    if cur:
        blocks.append(cur)
    return blocks


def parse_status(out):
    """Parse `git status --porcelain=v1 -z --ignored`. Returns (changed, untracked, ignored) path lists."""
    changed, untracked, ignored = [], [], []
    parts = out.split("\0")
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if not rec:
            continue
        code, path = rec[:2], rec[3:]
        if code == "!!":
            ignored.append(path.rstrip("/"))
        elif code == "??":
            untracked.append(path)
        else:
            changed.append(path)
            if code[0] in "RC":
                i += 1  # rename/copy source follows as its own field
    return changed, untracked, ignored


def recent_activity(path, days):
    """True if any file outside skipped dirs changed within `days`. Raises InspectError on walk errors."""
    cutoff = time.time() - days * 86400
    errors = []
    for dirpath, dirnames, filenames in os.walk(path, onerror=errors.append):
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK]
        for f in filenames:
            if f == ".git":
                continue
            try:
                if os.lstat(os.path.join(dirpath, f)).st_mtime >= cutoff:
                    return True
            except OSError as exc:
                raise InspectError("file walk failed") from exc
    if errors:
        raise InspectError("file walk failed")
    return False


def size_kb(path):
    """Size in KiB, or None if `du` failed (size unknown, not zero)."""
    try:
        r = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, timeout=600)
        return int(r.stdout.split()[0]) if r.returncode == 0 else None
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def integration_refs(repo, patterns):
    """Confirmed integration refs (exact or glob) that exist here, plus the remote default branch."""
    refs = []
    for pat in patterns:
        _, out = git(["for-each-ref", "--format=%(refname:short)", f"refs/remotes/{pat}", f"refs/heads/{pat}"], repo)
        refs.extend(x for x in out.splitlines() if x)
    rc, head = git(["symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], repo, ok=(0, 1))
    if rc == 0 and head:
        refs.append(head)
    return list(dict.fromkeys(refs))


def conventional_only(path, ignored):
    """True if every ignored path is a real (non-symlink) top-level directory with a conventional name."""
    for x in ignored:
        p = Path(path) / x
        if "/" in x or x not in CONVENTIONAL_OUTPUT or p.is_symlink() or not p.is_dir():
            return False
    return True


def classify(repo, wt, *, refs, stale_days, holders, measure):
    """Return a record for one linked worktree. Never mutates anything."""
    path = Path(wt["worktree"])
    branch = wt["branch"].removeprefix("refs/heads/") if isinstance(wt.get("branch"), str) else ""
    rec = {"repo": str(repo), "path": str(path), "branch": branch or None, "head": wt.get("HEAD") or None,
           "common_dir": None, "kb": None, "ignored": [], "evidence": []}
    ev = rec["evidence"]
    if "prunable" in wt or not path.is_dir():
        rec["class"] = "prunable"
        ev.append("registered but directory missing")
        return rec
    if measure:
        rec["kb"] = size_kb(path)
        if rec["kb"] is None:
            ev.append("size unknown")
    try:
        return _classify(repo, path, branch, wt, rec, refs=refs, stale_days=stale_days, holders=holders)
    except InspectError as exc:
        rec["class"] = "error"
        ev.append(str(exc))
        return rec


def _classify(repo, path, branch, wt, rec, *, refs, stale_days, holders):
    ev = rec["evidence"]
    _, cdir = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], path)
    rec["common_dir"] = os.path.realpath(cdir)
    if any(c in str(path) for c in "\t\n\r"):
        raise InspectError("control character in path")
    reasons = []
    if "locked" in wt:
        reasons.append("locked")
    if not branch:
        reasons.append("detached HEAD")
    _, st = git(["status", "--porcelain=v1", "-z", "--ignored", "--untracked-files=normal"], path)
    changed, untracked, ignored = parse_status(st)
    if changed:
        reasons.append(f"{len(changed)} changed")
    if untracked:
        reasons.append(f"{len(untracked)} untracked")
    _, stash = git(["stash", "list", "--format=%gs"], repo)
    if branch:
        n = sum(1 for s in stash.splitlines() if s.startswith((f"WIP on {branch}:", f"On {branch}:")))
        if n:
            reasons.append(f"{n} stash")
    _, sub = git(["submodule", "status"], path)
    if any(l and l[0] != "-" for l in sub.splitlines()):
        reasons.append("initialized submodule")
    if holders is None:
        raise InspectError("holder check unavailable")
    p = str(path)
    held = sum(1 for h in holders if h == p or h.startswith(p + "/"))
    if held:
        rec["class"] = "held"
        ev.append(f"{held} process cwd inside")
        return rec
    if reasons:
        rec["class"] = "dirty"
        ev.extend(reasons)
        return rec
    reach = [r for r in refs if git(["merge-base", "--is-ancestor", branch, r], repo, ok=(0, 1))[0] == 0]
    if reach:
        ev.append("merged into " + ",".join(reach))
    else:
        _, track = git(["for-each-ref", "--format=%(upstream:track)", f"refs/heads/{branch}"], repo)
        _, remote = git(["branch", "-r", "--format=%(refname:short)", "--contains", branch], repo)
        live = [r for r in remote.splitlines() if r and not r.endswith("/HEAD")]
        if live and "gone" not in track:
            ev.append("pushed to " + live[0])
        else:
            rec["class"] = "unreachable"
            ev.append("commits not on any durable ref")
            return rec
    _, cd = git(["log", "-1", "--format=%ct", branch], repo)
    if not cd.isdigit():
        raise InspectError("commit date unavailable")
    age = int((time.time() - int(cd)) / 86400)
    rec["age_days"] = age
    ev.append(f"last commit {age}d")
    if age < stale_days or recent_activity(path, stale_days):
        rec["class"] = "recent"
        ev.append(f"activity within {stale_days}d")
        return rec
    rec["ignored"] = sorted(ignored)
    if ignored:
        if conventional_only(path, ignored):
            rec["class"] = "ignored-conventional"
            ev.append(f"clean; {len(ignored)} ignored conventional output dirs (not regeneration proof)")
        else:
            rec["class"] = "ignored-other"
            ev.append(f"{len(ignored)} ignored paths, some not conventional output dirs")
        return rec
    rec["class"] = "safe"
    ev.append("clean; no ignored files")
    return rec


def kind_for(path, agent_roots):
    for root in agent_roots:
        r = str(Path(root).expanduser().resolve())
        if str(path).startswith(r + "/"):
            return "agent"
    return "code"


def scan_repos(repos, *, agent_roots, patterns, stale_days, measure, only_paths=None, holders_cmd=None):
    holders = cwd_holders(holders_cmd)
    records, errors = [], []
    principals = {str(r) for r in repos}
    for repo in repos:
        try:
            _, out = git(["worktree", "list", "--porcelain", "-z"], repo)
            refs = integration_refs(repo, patterns)
        except InspectError as exc:
            errors.append({"repo": str(repo), "error": str(exc)})
            continue
        for i, wt in enumerate(parse_worktrees(out)):
            p = wt.get("worktree")
            if i == 0 or not p or p in principals:
                continue
            if only_paths is not None and p not in only_paths:
                continue
            rec = classify(repo, wt, refs=refs, stale_days=stale_days, holders=holders, measure=measure)
            rec["kind"] = kind_for(p, agent_roots)
            records.append(rec)
    return records, errors


def _write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)


IDENTITY = ("repo", "common_dir", "path", "branch", "head", "class", "ignored")


def manifest_text(records, settings):
    """JSON Lines: a settings header, then one target per line. Lossless for any path."""
    # Sorted so that each class/kind/repo group is a contiguous ID range.
    rows = sorted(records, key=lambda r: (CLASSES.index(r["class"]), r["kind"], r["repo"], -(r["kb"] or 0), r["path"]))
    lines = [json.dumps({"schema": MANIFEST_SCHEMA, "settings": settings}, sort_keys=True)]
    for n, r in enumerate(rows, 1):
        r["row"] = n
        lines.append(json.dumps({k: r.get(k) for k in ("row", "kind", "kb", "evidence", *IDENTITY)}, sort_keys=True))
    return rows, "\n".join(lines) + "\n"


def read_manifest(path):
    text = Path(path).read_text()
    try:
        lines = [json.loads(l) for l in text.splitlines()]
    except ValueError:
        raise SystemExit("malformed manifest")
    if not lines or lines[0].get("schema") != MANIFEST_SCHEMA or not isinstance(lines[0].get("settings"), dict):
        raise SystemExit(f"unexpected manifest header in {path}")
    rows, seen_rows, seen_paths = [], set(), set()
    for r in lines[1:]:
        if not isinstance(r.get("row"), int) or any(k not in r for k in IDENTITY):
            raise SystemExit("malformed manifest row")
        if r["row"] in seen_rows or r["path"] in seen_paths:
            raise SystemExit("duplicate manifest row or path")
        seen_rows.add(r["row"]); seen_paths.add(r["path"])
        rows.append(r)
    return lines[0]["settings"], rows, hashlib.sha256(text.encode()).hexdigest()


def summarize(records):
    out = {}
    for r in records:
        s = out.setdefault(r["class"], {"count": 0, "kb": 0})
        s["count"] += 1
        s["kb"] += max(r["kb"] or 0, 0)
    return out


def parse_rows(spec):
    rows = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            rows.update(range(int(a), int(b) + 1))
        elif part:
            rows.add(int(part))
    return rows


def new_run_dir(out):
    if out:
        p = Path(out).expanduser()
        p.mkdir(mode=0o700, parents=True, exist_ok=True)
        if any(p.iterdir()):
            raise SystemExit(f"refusing to reuse non-empty run directory {p}")
        os.chmod(p, 0o700)
        return p
    return Path(tempfile.mkdtemp(prefix="cleanup-machine-"))  # 0700, unique


def cmd_scan(a, holders_cmd=None):
    agent_roots = [str(Path(x).expanduser()) for x in a.agent_root]
    discovery_errors = []
    repos = sorted(set(find_repos(a.root, a.depth, discovery_errors))
                   | set(repos_from_agent_roots(agent_roots, discovery_errors)))
    records, errors = scan_repos(repos, agent_roots=agent_roots, patterns=a.integration,
                                 stale_days=a.stale_days, measure=not a.no_size, holders_cmd=holders_cmd)
    errors = discovery_errors + errors
    run = new_run_dir(a.out)
    settings = {"roots": a.root, "depth": a.depth, "agent_roots": agent_roots,
                "integration": a.integration, "stale_days": a.stale_days, "scanned_at": int(time.time())}
    rows, text = manifest_text(records, settings)
    digest = hashlib.sha256(text.encode()).hexdigest()
    _write_private(run / "manifest.jsonl", text)
    inv = {"note": "informational; manifest.jsonl is the approval authority", "manifest_sha256": digest,
           "repos": [str(x) for x in repos], "errors": errors, "summary": summarize(rows), "worktrees": rows}
    _write_private(run / "inventory.json", json.dumps(inv, indent=1))
    print(json.dumps({"run": str(run), "digest": digest, "repos": len(repos), "worktrees": len(rows),
                      "errors": errors, "summary": inv["summary"]}, indent=1))
    return 0


def cmd_recheck(a, holders_cmd=None):
    run = Path(a.run).expanduser()
    s, rows, digest = read_manifest(run / "manifest.jsonl")
    if digest != a.digest:
        raise SystemExit("manifest digest does not match the approved report; run a new scan")
    wanted = parse_rows(a.rows)
    known = {r["row"] for r in rows}
    if wanted - known:
        raise SystemExit(f"rows not in manifest: {sorted(wanted - known)}")
    chosen = [r for r in rows if r["row"] in wanted]
    rejected = [r["row"] for r in chosen
                if r["class"] not in EXECUTABLE or (EXECUTABLE[r["class"]] and not a.approve_ignored)]
    by_path = {r["path"]: r for r in chosen if r["row"] not in rejected}
    repos = sorted({Path(r["repo"]) for r in by_path.values()})
    records, errors = scan_repos(repos, agent_roots=s["agent_roots"], patterns=s["integration"],
                                 stale_days=s["stale_days"], measure=False, only_paths=set(by_path),
                                 holders_cmd=holders_cmd)
    seen = {r["path"]: r for r in records}
    result = []
    for p, m in by_path.items():
        now = seen.get(p)
        if now is None:
            status, why = "gone", "not registered in its repository"
        else:
            diff = [k for k in IDENTITY if (now.get(k) or None) != (m.get(k) or None)]
            status, why = ("changed", "differs from report: " + ",".join(diff)) if diff else ("still-safe", "")
        result.append({"row": m["row"], "path": p, "repo": m["repo"], "branch": m["branch"], "kind": m["kind"],
                       "class": m["class"], "approved_ignored": m["ignored"],
                       "current_ignored": None if now is None else now["ignored"],
                       "status": status, "reason": why, "evidence": None if now is None else now["evidence"]})
    print(json.dumps({"digest": digest, "rejected": rejected, "errors": errors,
                      "targets": sorted(result, key=lambda x: x["row"])}, indent=1))
    return 0


def main(argv=None, holders_cmd=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="inventory and classify; writes a new private run directory")
    s.add_argument("--root", action="append", required=True, help="code root (repeatable)")
    s.add_argument("--depth", type=int, default=3)
    s.add_argument("--agent-root", action="append", default=[], help="agent-managed worktree root (repeatable)")
    s.add_argument("--integration", action="append", default=[],
                   help="user-confirmed integration ref or glob, e.g. origin/integration-70.2 (repeatable)")
    s.add_argument("--stale-days", type=int, default=14)
    s.add_argument("--no-size", action="store_true", help="skip du (faster)")
    s.add_argument("--out", help="new or empty run directory (default: a unique private temp dir)")
    r = sub.add_parser("recheck", help="revalidate approved manifest rows with the scan's own settings")
    r.add_argument("--run", required=True, help="run directory printed by scan")
    r.add_argument("--digest", required=True, help="manifest digest printed by scan and shown in the report")
    r.add_argument("--rows", required=True, help="approved manifest row IDs, e.g. 1-4,7")
    r.add_argument("--approve-ignored", action="store_true",
                   help="the user approved losing the listed ignored paths of ignored-conventional rows")
    a = ap.parse_args(argv)
    return cmd_scan(a, holders_cmd) if a.cmd == "scan" else cmd_recheck(a, holders_cmd)


if __name__ == "__main__":
    sys.exit(main())
