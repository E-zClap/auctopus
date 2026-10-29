"""Stages that drive the computational researcher: the first verification task and the PI's review loops."""
from __future__ import annotations

import shutil

from ..state import Blocked
from .chain import Chain


class Verify(Chain):
    """Push the paper package and the PI's computational test design to the HPC and run the first task (05-codex)."""

    def run(self) -> None:
        exp = self.rd / "04-exp-reply.md"
        if not exp.exists():
            raise Blocked("verify: no computational test design (04-exp-reply.md)")
        hs = self.hpc_state
        if not hs.get("dir"):
            t = self.ctx.transport("hpc")
            base = self.cfg.hpc.remote_root
            name = self.choose_remote_name()
            remote = f"{base}/{name}"
            for v in range(2, 10):
                if not t.exists(remote):
                    break
                remote = f"{base}/{name}-v{v}"
            shutil.copyfile(exp, self.ctx.package / "experiment.md")
            t.push_dir(self.ctx.package, remote)
            if not t.exists(f"{remote}/experiment.md"):
                raise Blocked(f"verify: experiment.md did not arrive in {remote}")
            hs["dir"] = remote
            hs["experiments"] = 1
            self.ctx.state.save()
            self.ctx.journal.say(f"verify: package pushed to {remote}")
        self.codex_task("verify", self.ctx.prompt("05-codex.md"))


class ReviewLoop(Chain):
    def __init__(self, ctx, key: str):
        super().__init__(ctx)
        self.key = key

    def run(self) -> None:
        self.review_loop(self.key, self.cfg.chain.max_review_rounds)
