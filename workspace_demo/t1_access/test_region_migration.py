"""Region-migration guards (Codex, continuation review 3, 13 Sept 2026). Every AWS client is a fake; nothing is
fitted, uploaded or launched.

1. launch_t1.upload_code: a resume into a bucket without the run's snapshot refuses and uploads nothing; an
   incomplete snapshot refuses; a --from-snapshot resume whose t1_job imports points_filter without the file
   refuses; an older snapshot that never used points_filter still resumes; a new namespace still uploads.
2. aws_env.cache_dir: sim_results/<run> for the Stockholm bucket, sim_results/<run>@<bucket> for any other.
3. spotcheck: revalidate refuses a gain file the latest pull did not fetch from the selected source (the stale
   Stockholm copy beside an empty Oregon listing); a freshly pulled one proceeds; pull refuses a local cache
   that mirrors another source.
"""
import contextlib
import importlib
import io
import json
import os
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("NPROC", "1")


def fresh(module, **env):
    for k in ("T1_AWS_REGION", "T1_AWS_BUCKET"):
        os.environ.pop(k, None)
    os.environ.update(env)
    for m in ("aws_env", module):
        sys.modules.pop(m, None)
    return importlib.import_module(module)


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


class FakeS3:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.uploads = []

    def list_objects_v2(self, Bucket, Prefix, **kw):
        return {"Contents": [{"Key": k, "Size": len(v)} for k, v in sorted(self.objects.items()) if k.startswith(Prefix)]}

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}

    def download_file(self, Bucket, Key, local):
        with open(local, "wb") as fh:
            fh.write(self.objects[Key])

    def upload_file(self, local, Bucket, Key):
        self.uploads.append(Key)


def refuses(fn):
    try:
        with quiet():
            fn()
    except SystemExit as e:
        return str(e)
    raise AssertionError("did not refuse")


# 1. the launcher
L = fresh("launch_t1", T1_AWS_REGION="us-west-2")
s3 = FakeS3()
assert "holds no code snapshot" in refuses(lambda: L.upload_code(s3, "existing_run", resume=True, from_snapshot=True))
assert "holds no code snapshot" in refuses(lambda: L.upload_code(s3, "existing_run", resume=True, from_snapshot=False))
assert s3.uploads == []
pre = "code/t1_access/existing_run/"
s3 = FakeS3({pre + "t1_job.py": b"import points_filter", pre + "models.py": b"", pre + "analyze.py": b""})
assert "incomplete snapshot" in refuses(lambda: L.upload_code(s3, "existing_run", resume=True, from_snapshot=True))
s3.objects[pre + "simulate.py"] = b""
assert "points_filter.py is missing" in refuses(lambda: L.upload_code(s3, "existing_run", resume=True, from_snapshot=True))
s3.objects[pre + "points_filter.py"] = b""
with quiet():
    assert L.upload_code(s3, "existing_run", resume=True, from_snapshot=True) == pre
s3 = FakeS3({pre + n: b"" for n in ("t1_job.py", "models.py", "analyze.py", "simulate.py")})    # a d4v12b-era snapshot
with quiet():
    assert L.upload_code(s3, "existing_run", resume=True, from_snapshot=True) == pre
assert s3.uploads == []
s3 = FakeS3()
with quiet():
    L.upload_code(s3, "new_run", resume=False)
assert len(s3.uploads) == len(L.CODE_FILES)
print("launcher: a resume never uploads; incomplete or points_filter-less snapshots refuse; old snapshots resume; new runs upload OK")

# 2. the local cache per bucket
E = fresh("aws_env")
assert E.cache_dir("/x", "r") == "/x/sim_results/r"
E = fresh("aws_env", T1_AWS_REGION="us-west-2")
assert E.cache_dir("/x", "r") == "/x/sim_results/r@xtenure-cself-pvr-usw2"
print("cache_dir: Stockholm keeps sim_results/<run>, Oregon gets sim_results/<run>@<bucket> OK")

# 3. the spot checker
C = fresh("spotcheck", T1_AWS_REGION="us-west-2")
import simulate as S  # noqa: E402


def no_fit(*a, **k):
    raise AssertionError("revalidation reached the fit")


S.revalidate_gain_entries = no_fit
run = "existing_run"
rp = f"results/t1_access/{run}/"
gain = json.dumps(dict(code_hash="a" * 12, D=4, entries=[{"origin": "prior Stockholm cache"}])).encode()
with tempfile.TemporaryDirectory() as td:
    with open(os.path.join(td, "gain_calibration_D4.json"), "wb") as fh:
        fh.write(gain)
    fake = FakeS3()
    C.boto3 = types.SimpleNamespace(Session=lambda **k: types.SimpleNamespace(client=lambda s: fake))
    with quiet():
        C.pull(run, "p", td)
    assert "not pulled from" in refuses(lambda: C.revalidate(run, 4, td, "p", 2026, 1))
    fake.objects[rp + "gain_calibration_D4.json"] = gain
    with quiet():
        C.pull(run, "p", td)
    try:
        with quiet():
            C.revalidate(run, 4, td, "p", 2026, 1)
        raise RuntimeError("revalidation neither refused nor reached the fit")
    except AssertionError as e:
        assert "reached the fit" in str(e)
    C2 = fresh("spotcheck")
    C2.boto3 = types.SimpleNamespace(Session=lambda **k: types.SimpleNamespace(client=lambda s: FakeS3()))
    assert "never crosses sources" in refuses(lambda: C2.pull(run, "p", td))
print("spotcheck: a stale local gain file is never revalidated; a freshly pulled one is; a cache never crosses sources OK")
