"""The producer-runtime identity oracle (chpc/row19_identity_oracle.py; Codex's bounded design opinion RSC 9d8f706): a
GENUINE local identity mismatch - the producer's dataset differs from this host's rebuild by one ULP in the response bytes
(the row 19 rep-2 case) - is established only by an oracle generated in the producer's own process from the same manifest
and binding; every other oracle refuses (another manifest, another binding/root, another rep/seed/B, another runtime or
pins or snapshot, a structural/fold/draw digest that differs, a recomputed identity that differs, an unusable entry, a
malformed document, two entries, an absent oracle = today's behaviour); the record refusals stay refused on the oracle
path; a failed pull never supplies the oracle; an oracle beside a local match is not consulted (basis stays local)."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, io, contextlib, copy
import numpy as np
import analyze as A, simulate as S

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
import row19_identity_oracle as O
spec = importlib.util.spec_from_file_location("row19_control_compare", os.path.join(T1, "chpc", "row19_control_compare.py"))
CC = importlib.util.module_from_spec(spec); spec.loader.exec_module(CC)
from test_row19_slice import _manifest, _run, _dirs, _Patched
from test_row19_watch import _snapshot, _watch, _set_entry, W, R19
from test_row19_control_compare import _run_ctl, W_INT
from row19_ledger import CampaignLedger


def _perturbed_make_dataset(orig):
    """The producer's generator: the same dataset with ten response values moved by one ULP (the measured rep-2 difference)."""
    def make(*args, **kw):
        ds = orig(*args, **kw)
        y = np.array(ds.y, dtype=np.float64, copy=True)
        flat = y.reshape(-1)
        flat[:10] = np.nextafter(flat[:10], np.inf)
        d2 = A.Dataset(y, ds.k, ds.concept, ds.family, ds.layers, group=ds.group)
        d2.meta.update(ds.meta)
        return d2
    return make


class _Producer:
    """Run the producer (the runner and the oracle generator) under the perturbed generator; restore afterwards."""
    def __init__(self, perturbed=True):
        self.perturbed = perturbed
    def __enter__(self):
        self.keep = S.make_dataset
        if self.perturbed:
            S.make_dataset = _perturbed_make_dataset(self.keep)
        self.p = _Patched(); self.p.__enter__()
        return self
    def __exit__(self, *a):
        self.p.__exit__(*a)
        S.make_dataset = self.keep


def _produce_main(perturbed=True, n_boot=10, segment=4):
    d, c = _dirs()
    with _Producer(perturbed):
        man = _manifest(d, c, n_boot=n_boot)
        assert _run(d, man, "--job-id", "j1", "--segment", str(segment)) == R19.RESUME
        mp = os.path.join(d, "manifest.json")
        doc = O.generate(mp, d)
    b = json.load(open(os.path.join(d, "task_0.json")))["binding"]
    return d, c, man, mp, b, doc


def test_a_genuine_local_mismatch_is_established_only_by_the_producers_oracle():
    d, c, man, mp, b, doc = _produce_main()
    e = doc["entries"]["0"]
    assert e["usable"] and e["identity_equals_binding"] and e["identity"] == b["ident"] and doc["manifest_sha256"] == b["manifest_sha"]
    # this host's rebuild differs (one ULP in y): today's refusal without an oracle
    try:
        CC.expected_contract(mp, b); assert False, "the local rebuild should not reproduce the perturbed identity"
    except ValueError as ex:
        assert "not the manifest's" in str(ex) and "fallback" not in str(ex)
    # with the producer's oracle: established, basis oracle, structural digests equal, the response digest differs
    ex = CC.expected_contract(mp, b, oracle=O.load(d))
    assert ex["basis"] == "oracle" and ex["ident"] == b["ident"] and "pinned-runtime oracle" in ex["basis_detail"]
    loc, _ = O.structural_digests(*O.rebuild(man, 0, b["ds_seed"])[1:3], O.rebuild(man, 0, b["ds_seed"])[4])
    assert all(e["digests"][k] == loc[k] for k in O.STRUCTURAL) and e["digests"]["y"] != loc["y"]
    # the produced records validate under the established contract; refusals stay refusals on this path
    ck = os.path.join(d, "ckpt", [f for f in os.listdir(os.path.join(d, "ckpt")) if f.endswith(".jsonl")][0])
    recs = [json.loads(l) for l in open(ck).read().splitlines() if l.strip()]
    assert len(recs) == 4 and all(CC.validate_record(r, ex, 10) == "" for r in recs)
    bad = copy.deepcopy(recs[0]); bad["ident"] = "0" * 64; bad["sha"] = CC.record_sha(bad)
    assert "identity" in CC.validate_record(bad, ex, 10)
    bad = copy.deepcopy(recs[1]); bad["chosen"] = [-1]; bad["sha"] = CC.record_sha(bad)
    assert "drawn concepts differ" in CC.validate_record(bad, ex, 10)
    # the watch on the pulled root: counts the records, names the basis, no alarm; after a FAILED pull the oracle is not used
    mp2, lr = _snapshot(d, c, man)
    _set_entry("j1", runner_exit=None, runner_ended=None)
    rc, out = _watch(mp2)
    assert rc == 0 and "accepted 4/10" in out and "identity basis: oracle" in out
    keep = W.fresh_snapshot
    W.fresh_snapshot = lambda campaign, roots: (False, ["pull of x failed (rc 1): simulated"])
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = W.main(["--manifest", mp2])
        out = buf.getvalue()
    finally:
        W.fresh_snapshot = keep
    assert rc == 1 and "PULL FAILED" in out and "task binding is not this manifest's" in out and "identity basis: oracle" not in out


