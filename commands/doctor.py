# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Environment diagnostics command."""

from __future__ import annotations

import os
import sys
import platform
import importlib.util
import importlib.metadata as _ilmd

from core import HF_CACHE_PATH, _probe_mlx_runtime, _detect_harmony_renderer


def cmd_doctor() -> None:
    """
    Run environment diagnostics to check MLX, mlx-lm, Harmony, and cache availability.

    Displays checkmarks for working components and suggestions for fixing issues.
    """
    print("🩺 mlxlm doctor\n")
    def mark(ok: bool) -> str: return "✅" if ok else "  "
    py_ok=True; print(f"{mark(py_ok)} Python : {sys.version.split()[0]} ({platform.machine()})")
    # MLX
    mlx_ok=False
    try:
        import mlx
        try: mlx_ver=_ilmd.version("mlx")
        except Exception: mlx_ver="unknown"
        ok, _, libpath = _probe_mlx_runtime()
        mlx_ok=ok
        loc=getattr(mlx,"__file__",None) or "unknown"
        print(f"{mark(mlx_ok)} mlx    : {mlx_ver} → {loc}")
    except Exception as e:
        print(f"{mark(False)} mlx    : (import failed) {e}")
    # mlx-lm
    try:
        import mlx_lm
        mlxlm_ver = getattr(mlx_lm,'__version__', _ilmd.version('mlx-lm'))
        print(f"{mark(True)} mlx-lm : {mlxlm_ver}")
    except Exception as e:
        print(f"{mark(False)} mlx-lm : (import failed) {e}")
    # Harmony
    try:
        installed = any(importlib.util.find_spec(n) is not None for n in ("openai_harmony","openai.harmony","harmony"))
    except Exception:
        installed=False
    try:
        renderer = _detect_harmony_renderer()
    except Exception:
        renderer = None
    if renderer:
        print(f"{mark(True)} harmony: OK (renderer found)")
    else:
        if installed:
            print(f"{mark(False)} harmony: INSTALLED (renderer not found; try updating `openai-harmony` or set MLXLM_RENDERER)")
        else:
            print(f"{mark(False)} harmony: MISSING")
    ok_lib, info_lib, lib_path = _probe_mlx_runtime()
    print(f"{mark(ok_lib)} libmlx : {'OK' if ok_lib else 'NG'} → {(lib_path or info_lib)}")
    hub = HF_CACHE_PATH
    hub_ok = os.path.isdir(hub)
    print(f"{mark(hub_ok)} HF hub : {hub} → {'exists' if hub_ok else 'missing'}")
    if not renderer:
        try:
            import importlib as _il
            candidates=[]
            for base in ("openai_harmony","openai.harmony","harmony"):
                for sub in ("","chat","renderer","render","core","api","utils"):
                    mod_name = f"{base}.{sub}" if sub else base
                    try:
                        mod = _il.import_module(mod_name)
                        names = [n for n in dir(mod) if n.startswith(('render','format'))]
                        if names: candidates.append((mod_name, names[:8]))
                    except Exception:
                        continue
            if candidates:
                print("harmony candidates:")
                for mod_name, names in candidates:
                    print("  -", mod_name, "→", ", ".join(names))
            env_spec = os.getenv("MLXLM_RENDERER","")
            if env_spec: print("harmony override (MLXLM_RENDERER):", env_spec)
        except Exception as e:
            print("harmony: extended probe error →", e)
    print("\nIf everything shows a checkmark✅, you're good to run `mlxlm run ...`")
