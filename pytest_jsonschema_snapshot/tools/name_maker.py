from __future__ import annotations

import inspect
import re
import types
from functools import partial
from typing import Callable, Dict, List, Optional


class NameMaker:
    """
    Lightweight helper that converts a callable into a string identifier
    using a tiny placeholder-based template language (keeps backward
    compatibility with the original test-suite).

    Supported placeholders
    ----------------------
    {package}                  – full module path (``tests.test_mod``)
    {package_full=SEP}         – same but with custom separator (default “.”)
    {path} / {path=SEP}        – module path *without* the first segment
    {class}                    – class name or empty string
    {method}                   – function / method name
    {class_method} / {...=SEP} – ``Class{SEP}method`` or just ``method``

    Unknown placeholders collapse to an empty string.

    After substitution:
      * “//”, “..”, “--” are collapsed to “/”, “.”, “-” respectively;
      * double underscores **are preserved** so ``__call__`` stays intact.
    """

    _RE_PLHDR = re.compile(r"\{([^{}]+)\}")

    # ────────────────────────────── PUBLIC ──────────────────────────────
    @staticmethod
    def format(obj: Callable, rule: str) -> str:
        """
        Render *rule* using metadata extracted from *obj*.

        If *sanitize* is True, the result is passed through
        ``pathvalidate.sanitize_filename`` (imported lazily so the dependency
        remains optional).
        """
        meta = NameMaker._meta(obj)

        def _sub(match: re.Match[str]) -> str:
            token = match.group(1)
            name, joiner = (token.split("=", 1) + [None])[:2]
            return NameMaker._expand(name, joiner, meta)

        out = NameMaker._RE_PLHDR.sub(_sub, rule)
        out = NameMaker._collapse(out)

        return out

    # ───────────────────────────── INTERNAL ─────────────────────────────
    # metadata -----------------------------------------------------------
    @staticmethod
    def _unwrap(obj: Callable) -> Callable:
        """Strip functools.partial and @functools.wraps wrappers."""
        while True:
            if isinstance(obj, partial):
                obj = obj.func
                continue
            if hasattr(obj, "__wrapped__"):
                obj = obj.__wrapped__  # type: ignore[attr-defined]
                continue
            break
        return obj

    @staticmethod
    def _meta(obj: Callable) -> Dict[str, object]:
        """Return mapping used during placeholder substitution."""
        obj = NameMaker._unwrap(obj)

        # 1) built-in function (len, sum, …)
        if inspect.isbuiltin(obj) or isinstance(obj, types.BuiltinFunctionType):
            qualname = obj.__name__
            module = obj.__module__ or "builtins"

        # 2) callable instance (defines __call__)
        elif not (inspect.isfunction(obj) or inspect.ismethod(obj)):
            qualname = f"{obj.__class__.__qualname__}.__call__"
            module = obj.__class__.__module__

        # 3) regular function / bound or unbound method
        else:
            qualname = obj.__qualname__
            module = obj.__module__

        parts: List[str] = qualname.split(".")
        cls: Optional[str] = None
        if len(parts) > 1 and parts[-2] != "<locals>":
            cls = parts[-2]
        method = parts[-1]

        mod_parts = (module or "").split(".")
        return {
            "package": module,
            "package_full": module,
            "path_parts": mod_parts[1:] if len(mod_parts) > 1 else [],
            "class": cls,
            "method": method,
        }

    # placeholders -------------------------------------------------------
    @staticmethod
    def _expand(name: str, joiner: Optional[str], m: Dict[str, object]) -> str:
        if name == "package":
            return m["package"] or ""
        if name == "package_full":
            sep = joiner if joiner is not None else "."
            return sep.join(str(m["package_full"]).split("."))
        if name == "path":
            if not m["path_parts"]:
                return ""
            sep = joiner if joiner is not None else "/"
            return sep.join(m["path_parts"])
        if name == "class":
            return m["class"] or ""
        if name == "method":
            return m["method"]
        if name == "class_method":
            sep = joiner if joiner is not None else "."
            if m["class"]:
                return sep.join([m["class"], m["method"]])
            return m["method"]
        # unknown placeholder → empty
        return ""

    # post-processing ----------------------------------------------------
    @staticmethod
    def _collapse(s: str) -> str:
        # collapse critical duplicates but keep double underscores
        s = re.sub(r"/{2,}", "/", s)   # '//' → '/'
        s = re.sub(r"\.{2,}", ".", s)  # '..' → '.'
        s = re.sub(r"-{2,}", "-", s)   # '--' → '-'
        return s
