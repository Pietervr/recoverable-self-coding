"""HTTP client for the jlens-qwen36 serve API (stdlib only).

Endpoints (see upstream jlens_qwen/serve.py):
  GET  /api/lens      -> lens metadata (verify n_prompts == 1000 before use)
  GET  /api/model     -> model metadata
  POST /api/slice     {prompt, max_seq_len, top_n}
      -> {layers, seq_len, token_strs, top_n,
          cells: {layer: {top_ids, top_tokens, top_scores}}}  (prompt-only
          readout: this is the pre-action workspace state)
  POST /api/generate  {prompt, max_tokens, temp} -> {text, ...}
  POST /api/intervene {prompt, max_tokens, temp, layer,
                       mode: steer|swap|ablate, token, target, alpha,
                       positions, each_step}
  POST /api/tokenize  {prompt(?)} -> token ids/strings
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class JLensClient:
    def __init__(self, port: int = 8765, host: str = "127.0.0.1", timeout: int = 1800):
        self.base = f"http://{host}:{port}"
        self.timeout = timeout

    # -- plumbing ---------------------------------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.load(r)

    def _get(self, path: str) -> dict:
        with urllib.request.urlopen(self.base + path, timeout=60) as r:
            return json.load(r)

    # -- endpoints --------------------------------------------------------
    def lens_info(self) -> dict:
        return self._get("/api/lens")

    def model_info(self) -> dict:
        return self._get("/api/model")

    def require_n1000(self) -> dict:
        """The port's CLAUDE.md gate: refuse to interpret readouts on a
        smaller lens."""
        info = self.lens_info()
        if info.get("n_prompts") != 1000:
            raise RuntimeError(f"not the n=1000 lens: {info}")
        return info

    def slice(self, prompt: str, top_n: int = 10, max_seq_len: int = 512) -> dict:
        return self._post(
            "/api/slice",
            {"prompt": prompt, "top_n": top_n, "max_seq_len": max_seq_len},
        )

    def generate(self, prompt: str, max_tokens: int = 8, temp: float = 0.0) -> str:
        return self._post(
            "/api/generate",
            {"prompt": prompt, "max_tokens": max_tokens, "temp": temp},
        ).get("text", "")

    def intervene(
        self,
        prompt: str,
        layer: int,
        mode: str,
        token: str | None = None,
        target: str | None = None,
        alpha: float = 1.0,
        positions: list[int] | None = None,
        max_tokens: int = 8,
        temp: float = 0.0,
        each_step: bool = False,
    ) -> dict:
        payload: dict = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temp": temp,
            "layer": layer,
            "mode": mode,
            "alpha": alpha,
            "each_step": each_step,
        }
        if token is not None:
            payload["token"] = token
        if target is not None:
            payload["target"] = target
        if positions is not None:
            payload["positions"] = positions
        return self._post("/api/intervene", payload)

    def tokenize(self, prompt: str) -> dict:
        return self._post("/api/tokenize", {"prompt": prompt})

    def n_pieces(self, text: str) -> int:
        """Number of tokenizer pieces for `text` (used to filter the battery
        to single-token determinants — the lens's vocabulary limitation)."""
        r = self.tokenize(text)
        for key in ("ids", "input_ids", "tokens", "token_ids"):
            if key in r and isinstance(r[key], list):
                seq = r[key]
                # possibly nested [[...]]
                if seq and isinstance(seq[0], list):
                    seq = seq[0]
                return len(seq)
        raise RuntimeError(f"unrecognised tokenize response keys: {sorted(r)}")
