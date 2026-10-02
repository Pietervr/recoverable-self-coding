"""Photograph arm, Stage A (ledger row 20): the completeness validator and the report (framework §8.4 (p); R052
brief 2026-10-02 repair 17). Runs as `stage_a.py report` inside A's budget (its own session of the same state file),
after a pass or after a stop; it never runs a forward.

VALIDATOR. Every planned attempt is classed: committed (its outputs re-read and their checksums verified),
failed, interrupted, or never started. The run PASSES only if there is no TERMINAL.json, both phase records exist,
all 178 planned instrumented and native attempts are committed and verified, every bitwise case equals plain, both
suffix-isolation diagnostics hold, the encoder-sensitivity pair differs, and all 20 native rows pass the fixed
tolerances. Anything else is reported as STOPPED with the first terminal reason, never as a partial pass.

REPORT (captures/photo_stage_a/report/): stage_a_report.json (the machine record), STAGE_A_REPORT.md (phase timings,
resource peaks, diagnostic accounting, the figures, the parity table, Stage B's headroom, and the interpretation
section for the author to complete after inspecting the figures), and two SVG figures: relative L2 by layer for
every input, and the maximum absolute E1 logit difference per input against the 0.10 tolerance.

STAGE B HEADROOM (framework §8.4): from WHOLE-STAGE rates, not forward timings - every second of A's own sessions
(loads, preprocessing, forwards, writes, checks, this report; the engineering carry excluded because it is not a
Stage A rate) divided by A's attempts; likewise bytes per attempt. Stage B is admitted only if its planned attempts
at those rates fit row 21's caps with 20 % headroom (predicted x 1.2 <= cap), and A's whole-task memory peak is
under 48 GiB. Row 21's attempt count is its cap (1,856) until its own plan declares fewer.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

B_PLANNED_ATTEMPTS = 1856
HEADROOM = 1.2


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def classify(out: Path, plan: dict, state: dict) -> dict:
    rows = {}
    for a in plan["attempts"]:
        aid = a["id"]
        st = state["attempts"].get(aid, {}).get("status")
        c = state["completed"].get(aid)
        if c:
            bad = [rel for rel, h in c["outputs"].items() if not (out / rel).exists() or _sha(out / rel) != h]
            rows[aid] = {"status": "committed" if not bad else "committed, OUTPUT CORRUPT", "bad": bad,
                         "kind": a["kind"], "phase": a["phase"]}
        else:
            rows[aid] = {"status": st or "never started", "kind": a["kind"], "phase": a["phase"]}
    return rows


def _svg_lines(series: dict[str, list[float]], title: str, ylabel: str, tol: float | None) -> str:
    W, H, L, R, T, B = 760, 380, 60, 20, 30, 40
    vals = [v for s in series.values() for v in s if np.isfinite(v)] + ([tol] if tol else [])
    ymax = max(vals) * 1.1 if vals and max(vals) > 0 else 1.0
    n = max(len(s) for s in series.values()) if series else 1
    X = lambda i: L + (W - L - R) * i / max(n - 1, 1)
    Y = lambda v: T + (H - T - B) * (1 - v / ymax)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" '
             f'font-size="11"><rect width="{W}" height="{H}" fill="white"/>',
             f'<text x="{L}" y="18" font-size="13">{title}</text>',
             f'<line x1="{L}" y1="{H - B}" x2="{W - R}" y2="{H - B}" stroke="black"/>',
             f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H - B}" stroke="black"/>',
             f'<text x="{L - 50}" y="{T + 10}">{ymax:.3g}</text><text x="{L - 20}" y="{H - B}">0</text>',
             f'<text x="{W / 2}" y="{H - 8}">{ylabel}</text>']
    if tol is not None:
        parts.append(f'<line x1="{L}" y1="{Y(tol):.1f}" x2="{W - R}" y2="{Y(tol):.1f}" stroke="red" '
                     f'stroke-dasharray="4,3"/><text x="{W - R - 90}" y="{Y(tol) - 4:.1f}" fill="red">tolerance '
                     f'{tol}</text>')
    for k, s in series.items():
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s))
        parts.append(f'<polyline fill="none" stroke="#3366aa" stroke-opacity="0.6" points="{pts}"><title>{k}'
                     f'</title></polyline>')
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_bars(values: list[float], labels: list[str], title: str, tol: float) -> str:
    W, H, L, B, T = 760, 340, 60, 50, 30
    ymax = max(values + [tol]) * 1.15
    bw = (W - L - 20) / max(len(values), 1)
    Y = lambda v: T + (H - T - B) * (1 - v / ymax)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" '
             f'font-size="10"><rect width="{W}" height="{H}" fill="white"/>',
             f'<text x="{L}" y="18" font-size="13">{title}</text>',
             f'<line x1="{L}" y1="{Y(tol):.1f}" x2="{W - 20}" y2="{Y(tol):.1f}" stroke="red" stroke-dasharray="4,3"/>']
    for i, (v, lab) in enumerate(zip(values, labels)):
        x = L + i * bw
        parts.append(f'<rect x="{x + 2:.1f}" y="{Y(v):.1f}" width="{bw - 4:.1f}" height="{H - B - Y(v):.1f}" '
                     f'fill="#3366aa"/><text x="{x + 2:.1f}" y="{H - B + 14}">{lab}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def build(out: Path, plan: dict, budget) -> dict:
    from enforce import write_atomic, write_json_atomic
    state = budget.state
    rep_dir = out / "report"
    rep_dir.mkdir(parents=True, exist_ok=True)
    terminal = json.loads((out / "TERMINAL.json").read_text()) if (out / "TERMINAL.json").exists() else None
    cls = classify(out, plan, state)
    planned = [a["id"] for a in plan["attempts"]]
    committed = [a for a in planned if cls[a]["status"] == "committed"]
    parity = json.loads((out / "native_parity.json").read_text()) if (out / "native_parity.json").exists() else []
    recs = {}
    for aid in committed:
        p = out / f"passes/{aid}.json"
        recs[aid] = json.loads(p.read_text())
    plain = {r["index"]: r for r in recs.values() if r.get("case") == "plain"}
    bitwise = {aid: (r["residuals_sha256"], r["logits_sha256"], r["image"]["features_sha256"]) ==
               (plain[r["index"]]["residuals_sha256"], plain[r["index"]]["logits_sha256"],
                plain[r["index"]]["image"]["features_sha256"])
               for aid, r in recs.items() if r.get("case") in plan["bitwise_cases"] and r["index"] in plain}
    suffix = {aid: r["residuals_sha256"] == plain[r["index"]]["residuals_sha256"]
              for aid, r in recs.items() if r.get("case") == "suffix_isolation" and r["index"] in plain}
    enc_pair = plan["diagnostics"]["encoder_sensitivity"]["pair"]
    enc = (all(i in plain for i in enc_pair) and
           plain[enc_pair[0]]["image"]["features_sha256"] != plain[enc_pair[1]]["image"]["features_sha256"])
    passed = (terminal is None and (out / "INSTRUMENTED_DONE.json").exists() and (out / "NATIVE_DONE.json").exists()
              and len(committed) == len(planned) and all(bitwise.values()) and len(bitwise) == 6 * 20
              and all(suffix.values()) and len(suffix) == 2 and enc and len(parity) == 20
              and all(r["pass"] for r in parity))
    # phase timings (A's own sessions; the engineering carry is listed apart)
    sessions = state["sessions"] + ([state["open_session"]] if state.get("open_session") else [])
    by_phase: dict[str, float] = {}
    for s in sessions:
        by_phase[s["phase"]] = by_phase.get(s["phase"], 0.0) + float(s.get("charged_seconds", s["live_seconds"]))
    carry = state.get("carry_in", {}).get("row20", {})
    a_seconds = sum(by_phase.values())
    a_attempts = sum(1 for a in planned if cls[a]["status"] != "never started")
    out_bytes = budget.used_bytes()
    rate_s = a_seconds / a_attempts if a_attempts else None
    rate_b = out_bytes / a_attempts if a_attempts else None
    caps = state["caps"]["row21"]
    b = None
    if rate_s is not None:
        pred_s, pred_b = rate_s * B_PLANNED_ATTEMPTS, rate_b * B_PLANNED_ATTEMPTS
        b = {"planned_attempts": B_PLANNED_ATTEMPTS, "seconds_per_attempt_whole_stage": rate_s,
             "bytes_per_attempt": rate_b, "predicted_seconds": pred_s, "predicted_bytes": pred_b,
             "time_ok_with_20pct": pred_s * HEADROOM <= caps["seconds"],
             "storage_ok_with_20pct": pred_b * HEADROOM <= caps["bytes"],
             "memory_ok": state["peaks"]["enforced"] <= state["memory_cap"]}
        b["admitted"] = bool(passed and b["time_ok_with_20pct"] and b["storage_ok_with_20pct"] and b["memory_ok"])
    kinds: dict[str, dict] = {}
    for a in plan["attempts"]:
        k = kinds.setdefault(a["kind"], {"planned": 0, "committed": 0, "failed": 0, "interrupted": 0,
                                         "never started": 0})
        k["planned"] += 1
        st = cls[a["id"]]["status"]
        key = ("committed" if st == "committed" else "interrupted" if st.startswith("interrupted")
               else "never started" if st == "never started" else "failed")
        k[key] += 1
    record = {"outcome": "PASS" if passed else "STOPPED", "terminal": terminal,
              "counters_row20": state["counters"]["row20"], "counters_aggregate": state["counters"]["aggregate"],
              "engineering_carry": carry, "phase_seconds": by_phase, "stage_a_seconds": a_seconds,
              "peaks": state["peaks"], "final_bytes": state.get("final_bytes"), "attempts_by_kind": kinds,
              "attempts": cls, "bitwise_equal_to_plain": bitwise, "suffix_isolation": suffix,
              "encoder_sensitivity": {"pair": enc_pair, "features_differ": enc}, "native_parity": parity,
              "stage_b": b, "recovered_sessions": state.get("recovered_sessions", []),
              "interrupted": state.get("interrupted", []), "authorised_recoveries": state.get("authorised_recoveries")}
    figs = {}
    if parity:
        figs["rel_l2_by_layer.svg"] = _svg_lines({f"input {r['index']}": r["rel_l2_by_layer"] for r in parity},
                                                 "Relative L2 (instrumented vs native), marker rows, by layer",
                                                 "layer 0-63", 0.01)
        figs["logit_max_abs.svg"] = _svg_bars([r["logit_max_abs"] for r in parity], [str(r["index"]) for r in parity],
                                              "Max |E1 logit difference| per input (tolerance 0.10)", 0.10)
    for name, svg in figs.items():
        write_atomic(rep_dir / name, svg.encode())
    write_json_atomic(rep_dir / "stage_a_report.json", record)
    md = render_md(record, plan, sorted(figs))
    write_atomic(rep_dir / "STAGE_A_REPORT.md", md.encode())
    required = ["stage_a_report.json", "STAGE_A_REPORT.md"] + (["rel_l2_by_layer.svg", "logit_max_abs.svg"]
                                                               if passed else [])
    record_complete = all((rep_dir / f).exists() for f in required)
    return {"outcome": record["outcome"], "report_files_complete": record_complete, "dir": str(rep_dir)}


def render_md(r: dict, plan: dict, figs: list[str]) -> str:
    L = [f"# Stage A (ledger row 20) report — outcome: {r['outcome']}", "",
         "Generated by `stage_a.py report` (stage_a_report.py). The interpretation section is the author's, written "
         "after inspecting the figures; nothing else here is edited by hand.", ""]
    if r["terminal"]:
        L += [f"**Terminal stop:** {r['terminal']['first']['phase']}: {r['terminal']['first']['reason']}", ""]
    L += ["## Counters", "", "| | started | completed | failed | passes | seconds |", "|---|---|---|---|---|---|"]
    for k in ("counters_row20", "counters_aggregate"):
        c = r[k]
        L.append(f"| {k[9:]} | {c['started']} | {c['completed']} | {c['failed']} | {c['passes']} | {c['seconds']:.1f} |")
    L += ["", f"Engineering carried in: {r['engineering_carry'].get('passes')} attempts, "
              f"{r['engineering_carry'].get('seconds')} s ({r['engineering_carry'].get('measured_seconds')} s measured "
              f"+ {r['engineering_carry'].get('allowance_seconds')} s allowance).", "",
          "## Phase timings (whole-stage, A's own sessions)", ""]
    L += [f"- {p}: {s:.1f} s" for p, s in r["phase_seconds"].items()] + [f"- total: {r['stage_a_seconds']:.1f} s", ""]
    pk = r["peaks"]
    L += ["## Resource peaks", "", f"- enforced task memory peak: {pk['enforced'] / 2**30:.2f} GiB (cap 48 GiB); by "
          f"phase: " + ", ".join(f"{k} {v / 2**30:.2f} GiB" for k, v in pk.get("by_phase", {}).items()),
          f"- phys_footprint peak {pk['phys_footprint'] / 2**30:.2f} GiB; MLX peak {pk['mlx_peak'] / 2**30:.2f} GiB",
          f"- task storage peak {pk['output_bytes'] / 2**20:.1f} MiB; final {r['final_bytes']}", "",
          "## Attempt accounting", "", "| kind | planned | committed | failed | interrupted | never started |",
          "|---|---|---|---|---|---|"]
    for k, v in r["attempts_by_kind"].items():
        L.append(f"| {k} | {v['planned']} | {v['committed']} | {v['failed']} | {v['interrupted']} | "
                 f"{v['never started']} |")
    L += ["", "## Checks", "", f"- bitwise cases equal to plain: {sum(r['bitwise_equal_to_plain'].values())} of "
          f"{len(r['bitwise_equal_to_plain'])}", f"- future-suffix isolation: {r['suffix_isolation']}",
          f"- encoder sensitivity: {r['encoder_sensitivity']}", "", "## Native parity", "",
          "| input | rel L2 max | layer | logit max abs | argmax equal | pass |", "|---|---|---|---|---|---|"]
    for p in r["native_parity"]:
        L.append(f"| {p['index']} | {p['rel_l2_max']:.3g} | {p['rel_l2_argmax_layer']} | {p['logit_max_abs']:.3g} | "
                 f"{p['argmax_equal']} | {p['pass']} |")
    L += ["", "## Figures", ""] + [f"![{f}]({f})" for f in figs]
    L += ["", "## Stage B headroom (whole-stage rates)", "", "```", json.dumps(r["stage_b"], indent=1), "```", "",
          "## Interpretation (author, after inspecting the figures)", "",
          "- What the pass or stop establishes about the instrument's fidelity on these 20 DEV-CAL inputs:",
          "- The logit differences against the fixed 0.10 tolerance, reported unexplained unless attributed by a "
          "declared, counted comparison:",
          "- What it does not establish (semantics, recognition, any mixture or intervention effect; precision for "
          "later target-minus-foil contrasts):", "- Anomalies seen in the figures:", ""]
    return "\n".join(L)
