"""Offline tests for cleanup_inventory.py. Uses throwaway Git repositories in a temp dir.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/cleanup-machine/tests -v
"""

import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cleanup_inventory as ci  # noqa: E402

OLD = time.time() - 60 * 86400
OLD_DATE = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(OLD))
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


def sh(*args, cwd, env=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, env=dict(os.environ, **GIT_ENV, **(env or {})))


def commit(cwd, name, old=True, msg=None, content=None):
    Path(cwd, name).parent.mkdir(parents=True, exist_ok=True)
    Path(cwd, name).write_text(content or name)
    sh("git", "add", name, cwd=cwd)
    env = {"GIT_AUTHOR_DATE": OLD_DATE, "GIT_COMMITTER_DATE": OLD_DATE} if old else {}
    sh("git", "commit", "-qm", msg or name, cwd=cwd, env=env)


def age_tree(path):
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            os.utime(os.path.join(dirpath, f), (OLD, OLD))


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.code = self.tmp / "Code"
        self.agent = self.tmp / "agent-worktrees"
        self.remote = self.tmp / "remote.git"
        self.repo = self.code / "group" / "app"      # nested: depth 2
        self.repo.mkdir(parents=True)
        self.agent.mkdir()
        sh("git", "init", "-q", "--bare", "-b", "main", str(self.remote), cwd=self.tmp)
        sh("git", "init", "-q", "-b", "main", cwd=self.repo)
        Path(self.repo, ".gitignore").write_text("node_modules/\nenv.local\n*.log\n")
        sh("git", "add", ".gitignore", cwd=self.repo)
        commit(self.repo, "base")
        sh("git", "remote", "add", "origin", str(self.remote), cwd=self.repo)
        sh("git", "push", "-q", "origin", "main", cwd=self.repo)
        sh("git", "remote", "set-head", "origin", "main", cwd=self.repo)
        self.holders = set()
        self._orig_holders = ci.cwd_holders
        ci.cwd_holders = lambda cmd=None: set(self.holders)
        self.run_n = 0

    def tearDown(self):
        ci.cwd_holders = self._orig_holders
        self._tmp.cleanup()

    def worktree(self, branch, where=None, base="main"):
        path = where or (self.code / "group" / f"app.{branch}")
        path.parent.mkdir(parents=True, exist_ok=True)
        sh("git", "worktree", "add", "-q", "-b", branch, str(path), base, cwd=self.repo)
        return path

    def merged(self, branch, **kw):
        """Old worktree whose branch is merged into origin/main."""
        p = self.worktree(branch, **kw)
        commit(p, f"{branch}.txt")
        sh("git", "push", "-q", "origin", f"{branch}:main", cwd=p)
        sh("git", "fetch", "-q", "origin", cwd=self.repo)
        sh("git", "merge", "-q", "--ff-only", "origin/main", cwd=self.repo)
        age_tree(p)
        return p

    def scan(self, **kw):
        self.run_n += 1
        out = self.tmp / f"run{self.run_n}"
        args = ["scan", "--root", str(self.code), "--agent-root", str(self.agent), "--out", str(out), "--no-size"]
        for k, v in kw.items():
            args += [f"--{k.replace('_', '-')}", str(v)]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ci.main(args)
        res = json.loads(buf.getvalue())
        inv = json.loads((out / "inventory.json").read_text())
        return out, res["digest"], {Path(w["path"]).name: w for w in inv["worktrees"]}

    def recheck(self, out, digest, rows, approve_ignored=False):
        buf = io.StringIO()
        args = ["recheck", "--run", str(out), "--digest", digest, "--rows", rows]
        with contextlib.redirect_stdout(buf):
            ci.main(args + (["--approve-ignored"] if approve_ignored else []))
        return json.loads(buf.getvalue())


