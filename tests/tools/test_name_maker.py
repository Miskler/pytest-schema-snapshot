from functools import wraps

import pytest

# импортируем тестируемую функцию из вашего модуля
from pytest_jsonschema_snapshot.tools import NameMaker

# ------------------------------ тестовые объекты ------------------------------


def free_func():
    pass


class C:
    def m(self):
        pass

    @staticmethod
    def s():
        pass

    @classmethod
    def c(cls):
        pass


class K:
    def __call__(self):
        pass


def decorator_no_wraps(fn):
    def wrapper(*a, **kw):
        return fn(*a, **kw)

    return wrapper


def decorator_with_wraps(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        return fn(*a, **kw)

    return wrapper


@decorator_no_wraps
def decorated_plain():
    pass


@decorator_with_wraps
def decorated_wrapped():
    pass


def make_inner():
    def inner():
        pass

    return inner


# ------------------------------ вспомогалки ------------------------------


def _split_module(mod_full: str):
    """Разбить имя модуля на (package, path_str) для ожиданий в ассертах."""
    if not mod_full:
        return "", ""
    parts = mod_full.split(".")
    pkg = parts[0]
    path_str = ".".join(parts[1:]) if len(parts) > 1 else ""
    return pkg, path_str


def _expected_prefix_for_module(obj, use_path_dot: bool = True) -> str:
    """
    Собрать ожидаемую приставку "{package}/{path=.}/" для данного объекта.
    use_path_dot=True соответствует {path=.}; False — соответствует пустому {path}.
    """
    mod_full = getattr(obj, "__module__", "") or getattr(type(obj), "__module__", "")
    pkg, path_dot = _split_module(mod_full)
    # если путь пуст — в правиле "{package}/{path=.}/..." двойной слэш схлопнется до одинарного
    # в нашей реализации лишние // конденсим -> "/"
    if path_dot and use_path_dot:
        return f"{pkg}/{path_dot}/"
    return f"{pkg}/"


# ------------------------------ тесты поведения плейсхолдеров ------------------------------


def test_free_function_class_method_joiner_slash():
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(free_func, rule)
    exp_prefix = _expected_prefix_for_module(free_func, use_path_dot=True)
    assert got == f"{exp_prefix}free_func"


def test_bound_method_class_method_joiner_slash():
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(C().m, rule)
    exp_prefix = _expected_prefix_for_module(C().m, use_path_dot=True)
    assert got == f"{exp_prefix}C/m"


def test_unbound_method_detects_class_via_qualname():
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(C.m, rule)  # функция, извлечённая у класса
    exp_prefix = _expected_prefix_for_module(C.m, use_path_dot=True)
    assert got == f"{exp_prefix}C/m"


def test_staticmethod_detects_class():
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(C.s, rule)  # обращаемся как к атрибуту класса
    exp_prefix = _expected_prefix_for_module(C.s, use_path_dot=True)
    assert got == f"{exp_prefix}C/s"


def test_classmethod_owner_is_class():
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(C.c, rule)
    exp_prefix = _expected_prefix_for_module(C.c, use_path_dot=True)
    assert got == f"{exp_prefix}C/c"


def test_callable_object_uses_dunder_call():
    rule = "{package}/{path=.}/{class_method=/}"
    k = K()
    got = NameMaker.format(k, rule)
    exp_prefix = _expected_prefix_for_module(k, use_path_dot=True)
    assert got == f"{exp_prefix}K/__call__"


def test_lambda_treated_as_function():
    f = lambda x: x  # noqa: E731
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(f, rule)
    exp_prefix = _expected_prefix_for_module(f, use_path_dot=True)
    # у лямбды имя <lambda>
    assert got == f"{exp_prefix}<lambda>"


def test_builtins_len_has_no_path():
    rule = "{package}/{path=/}/{class_method=/}"
    got = NameMaker.format(len, rule)
    # builtins → нет path; joiner для path не вставляется
    assert got == "builtins/len"


def test_inner_function_has_no_class_due_to_locals():
    inner = make_inner()
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(inner, rule)
    exp_prefix = _expected_prefix_for_module(inner, use_path_dot=True)
    # класс не извлекается из __qualname__ из-за '<locals>'
    assert got == f"{exp_prefix}inner"


def test_decorator_without_wraps_changes_method_name():
    rule = "{method}"
    got = NameMaker.format(decorated_plain, rule)
    # без wraps имя метода — wrapper
    assert got == "wrapper"


def test_decorator_with_wraps_preserves_original_name():
    rule = "{method}"
    got = NameMaker.format(decorated_wrapped, rule)
    assert got == "decorated_wrapped"


def test_package_full_with_custom_separator():
    rule = "{package_full=/}"
    got = NameMaker.format(free_func, rule)
    # ожидаем модуль в формате с '/'
    mod_full = free_func.__module__
    assert got == "/".join(mod_full.split(".")) if mod_full else ""


def test_path_default_separator_and_override():
    # по умолчанию path без "=SEP" собирается через '/'
    rule_default = "{path}"
    got_default = NameMaker.format(free_func, rule_default)
    mod_parts = (free_func.__module__ or "").split(".")
    path_slash = "/".join(mod_parts[1:]) if len(mod_parts) > 1 else ""
    assert got_default == path_slash

    # с переопределением разделителя: {path=.}
    rule_dot = "{path=.}"
    got_dot = NameMaker.format(free_func, rule_dot)
    path_dot = ".".join(mod_parts[1:]) if len(mod_parts) > 1 else ""
    assert got_dot == path_dot


def test_class_method_joiner_vs_literal_class_slash_method_difference():
    # у свободной функции {class}/{method} даёт ведущий '/', а {class_method=/} — нет
    got_join = NameMaker.format(free_func, "{class_method=/}")
    got_lit = NameMaker.format(free_func, "{class}/{method}")
    assert got_join == "free_func"
    assert got_lit == "/free_func"


def test_double_slashes_from_literal_collapsed():
    # правило с литеральными '//' схлопывается
    got = NameMaker.format(C().m, "X//{class_method=/}//Y")
    assert got == "X/C/m/Y"


def test_unknown_placeholder_becomes_empty():
    got = NameMaker.format(free_func, "A{unknown}B")
    assert got == "AB"


@pytest.mark.parametrize(
    "obj,expected_suffix",
    [
        (free_func, "free_func"),
        (C().m, "C/m"),
        (C.m, "C/m"),
        (C.s, "C/s"),
        (C.c, "C/c"),
        (K(), "K/__call__"),
    ],
)
def test_matrix_basic_suffixes(obj, expected_suffix):
    rule = "{package}/{path=.}/{class_method=/}"
    got = NameMaker.format(obj, rule)
    exp_prefix = _expected_prefix_for_module(obj, use_path_dot=True)
    assert got == f"{exp_prefix}{expected_suffix}"
