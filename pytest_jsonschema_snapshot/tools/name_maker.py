import inspect
import re
from types import FunctionType, MethodType
from typing import Any, Dict, List, Tuple


class NameMaker:
    _PLACEHOLDER_RX = re.compile(r"\{([a-zA-Z_]\w*)(?:=([^}]*))?\}")

    @staticmethod
    def _join_nonempty(parts: List[str], sep: str) -> str:
        parts = [p for p in parts if p]
        return sep.join(parts) if parts else ""

    @staticmethod
    def _owner_from_qualname(obj: Any) -> str:
        qn = getattr(obj, "__qualname__", "")
        if "." not in qn or "<locals>" in qn:
            return ""
        cand = qn.rsplit(".", 1)[0]
        mod = inspect.getmodule(obj)
        return cand if mod and hasattr(mod, cand) and inspect.isclass(getattr(mod, cand)) else ""

    @staticmethod
    def _meta(obj: Any) -> Dict[str, Any]:
        is_method = isinstance(obj, MethodType)
        is_function = isinstance(obj, FunctionType)

        cls_name = ""
        method_name = ""
        module_name = ""
        qualname = getattr(obj, "__qualname__", "") or ""

        if is_method:
            method_name = obj.__name__
            owner = obj.__self__
            if owner is not None:
                cls_name = owner.__name__ if inspect.isclass(owner) else owner.__class__.__name__
            else:
                cls_name = NameMaker._owner_from_qualname(obj)
            module_name = obj.__func__.__module__
        elif is_function:
            method_name = obj.__name__
            module_name = obj.__module__
            cls_name = NameMaker._owner_from_qualname(obj)
        elif inspect.isbuiltin(obj):
            # builtin: len, [].append и т.п.
            method_name = getattr(obj, "__name__", "") or ""
            module_name = getattr(obj, "__module__", "") or ""
            owner = getattr(obj, "__self__", None)
            if owner is not None:
                cls_name = owner.__name__ if inspect.isclass(owner) else owner.__class__.__name__
        elif callable(obj):
            method_name = "__call__"
            typ = type(obj)
            cls_name = typ.__name__
            module_name = typ.__module__
        else:
            method_name = getattr(obj, "__name__", "")
            module_name = getattr(obj, "__module__", "")

        module_parts = module_name.split(".") if module_name else []
        package = module_parts[0] if module_parts else ""
        path_parts = module_parts[1:] if len(module_parts) > 1 else []
        module_leaf = module_parts[-1] if module_parts else ""

        try:
            filename = inspect.getsourcefile(obj) or inspect.getfile(obj)  # type: ignore[arg-type]
        except Exception:
            filename = ""

        return {
            "package": package,
            "package_full": module_name,
            "module": module_leaf,
            "module_parts": module_parts,  # для {package_full=SEP}
            "path_parts": path_parts,      # для {path=SEP}
            "class": cls_name,
            "method": method_name,
            "class_method": f"{cls_name}.{method_name}" if cls_name else method_name,
            "qualname": qualname,
            "filename": filename or "",
        }

    @staticmethod
    def format_callable(obj: Any, rule: str) -> str:
        meta = NameMaker._meta(obj)

        def repl(m: re.Match) -> str:
            key, sep = m.group(1), m.group(2)
            if key == "path":
                joiner = sep if sep is not None else "/"
                return NameMaker._join_nonempty(meta["path_parts"], joiner)
            if key == "class_method":
                joiner = sep if sep is not None else "."
                cls, meth = meta["class"], meta["method"]
                return meth if not cls else f"{cls}{joiner}{meth}"
            if key == "package_full":
                joiner = sep if sep is not None else "."
                return NameMaker._join_nonempty(meta["module_parts"], joiner)
            # простые скаляры
            return str(meta.get(key, ""))

        out = NameMaker._PLACEHOLDER_RX.sub(repl, rule)
        # чуть-чуть приберём, если в правиле было что-то вроде "X//{...}//Y"
        out = re.sub(r"/{2,}", "/", out)
        return out