class ScanTests(Fixture):
    def test_merged_old_clean_worktree_without_ignored_files_is_safe(self):
        self.merged("feat")
        _, _, w = self.scan()
        self.assertEqual(w["app.feat"]["class"], "safe")
        self.assertIn("merged into origin/main", "; ".join(w["app.feat"]["evidence"]))

    def test_conventional_output_dirs_are_never_plain_safe(self):
        a = self.merged("nm")
        Path(a, "node_modules").mkdir()
        Path(a, "node_modules", "x.js").write_text("x")
        b = self.merged("distfile")
        Path(b, "dist").write_text("unique data in a plain file named dist")
        c = self.merged("distlink")
        os.symlink(self.tmp, Path(c, "dist"))
        for p in (a, b, c):
            age_tree(p)
        Path(self.repo, ".gitignore").write_text("node_modules/\nenv.local\n*.log\ndist\n")
        for p in (b, c):
            sh("git", "config", "core.excludesFile", str(self.repo / ".gitignore"), cwd=p)
        _, _, w = self.scan()
        self.assertEqual(w["app.nm"]["class"], "ignored-conventional")
        self.assertEqual(w["app.nm"]["ignored"], ["node_modules"])
        self.assertEqual(w["app.distfile"]["class"], "ignored-other")
        self.assertEqual(w["app.distlink"]["class"], "ignored-other")

    def test_other_ignored_data_blocks_including_logs(self):
        a = self.merged("env")
        Path(a, "env.local").write_text("SECRET=1")
        b = self.merged("log")
        Path(b, "audit.log").write_text("keep me")
        age_tree(a), age_tree(b)
        _, _, w = self.scan()
        self.assertEqual(w["app.env"]["class"], "ignored-other")
        self.assertEqual(w["app.env"]["ignored"], ["env.local"])
        self.assertEqual(w["app.log"]["class"], "ignored-other")

    def test_recent_commit_or_file_is_recent(self):
        p = self.worktree("fresh")
        commit(p, "fresh.txt", old=False)
        sh("git", "push", "-q", "origin", "fresh", cwd=p)
        q = self.merged("touched")
        Path(q, "base").touch()
        _, _, w = self.scan()
        self.assertEqual(w["app.fresh"]["class"], "recent")
        self.assertEqual(w["app.touched"]["class"], "recent")

    def test_dirty_untracked_stash_lock_detached_block(self):
        a = self.merged("mod")
        Path(a, "base").write_text("changed")
        b = self.merged("new")
        Path(b, "scratch file.txt").write_text("x")
        c = self.merged("stashed")
        Path(c, "base").write_text("wip")
        sh("git", "stash", "-q", cwd=c)
        age_tree(c)
        d = self.merged("locked")
        sh("git", "worktree", "lock", str(d), cwd=self.repo)
        e = self.code / "group" / "app.detached"
        sh("git", "worktree", "add", "-q", "--detach", str(e), "main", cwd=self.repo)
        age_tree(e)
        _, _, w = self.scan()
        for name in ("app.mod", "app.new", "app.stashed", "app.locked", "app.detached"):
            self.assertEqual(w[name]["class"], "dirty", name)
        self.assertIn("1 stash", w["app.stashed"]["evidence"])
        self.assertIn("locked", w["app.locked"]["evidence"])
        self.assertIn("detached HEAD", w["app.detached"]["evidence"])

    def test_rename_is_dirty(self):
        p = self.merged("ren")
        sh("git", "mv", "base", "renamed base", cwd=p)
        _, _, w = self.scan()
        self.assertEqual(w["app.ren"]["class"], "dirty")
        self.assertIn("1 changed", w["app.ren"]["evidence"])

    def test_unique_unpushed_commit_is_unreachable(self):
        p = self.worktree("local-only")
        commit(p, "mine.txt")
        age_tree(p)
        _, _, w = self.scan()
        self.assertEqual(w["app.local-only"]["class"], "unreachable")

    def test_pushed_branch_is_reachable_until_remote_branch_is_gone(self):
        p = self.worktree("pushed")
        commit(p, "p.txt")
        sh("git", "push", "-q", "-u", "origin", "pushed", cwd=p)
        age_tree(p)
        _, _, w = self.scan()
        self.assertEqual(w["app.pushed"]["class"], "safe")
        sh("git", "push", "-q", "origin", "--delete", "pushed", cwd=p)
        sh("git", "fetch", "-q", "--prune", "origin", cwd=self.repo)
        _, _, w = self.scan()
        self.assertEqual(w["app.pushed"]["class"], "unreachable")

    def test_squash_merged_branch_is_not_treated_as_merged(self):
        p = self.worktree("squashed")
        commit(p, "s.txt")
        age_tree(p)
        commit(self.repo, "s.txt", msg="squash of #1")
        sh("git", "push", "-q", "origin", "main", cwd=self.repo)
        _, _, w = self.scan()
        self.assertEqual(w["app.squashed"]["class"], "unreachable")

    def test_held_and_prunable(self):
        held = self.merged("held")
        gone = self.merged("gone")
        self.holders = {str(held / "sub")}
        shutil.rmtree(gone)
        _, _, w = self.scan()
        self.assertEqual(w["app.held"]["class"], "held")
        self.assertEqual(w["app.gone"]["class"], "prunable")

    def test_failed_holder_inspection_is_error(self):
        self.merged("blind")
        ci.cwd_holders = self._orig_holders
        self.assertIsNone(ci.cwd_holders(["false"]))            # nonzero exit
        self.assertIsNone(ci.cwd_holders(["/nonexistent/lsof"]))  # cannot run
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ci.main(["scan", "--root", str(self.code), "--out", str(self.tmp / "r"), "--no-size"], holders_cmd=["false"])
        inv = json.loads((self.tmp / "r" / "inventory.json").read_text())
        self.assertEqual([w["class"] for w in inv["worktrees"]], ["error"])

    def test_failed_git_inspection_is_error_not_reachable(self):
        p = self.worktree("unpushed")
        commit(p, "u.txt")
        age_tree(p)
        real = ci.git

        def flaky(args, cwd, timeout=120, ok=(0,)):
            if args[:2] == ["branch", "-r"]:
                raise ci.InspectError("git branch: TimeoutExpired")
            return real(args, cwd, timeout, ok)
        ci.git = flaky
        try:
            _, _, w = self.scan()
        finally:
            ci.git = real
        self.assertEqual(w["app.unpushed"]["class"], "error")

    def test_explicit_integration_ref_counts_as_merged(self):
        p = self.worktree("feature")
        commit(p, "f.txt")
        sh("git", "push", "-q", "origin", "feature:integration-1.1", cwd=p)
        sh("git", "fetch", "-q", "origin", cwd=self.repo)
        age_tree(p)
        _, _, w = self.scan(integration="origin/integration-1.1")
        self.assertIn("merged into origin/integration-1.1", "; ".join(w["app.feature"]["evidence"]))

    def test_depth_limits_discovery_and_agent_roots_find_nested_owner(self):
        self.merged("agentwt", where=self.agent / "app" / "agentwt")
        _, _, w = self.scan(depth=0)
        self.assertIn("agentwt", w)
        self.assertEqual(w["agentwt"]["kind"], "agent")
        self.assertEqual(ci.find_repos([self.code], 1), [])
        self.assertEqual(ci.find_repos([self.code], 2), [self.repo])

    def test_control_character_path_is_error(self):
        self.merged("tab", where=self.code / "group" / "app\ttab")
        _, _, w = self.scan()
        self.assertEqual(w["app\ttab"]["class"], "error")

    def test_discovery_errors_are_reported(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ci.main(["scan", "--root", str(self.tmp / "missing"), "--out", str(self.tmp / "r"), "--no-size"])
        self.assertTrue(json.loads(buf.getvalue())["errors"])

    def test_scan_does_not_write_repository_state(self):
        p = self.merged("ro")
        Path(p, "base").touch()  # stat change that would normally make git status refresh the index
        gitdir = Path(subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=p, capture_output=True,
                                     text=True).stdout.strip())
        index = gitdir / "index"
        before = (index.read_bytes(), index.stat().st_mtime_ns)
        refs = subprocess.run(["git", "for-each-ref"], cwd=self.repo, capture_output=True, text=True).stdout
        wts = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=self.repo,
                             capture_output=True, text=True).stdout
        self.scan()
        self.assertTrue(p.is_dir())
        self.assertEqual(before, (index.read_bytes(), index.stat().st_mtime_ns))
        self.assertEqual(refs, subprocess.run(["git", "for-each-ref"], cwd=self.repo,
                                              capture_output=True, text=True).stdout)
        self.assertEqual(wts, subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=self.repo,
                                             capture_output=True, text=True).stdout)

    def test_run_directory_is_private_unique_and_not_reused(self):
        self.merged("x")
        out, _, _ = self.scan()
        self.assertEqual(stat.S_IMODE(out.stat().st_mode), 0o700)
        for f in ("manifest.jsonl", "inventory.json"):
            self.assertEqual(stat.S_IMODE((out / f).stat().st_mode), 0o600)
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(io.StringIO()):
                ci.main(["scan", "--root", str(self.code), "--out", str(out), "--no-size"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ci.main(["scan", "--root", str(self.code), "--no-size"])  # default: fresh temp dir
        run = Path(json.loads(buf.getvalue())["run"])
        self.assertEqual(stat.S_IMODE(run.stat().st_mode), 0o700)
        shutil.rmtree(run)


class RecheckTests(Fixture):
    def test_recheck_only_covers_approved_rows_and_flags_changes(self):
        a = self.merged("a")
        self.merged("b")
        out, dg, w = self.scan()
        Path(a, "base").write_text("edited after report")
        self.merged("c")                      # newly qualifying target, not in the report
        res = self.recheck(out, dg, f'{w["app.a"]["row"]},{w["app.b"]["row"]}')
        status = {Path(t["path"]).name: t["status"] for t in res["targets"]}
        self.assertEqual(status, {"app.a": "changed", "app.b": "still-safe"})

    def test_recheck_rejects_rows_that_were_not_safe_at_report(self):
        self.merged("ok")
        p = self.worktree("bad")
        commit(p, "x.txt")
        age_tree(p)
        out, dg, w = self.scan()
        res = self.recheck(out, dg, f'{w["app.ok"]["row"]},{w["app.bad"]["row"]}')
        self.assertEqual(res["rejected"], [w["app.bad"]["row"]])
        self.assertEqual([Path(t["path"]).name for t in res["targets"]], ["app.ok"])

    def test_recheck_requires_matching_digest(self):
        self.merged("d")
        out, dg, w = self.scan()
        with self.assertRaises(SystemExit):
            self.recheck(out, "0" * 64, str(w["app.d"]["row"]))

    def test_recheck_rejects_edited_manifest_or_settings(self):
        self.merged("e")
        out, dg, w = self.scan()
        m = out / "manifest.jsonl"
        text = m.read_text()
        m.write_text(text.replace("app.e", "app.f"))
        with self.assertRaises(SystemExit):
            self.recheck(out, dg, str(w["app.e"]["row"]))
        m.write_text(text.replace('"stale_days": 14', '"stale_days": 1'))
        with self.assertRaises(SystemExit):
            self.recheck(out, dg, str(w["app.e"]["row"]))
        (out / "inventory.json").write_text("{}")   # informational only; not an authority
        m.write_text(text)
        self.assertEqual(self.recheck(out, dg, str(w["app.e"]["row"]))["targets"][0]["status"], "still-safe")

    def test_ignored_conventional_needs_explicit_approval_and_frozen_paths(self):
        p = self.merged("nm")
        Path(p, "node_modules").mkdir()
        Path(p, "node_modules", "x.js").write_text("x")
        age_tree(p)
        out, dg, w = self.scan()
        row = str(w["app.nm"]["row"])
        self.assertEqual(self.recheck(out, dg, row)["rejected"], [int(row)])
        res = self.recheck(out, dg, row, approve_ignored=True)
        self.assertEqual(res["targets"][0]["status"], "still-safe")
        Path(self.repo, ".gitignore").write_text("node_modules/\nenv.local\n*.log\ncoverage/\n")
        sh("git", "config", "core.excludesFile", str(self.repo / ".gitignore"), cwd=p)
        Path(p, "coverage").mkdir()
        Path(p, "coverage", "c.txt").write_text("new")
        age_tree(p)
        res = self.recheck(out, dg, row, approve_ignored=True)
        self.assertEqual(res["targets"][0]["status"], "changed")
        self.assertEqual(res["targets"][0]["current_ignored"], ["coverage", "node_modules"])
        self.assertEqual(res["targets"][0]["approved_ignored"], ["node_modules"])

    def test_same_path_with_different_branch_is_changed(self):
        p = self.merged("orig")
        out, dg, w = self.scan()
        sh("git", "worktree", "remove", str(p), cwd=self.repo)
        self.merged("other", where=p)        # another old, clean, reachable branch at the same path
        res = self.recheck(out, dg, str(w["app.orig"]["row"]))
        self.assertEqual(res["targets"][0]["status"], "changed")

    def test_recheck_uses_saved_settings(self):
        p = self.worktree("mid")
        commit(p, "m.txt")
        sh("git", "push", "-q", "origin", "mid:main", cwd=p)
        sh("git", "fetch", "-q", "origin", cwd=self.repo)
        age_tree(p)
        out, dg, w = self.scan(stale_days=30)
        self.assertEqual(w["app.mid"]["class"], "safe")
        t = time.time() - 20 * 86400
        os.utime(p / "base", (t, t))         # 20 days: recent under 30, stale under the default 14
        res = self.recheck(out, dg, str(w["app.mid"]["row"]))
        self.assertEqual(res["targets"][0]["status"], "changed")

    def test_recheck_reports_removed_target_as_gone_and_unknown_rows_fail(self):
        p = self.merged("vanish")
        out, dg, w = self.scan()
        sh("git", "worktree", "remove", str(p), cwd=self.repo)
        res = self.recheck(out, dg, str(w["app.vanish"]["row"]))
        self.assertEqual(res["targets"][0]["status"], "gone")
        with self.assertRaises(SystemExit):
            self.recheck(out, dg, "999")

    def test_parse_rows(self):
        self.assertEqual(ci.parse_rows("1-3, 7"), {1, 2, 3, 7})


if __name__ == "__main__":
    unittest.main()