def test_an_oracle_beside_a_local_match_is_not_consulted():
    d, c, man, mp, b, doc = _produce_main(perturbed=False)
    ex = CC.expected_contract(mp, b, oracle=O.load(d))
    assert ex["basis"] == "local" and ex["ident"] == b["ident"]
    assert doc["entries"]["0"]["usable"]


def test_every_other_oracle_cannot_supply_the_fallback():
    d, c, man, mp, b, doc = _produce_main()
    good = O.load(d)
    assert CC.expected_contract(mp, b, oracle=good)["basis"] == "oracle"

    def refused(mut, binding=None, needle="fallback"):
        o = copy.deepcopy(good)
        mut(o)
        try:
            CC.expected_contract(mp, binding or b, oracle=o)
        except ValueError as ex:
            assert needle in str(ex), str(ex)
            return
        assert False, "the oracle should not have supplied the fallback"
    e = lambda o: o["entries"]["0"]
    refused(lambda o: o.__setitem__("manifest_sha256", "0" * 64))                                   # other manifest bytes
    refused(lambda o: e(o).__setitem__("rep", 1))                                                    # another rep
    refused(lambda o: e(o).__setitem__("ds_seed", int(b["ds_seed"]) + 1))                            # another seed
    refused(lambda o: e(o).__setitem__("n_rep", 11))                                                 # another B
    refused(lambda o: e(o).__setitem__("binding_digest", "0" * 64))                                   # another binding
    refused(lambda o: None, binding=dict(b, ckpt=b["ckpt"].replace("ckpt", "other_root")))           # another root's task, same seed
    refused(lambda o: o["generated"]["snapshot"]["runtime"].__setitem__("python", "9.9.9"))         # another runtime
    refused(lambda o: o["generated"]["snapshot"]["files"].__setitem__("models.py", "0" * 16))       # another pin
    refused(lambda o: o["generated"]["snapshot"]["models"].__setitem__("PAD_MULTIPLE", 7))          # another model setting
    refused(lambda o: o["generated"].__setitem__("sources", {"analyze.py": "0" * 16}))               # declared sources not the snapshot's
    for k in ("k", "concept", "family", "layers", "meta", "folds", "draws"):
        refused(lambda o, k=k: e(o)["digests"].__setitem__(k, "0" * 64))                            # a structural digest differs
    refused(lambda o: e(o)["digests"].pop("draws"))                                                  # a structural digest missing
    refused(lambda o: e(o).__setitem__("identity", "0" * 64))                                         # recomputed identity differs
    refused(lambda o: e(o).__setitem__("identity_equals_binding", False))
    refused(lambda o: e(o).__setitem__("usable", False))
    refused(lambda o: e(o).__setitem__("problems", ["x"]))
    refused(lambda o: o.__setitem__("version", 2), needle="fallback")
    refused(lambda o: o.pop("entries"))
    refused(lambda o: o["entries"].__setitem__("0b", copy.deepcopy(e(o))))                            # two entries for the rep
    refused(lambda o: o.__setitem__("__invalid__", "not JSON: x"))
    # an unreadable file on disk
    open(os.path.join(d, O.ORACLE_NAME), "w").write("{not json")
    try:
        CC.expected_contract(mp, b, oracle=O.load(d)); assert False
    except ValueError as ex:
        assert "unreadable" in str(ex)
    # absent: today's behaviour, no mention of a fallback
    os.remove(os.path.join(d, O.ORACLE_NAME))
    assert O.load(d) is None
    try:
        CC.expected_contract(mp, b, oracle=O.load(d)); assert False
    except ValueError as ex:
        assert "fallback" not in str(ex)


