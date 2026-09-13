"""Grid-point selection for the cloud runner (13 Sept 2026; Codex's allocation for the reference bank).

POINTS="M2S:omega=2.0,M2S:omega=1.0" names points of the declared simulation grid. select_points keeps exactly those,
in the grid's own order; a named point that is not in the grid is an error (a typo must never become a silent empty
run), and an empty selection is an error. Dataset seeds are per (point, rep), so filtering leaves every kept point's
dataset identities unchanged. Pure functions, no project imports: uploaded with the job (launch_t1.CODE_FILES)."""


def parse_points(spec: str) -> list:
    """'M2S:omega=2.0,M2H:tau=0.5,M2B' -> [('M2S', {'omega': 2.0}), ('M2H', {'tau': 0.5}), ('M2B', {})]."""
    out = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        name, _, kv = item.partition(":")
        kw = {}
        for pair in filter(None, kv.split(";")):
            k, _, v = pair.partition("=")
            if not k.strip() or not v.strip():
                raise SystemExit(f"POINTS: cannot parse '{item}'")
            kw[k.strip()] = float(v)
        if not name.strip():
            raise SystemExit(f"POINTS: cannot parse '{item}'")
        out.append((name.strip(), kw))
    if not out:
        raise SystemExit("POINTS: empty selection")
    return out


def _same(point, wanted) -> bool:
    return point[0] == wanted[0] and sorted((k, float(v)) for k, v in point[1].items()) == \
        sorted((k, float(v)) for k, v in wanted[1].items())


def select_points(points: list, spec: str) -> list:
    """The declared grid points named in spec, in grid order; every named point must exist; never empty."""
    wanted = parse_points(spec)
    missing = [w for w in wanted if not any(_same(p, w) for p in points)]
    if missing:
        raise SystemExit(f"POINTS: not in the declared grid: {missing}; grid has {points}")
    kept = [p for p in points if any(_same(p, w) for w in wanted)]
    if not kept:
        raise SystemExit("POINTS: selection empty after filtering")
    return kept
