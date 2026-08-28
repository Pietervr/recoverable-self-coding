"""E11 — RSC ingredient curves in PRODUCTION agentic traces (observational).

Data: the local Claude Code session logs of this machine's largest
project (~134 sessions > 100 kB, ~1.6 GB) — genuine operating-loop
traces of an LLM agent doing real engineering work. Analysis is
aggregate-only: no message text is read or retained; only block types,
flags, token counts, and timestamps.

This is NOT a collapse claim. The honest observational question: are
the two measured ingredients that drive collapse in the rig (E4 closure)
present in production?

  I1  error rate vs context: P(tool error) binned by the serving call's
      effective context (usage.input_tokens + cache_read_input_tokens).
      Rig analog: P_err(j) rising 0.05 -> 0.84.
  I2  service time vs context: median seconds from the assistant message
      issuing a tool_use to its tool_result, same bins. Rig analog: the
      measured service law 6.6 -> 25.2 s.
  I3  the feedback kernel: P(error | previous result was error) vs
      P(error | previous ok), per session, pooled.
  I4  cascade sizes: run lengths of consecutive tool errors vs the
      geometric null from each session's own error rate (feedback-free
      expectation); report observed vs expected P(run >= k).

Pre-committed analysis decisions (before any curve was looked at):
  - unit = tool_use -> tool_result pairs, matched by tool_use_id;
  - error = tool_result.is_error == true;
  - context bins: fixed edges 0-20k, ..., >=180k (10 bins of 20k);
  - service censored at 600 s (human walk-aways), reported as censor
    count; sessions with < 50 pairs excluded; sidechains included,
    counted separately;
  - one pass; the first output is the result (no post-hoc tuning).

Run:  python3 e11_production_traces.py   Out: runs/e11_production.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
LOGDIR = Path.home() / ".claude" / "projects" / "-Users-pietervanrooyen-Unimog-Projects"
MIN_PAIRS = 50
SERVICE_CAP = 600.0
BIN_W = 20000
N_BINS = 10


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def scan_session(path: Path):
    """Yield (ctx_tokens, service_s | None, is_error, is_sidechain) per
    tool_use->tool_result pair, in result order."""
    pend = {}          # tool_use_id -> (t_assistant, ctx, sidechain)
    out = []
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = r.get("type")
            if t == "assistant":
                m = r.get("message") or {}
                u = m.get("usage") or {}
                ctx = ((u.get("input_tokens") or 0)
                       + (u.get("cache_read_input_tokens") or 0))
                try:
                    t_a = ts(r["timestamp"])
                except (KeyError, ValueError):
                    t_a = None
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        pend[b.get("id")] = (t_a, ctx,
                                             bool(r.get("isSidechain")))
            elif t == "user":
                m = r.get("message") or {}
                try:
                    t_r = ts(r["timestamp"])
                except (KeyError, ValueError):
                    t_r = None
                content = m.get("content")
                if not isinstance(content, list):
                    continue
                for b in content:
                    if (isinstance(b, dict)
                            and b.get("type") == "tool_result"):
                        info = pend.pop(b.get("tool_use_id"), None)
                        if info is None:
                            continue
                        t_a, ctx, side = info
                        svc = (t_r - t_a if t_a is not None
                               and t_r is not None else None)
                        out.append((ctx, svc, bool(b.get("is_error")),
                                    side))
    return out


def main() -> int:
    files = sorted(LOGDIR.glob("*.jsonl"),
                   key=lambda p: p.stat().st_size, reverse=True)
    err_by_bin = [0] * N_BINS
    n_by_bin = [0] * N_BINS
    svc_by_bin = [[] for _ in range(N_BINS)]
    svc_censored = 0
    kernel = {"after_err": [0, 0], "after_ok": [0, 0]}   # [errors, n]
    run_obs = defaultdict(int)
    run_exp = defaultdict(float)
    n_sessions = n_pairs = n_side = 0

    for p in files:
        pairs = scan_session(p)
        if len(pairs) < MIN_PAIRS:
            continue
        n_sessions += 1
        n_pairs += len(pairs)
        errs = [e for _, _, e, _ in pairs]
        n_side += sum(1 for _, _, _, s in pairs if s)
        for ctx, svc, err, _ in pairs:
            b = min(N_BINS - 1, ctx // BIN_W)
            n_by_bin[b] += 1
            err_by_bin[b] += err
            if svc is not None and 0 <= svc:
                if svc <= SERVICE_CAP:
                    svc_by_bin[b].append(svc)
                else:
                    svc_censored += 1
        for i in range(1, len(errs)):
            k = "after_err" if errs[i - 1] else "after_ok"
            kernel[k][0] += errs[i]
            kernel[k][1] += 1
        # observed error-run lengths + geometric null at session rate
        pe = sum(errs) / len(errs)
        run = 0
        for e in errs + [False]:
            if e:
                run += 1
            elif run:
                run_obs[run] += 1
                run = 0
        n_runs = sum(run_obs.values())
        if 0 < pe < 1:
            exp_runs = len(errs) * pe * (1 - pe)
            for k in range(1, 30):
                run_exp[k] += exp_runs * (pe ** (k - 1)) * (1 - pe)

    def med(xs):
        return round(sorted(xs)[len(xs) // 2], 1) if xs else None

    out = {
        "sessions": n_sessions, "pairs": n_pairs,
        "sidechain_pairs": n_side, "service_censored": svc_censored,
        "bins_ctx_upper": [(i + 1) * BIN_W for i in range(N_BINS)],
        "I1_p_err": [round(err_by_bin[i] / n_by_bin[i], 4)
                     if n_by_bin[i] else None for i in range(N_BINS)],
        "I1_n": n_by_bin,
        "I2_service_median_s": [med(svc_by_bin[i]) for i in range(N_BINS)],
        "I3_p_err_after_err": round(
            kernel["after_err"][0] / kernel["after_err"][1], 4)
        if kernel["after_err"][1] else None,
        "I3_p_err_after_ok": round(
            kernel["after_ok"][0] / kernel["after_ok"][1], 4)
        if kernel["after_ok"][1] else None,
        "I3_n": {k: v[1] for k, v in kernel.items()},
        "I4_run_len_observed": {str(k): run_obs[k]
                                for k in sorted(run_obs)},
        "I4_run_len_geometric_null": {str(k): round(run_exp[k], 1)
                                      for k in sorted(run_exp)
                                      if run_exp[k] >= 0.5},
    }
    print(json.dumps(out, indent=1))
    (HERE / "runs" / "e11_production.json").write_text(
        json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
