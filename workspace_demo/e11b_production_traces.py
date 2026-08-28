"""E11b — corrected pass on the production traces (designed AFTER seeing
pass 1's two design errors, committed BEFORE running; e11 pass-1 results
stand as committed in runs/e11_production.json).

Corrections:
  I2' service law = LLM STEP LATENCY: for every assistant record that
      directly follows a tool_result record in the same session file
      (uuid chain: assistant.parentUuid == that user record's uuid),
      latency = t(assistant) - t(user tool_result). This is the
      generation time given context — the rig's service-law analog.
      Binned by the assistant call's effective context (input_tokens +
      cache_read_input_tokens), fixed edges as pass 1. Censor > 300 s
      (user walk-aways between turns are excluded by the parentUuid
      condition, but keep the cap as a guard).
  I1' error-vs-progression WITHIN sessions: per qualifying session
      (>= 50 pairs), pair index normalized to [0,1); pooled P(error) per
      progression decile, plus the per-session late-minus-early
      difference (second half - first half) with a sign count.

Pre-committed decisions: same session set as pass 1 (>= 50 pairs);
one pass; first output = the result.

Run:  python3 e11b_production_traces.py  Out: runs/e11b_production.json
"""

from __future__ import annotations

import json
from pathlib import Path

from e11_production_traces import LOGDIR, MIN_PAIRS, ts, scan_session

HERE = Path(__file__).parent
BIN_W = 20000
N_BINS = 10
LAT_CAP = 300.0


def scan_latencies(path: Path):
    """(ctx, latency_s) for assistant records that directly follow a
    tool_result-bearing user record (parentUuid chain)."""
    import json as _json
    last_user = {}          # uuid -> (t, had_tool_result)
    out = []
    with open(path) as f:
        for line in f:
            try:
                r = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            t = r.get("type")
            if t == "user":
                m = r.get("message") or {}
                content = m.get("content")
                has_tr = (isinstance(content, list)
                          and any(isinstance(b, dict)
                                  and b.get("type") == "tool_result"
                                  for b in content))
                try:
                    last_user[r.get("uuid")] = (ts(r["timestamp"]), has_tr)
                except (KeyError, ValueError):
                    pass
            elif t == "assistant":
                info = last_user.get(r.get("parentUuid"))
                if not info or not info[1]:
                    continue
                m = r.get("message") or {}
                u = m.get("usage") or {}
                ctx = ((u.get("input_tokens") or 0)
                       + (u.get("cache_read_input_tokens") or 0))
                try:
                    lat = ts(r["timestamp"]) - info[0]
                except (KeyError, ValueError):
                    continue
                if 0 <= lat <= LAT_CAP:
                    out.append((ctx, lat))
    return out


def main() -> int:
    files = sorted(LOGDIR.glob("*.jsonl"),
                   key=lambda p: p.stat().st_size, reverse=True)
    lat_by_bin = [[] for _ in range(N_BINS)]
    dec_err = [0] * 10
    dec_n = [0] * 10
    diffs = []
    n_sessions = 0
    for p in files:
        pairs = scan_session(p)
        if len(pairs) < MIN_PAIRS:
            continue
        n_sessions += 1
        n = len(pairs)
        errs = [e for _, _, e, _ in pairs]
        for i, e in enumerate(errs):
            d = min(9, int(10 * i / n))
            dec_n[d] += 1
            dec_err[d] += e
        half = n // 2
        p_early = sum(errs[:half]) / half
        p_late = sum(errs[half:]) / (n - half)
        diffs.append(round(p_late - p_early, 4))
        for ctx, lat in scan_latencies(p):
            b = min(N_BINS - 1, ctx // BIN_W)
            lat_by_bin[b].append(lat)

    def med(xs):
        return round(sorted(xs)[len(xs) // 2], 1) if xs else None

    out = {
        "sessions": n_sessions,
        "bins_ctx_upper": [(i + 1) * BIN_W for i in range(N_BINS)],
        "I2p_llm_latency_median_s": [med(b) for b in lat_by_bin],
        "I2p_n": [len(b) for b in lat_by_bin],
        "I1p_p_err_by_progression_decile": [
            round(dec_err[i] / dec_n[i], 4) if dec_n[i] else None
            for i in range(10)],
        "I1p_n_by_decile": dec_n,
        "I1p_late_minus_early_per_session": diffs,
        "I1p_sign_count_positive": sum(d > 0 for d in diffs),
    }
    print(json.dumps(out, indent=1))
    (HERE / "runs" / "e11b_production.json").write_text(
        json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