def test_the_generator_writes_unusable_entries_for_bindings_it_cannot_establish():
    d, c, man, mp, b, doc = _produce_main(perturbed=False)
    tp = os.path.join(d, "task_0.json"); t = json.load(open(tp))
    t["binding"]["numerical"]["runtime"]["python"] = "9.9.9"; json.dump(t, open(tp, "w"))
    doc = O.generate(mp, d)
    e = doc["entries"]["0"]
    assert e["usable"] is False and any("effective snapshot" in p for p in e["problems"])
    t["binding"]["numerical"]["runtime"]["python"] = b["numerical"]["runtime"]["python"]
    t["binding"]["manifest_sha"] = "0" * 64; json.dump(t, open(tp, "w"))
    e = O.generate(mp, d)["entries"]["0"]
    assert e["usable"] is False and any("manifest sha" in p for p in e["problems"])
    t["binding"]["manifest_sha"] = b["manifest_sha"]; t["binding"]["ident"] = "0" * 64; json.dump(t, open(tp, "w"))
    e = O.generate(mp, d)["entries"]["0"]
    assert e["usable"] is False and e["identity_equals_binding"] is False
    t["binding"].pop("orig"); json.dump(t, open(tp, "w"))
    doc = O.generate(mp, d)
    assert all(not v.get("usable") for v in doc["entries"].values())
    # the CLI exit reflects usability
    json.dump({"binding": b}, open(tp, "w"))
    assert O.main(["--manifest", mp, "--root", d]) == 0


def test_the_comparator_establishes_a_perturbed_control_through_the_oracle():
    d1, c = _dirs(); d2 = tempfile.mkdtemp()
    L = CampaignLedger(c, 1500.0)
    with _Producer(True):
        man = _manifest(d1, c, n_boot=30, target=20)
        assert _run_ctl(d1, man, "c1", "c1.sched", "--until", "20") == R19.RESUME
        assert _run_ctl(d2, man, "c2", "c2.sched", "--until", "20", "--segment", "7", "--pbs-kill-control", walltime_s=W_INT) == R19.RESUME
        assert _run_ctl(d2, man, "c3", "c3.sched", "--until", "20") == R19.RESUME
        O.generate(os.path.join(d1, "manifest.json"), d1)
    ck1 = os.path.join(d1, "ckpt", [f for f in os.listdir(os.path.join(d1, "ckpt")) if f.endswith(".jsonl")][0])
    ck3 = os.path.join(d2, "ckpt", [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0])
    it = os.path.join(d2, "c2_interruption.json")
    json.dump(dict(job_id="c2.sched", exit_status=271, walltime_requested_s=W_INT, walltime_used_s=W_INT + 3.0, pbs_killed=True,
                   accepted_records_before=7, original_cache_reused=True, tail_fragment_present=False), open(it, "w"))
    args = ["--manifest", os.path.join(d1, "manifest.json"), "--task", os.path.join(d1, "task_0.json"), "--c1", ck1, "--c3", ck3,
            "--status-c1", os.path.join(d1, "status_0.json"), "--status-c3", os.path.join(d2, "status_0.json"),
            "--interruption", it, "--ledger", L.path, "--target", "20"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = CC.main(args)
    assert rc == 3 and "cannot be rebuilt" in buf.getvalue()                                           # no oracle: not comparable
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = CC.main(args + ["--oracle", os.path.join(d1, O.ORACLE_NAME)])
    out = buf.getvalue()
    assert rc == 0 and "identity basis: oracle" in out
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = CC.main(args + ["--oracle", os.path.join(d1, "absent.json")])
    assert rc == 3 and "is absent" in buf.getvalue()
