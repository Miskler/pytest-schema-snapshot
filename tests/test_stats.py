from pytest_jsonschema_snapshot.stats import SchemaStats


class FakeTerminalReporter:
    """Простой заглушка терминального репортера pytest для тестирования print_summary."""

    def __init__(self):
        self.lines = []

    # pytest передаёт разделители вида write_sep("=", "Title")
    def write_sep(self, sep: str, title: str):  # noqa: D401, D403 — параметры как в pytest
        self.lines.append(f"{sep}{title}")

    # Цветные аргументы (green=True и т.д.) нам не нужны — собираем только текст
    def write_line(self, line: str, **_kwargs):  # noqa: D401, D403 — сигнатура как в pytest
        self.lines.append(line)


def test_add_methods_and_flags():
    """Проверяем, что все add_* методы корректно заполняют структуры и флаги has_*."""
    s = SchemaStats()

    # До изменений ничего не должно быть отмечено
    assert not s.has_changes()
    assert not s.has_any_info()

    s.add_created("new.schema.json")
    s.add_updated("upd.schema.json", diff="+added line")
    s.add_uncommitted("minor.schema.json", diff="+minor change")
    s.add_deleted("old.schema.json")
    s.add_unused("unused.schema.json")

    # Теперь должно считаться, что есть изменения и любая информация
    assert s.has_changes()
    assert s.has_any_info()

    # Проверяем содержимое списков
    assert s.created == ["new.schema.json"]
    assert s.updated == ["upd.schema.json"]
    assert s.uncommitted == ["minor.schema.json"]
    assert s.deleted == ["old.schema.json"]
    assert s.unused == ["unused.schema.json"]

    # Проверяем сохранённые diff'ы
    assert s.updated_diffs["upd.schema.json"] == "+added line"
    assert s.uncommitted_diffs["minor.schema.json"] == "+minor change"


def test_uncommitted_requires_diff():
    """add_uncommitted не должен ничего добавлять без непустого diff."""
    s = SchemaStats()
    s.add_uncommitted("minor.schema.json")  # diff не передаём
    assert s.uncommitted == []
    assert s.uncommitted_diffs == {}


def test_str_representation():
    """Строковое представление должно содержать корректные секции на русском."""
    s = SchemaStats()
    s.add_created("a.schema.json")
    s.add_updated("b.schema.json")
    s.add_unused("c.schema.json")

    summary = str(s)

    assert "Created schemas (1): `a.schema.json`" in summary
    assert "Updated schemas (1): `b.schema.json`" in summary
    assert "Unused schemas (1): `c.schema.json`" in summary


def test_print_summary_merging_and_output():
    """print_summary должен объединять .schema.json + .json и выводить diff."""
    s = SchemaStats()

    # Пара schema+original должна схлопнуться в одну строку
    s.add_created("foo.schema.json")
    s.add_created("foo.json")  # .json без .schema.json суффикса

    # Добавляем обновлённую схему с diff, чтобы проверить вывод изменений
    s.add_updated("bar.schema.json", diff="+changed")

    fake = FakeTerminalReporter()
    s.print_summary(fake, update_mode=False)

    output = "\n".join(fake.lines)

    assert "foo.schema.json + original" in output  # слияние имён
    assert "+changed" in output  # diff выводится
    assert "Unused schemas" not in output  # нет секции unused без схем


def test_print_summary_hides_unused_in_update_mode():
    """В режиме update_mode=True список unused не должен выводиться."""
    s = SchemaStats()
    s.add_unused("unused.schema.json")

    fake = FakeTerminalReporter()
    s.print_summary(fake, update_mode=True)

    output = "\n".join(fake.lines)

    assert "Unused schemas".lower() not in output.lower()
