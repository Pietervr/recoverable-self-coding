"""Photograph arm, desk gate ask 2: the dose and zero construction of framework §8.3, pixels only.

No model is loaded or run here. Every array is code values in [0, 1]; FP64 throughout generation, mixing and
reductions. Pinned implementation: Pillow 12.3.0 for decode, orientation, ICC and resize; NumPy 2.5.1 PCG64 for the
noise; transformers 5.13.0's native image processor from the frozen snapshot for the delivered tensor
(`.venv-image`).

  load_canvas(photo)   orientation (EXIF transpose), source ICC -> sRGB, alpha composited on RGB(0.5, 0.5, 0.5),
                       aspect-preserving fit inside 384 x 384 (longest side 384, the other rounded half-to-even,
                       min 1), bicubic with antialiasing, centred on a 0.5 canvas, odd padding pixel right/bottom.
                       Resizing is done per channel in float ('F' mode) so no 8-bit rounding precedes the dose.
  luma(rgb)            g = 0.2126 R + 0.7152 G + 0.0722 B in sRGB code values (luma, not luminance).
  signal(g)            S = r (g - mean g) / RMS(g - mean g); a constant canvas is rejected, never given a divisor.
  noise(nonce)         one 384 x 384 standard-normal draw from PCG64 seeded by the nonce, mean-subtracted on the
                       canvas and rescaled to RMS r. Never sees the photograph.
  mix(S, N, a)         I = mu + a S + sqrt(1 - a^2) N, clipped to [0, 1], quantised round-half-to-even(255 I),
                       replicated into three RGB channels, lossless PNG.
  zero(nonce)          mu + N on its OWN path: it never loads, opens or reads the photograph, its mean, spectrum,
                       geometry, label or file name.
  a_grid()             a = sqrt(10^(d/10) / (1 + 10^(d/10))) for d in (-18, -12, -6, 0, +6) dB, plus 0 and 1;
                       serialised with repr() and hashed - the rounded table is not the implementation.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps

CANVAS = 384
MU = 0.5
R = 0.10
DB = (-18.0, -12.0, -6.0, 0.0, 6.0)
NOISE_SEED = 20261004
LUMA = (0.2126, 0.7152, 0.0722)
SRGB = ImageCms.createProfile("sRGB")


def a_grid() -> dict:
    interior = [math.sqrt(10 ** (d / 10) / (1 + 10 ** (d / 10))) for d in DB]
    grid = {"noise_only": 0.0, **{f"{d:+.0f}dB": a for d, a in zip(DB, interior)}, "clean": 1.0}
    blob = json.dumps({k: repr(v) for k, v in grid.items()}, sort_keys=True).encode()
    return {"a": grid, "k": {n: 8 * a for n, a in grid.items()}, "sha256": hashlib.sha256(blob).hexdigest()}


def _round_half_even(x: float) -> int:
    return int(np.rint(x))


def load_canvas(path: Path) -> tuple[np.ndarray, dict]:
    """RGB float64 canvas (384, 384, 3) and the geometry record. The only function that opens the photograph."""
    raw = Path(path).read_bytes()
    im = Image.open(io.BytesIO(raw))
    ops = {"original_sha256": hashlib.sha256(raw).hexdigest(), "original_size": list(im.size),
           "original_mode": im.mode}
    im = ImageOps.exif_transpose(im)
    ops["orientation_applied"] = list(im.size) != ops["original_size"] or None
    icc = im.info.get("icc_profile")
    if icc:
        im = ImageCms.profileToProfile(im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im,
                                       ImageCms.ImageCmsProfile(io.BytesIO(icc)), SRGB, outputMode="RGB")
        ops["icc"] = "converted to sRGB"
    else:
        ops["icc"] = "none embedded; treated as sRGB"
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = np.asarray(im.convert("RGBA"), dtype=np.float64) / 255.0
        alpha = rgba[..., 3:4]
        rgb = rgba[..., :3] * alpha + MU * (1 - alpha)
        ops["alpha"] = "composited on 0.5 grey"
    else:
        rgb = np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0
        ops["alpha"] = "none"
    h, w = rgb.shape[:2]
    if w >= h:
        nw, nh = CANVAS, max(1, _round_half_even(h * CANVAS / w))
    else:
        nh, nw = CANVAS, max(1, _round_half_even(w * CANVAS / h))
    chans = [np.asarray(Image.fromarray(rgb[..., c].astype(np.float32), mode="F")
                        .resize((nw, nh), Image.Resampling.BICUBIC, reducing_gap=None), dtype=np.float64)
             for c in range(3)]
    fitted = np.stack(chans, axis=-1)
    canvas = np.full((CANVAS, CANVAS, 3), MU, dtype=np.float64)
    top, left = (CANVAS - nh) // 2, (CANVAS - nw) // 2
    canvas[top:top + nh, left:left + nw] = fitted
    ops.update(fitted_size=[nw, nh], offset=[left, top],
               padding={"left": left, "right": CANVAS - nw - left, "top": top, "bottom": CANVAS - nh - top},
               resize="Pillow 12.3.0 Image.resize BICUBIC, reducing_gap=None, per channel in mode F (float32)")
    return canvas, ops


def luma(rgb: np.ndarray) -> np.ndarray:
    return LUMA[0] * rgb[..., 0] + LUMA[1] * rgb[..., 1] + LUMA[2] * rgb[..., 2]


def signal(g: np.ndarray) -> np.ndarray:
    d = g - g.mean()
    rms = math.sqrt(float((d * d).mean()))
    if not rms > 0:
        raise ValueError("constant canvas: rejected at source qualification")
    return R * d / rms


def noise(nonce: str) -> np.ndarray:
    seq = np.random.SeedSequence([NOISE_SEED, int(hashlib.sha256(nonce.encode()).hexdigest()[:16], 16)])
    n = np.random.Generator(np.random.PCG64(seq)).standard_normal((CANVAS, CANVAS))
    n = n - n.mean()
    return R * n / math.sqrt(float((n * n).mean()))


def quantise(i: np.ndarray) -> tuple[np.ndarray, dict]:
    clipped = np.clip(i, 0.0, 1.0)
    stats = {"clipped_fraction": float(((i < 0) | (i > 1)).mean()),
             "clipped_low": float((i < 0).mean()), "clipped_high": float((i > 1).mean())}
    q = np.rint(255.0 * clipped).astype(np.uint8)          # numpy rint rounds half to even
    return np.repeat(q[..., None], 3, axis=-1), stats


def to_png(rgb8: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgb8, mode="RGB").save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def mix(S: np.ndarray, N: np.ndarray, a: float) -> np.ndarray:
    return MU + a * S + math.sqrt(1.0 - a * a) * N


def zero(nonce: str) -> np.ndarray:
    """Noise-only input. Built from mu and the nonce's draw alone: no photograph is opened or consulted."""
    return MU + noise(nonce)


def stats(I: np.ndarray, S: np.ndarray | None, N: np.ndarray | None) -> dict:
    out = {"pre_clip_mean": float(I.mean()), "pre_clip_rms": float(np.sqrt(((I - I.mean()) ** 2).mean()))}
    if S is not None and N is not None:
        out["S_rms"] = float(np.sqrt((S * S).mean()))
        out["N_rms"] = float(np.sqrt((N * N).mean()))
        out["corr_SN"] = float((S * N).mean() / (out["S_rms"] * out["N_rms"]))
        out["cross_term"] = float((S * N).mean())
    return out
