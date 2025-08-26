"""
Module for collecting and displaying statistics about schemas.
"""

from typing import Dict, Generator, List, Optional

import pytest


class SchemaStats:
    """Class for collecting and displaying statistics about schemas"""

    def __init__(self) -> None:
        self.created: List[str] = []
        self.updated: List[str] = []
        self.updated_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.uncommitted: List[str] = []  # New category for uncommitted changes
        self.uncommitted_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.deleted: List[str] = []
        self.unused: List[str] = []

    def add_created(self, schema_name: str) -> None:
        """Adds created schema"""
        self.created.append(schema_name)

    def add_updated(self, schema_name: str, diff: Optional[str] = None) -> None:
        """Adds updated schema"""
        # Generate diff if both schemas are provided
        if diff and diff.strip():
            self.updated.append(schema_name)
            self.updated_diffs[schema_name] = diff
        else:
            # If schemas are not provided, assume it was an update
            self.updated.append(schema_name)

    def add_uncommitted(self, schema_name: str, diff: Optional[str] = None) -> None:
        """Adds schema with uncommitted changes"""
        # Add only if there are real changes
        if diff and diff.strip():
            self.uncommitted.append(schema_name)
            self.uncommitted_diffs[schema_name] = diff

    def add_deleted(self, schema_name: str) -> None:
        """Adds deleted schema"""
        self.deleted.append(schema_name)

    def add_unused(self, schema_name: str) -> None:
        """Adds unused schema"""
        self.unused.append(schema_name)

    def has_changes(self) -> bool:
        """Returns True if any schema has changes"""
        return bool(self.created or self.updated or self.deleted)

    def has_any_info(self) -> bool:
        """Is there any information about schemas"""
        return bool(self.created or self.updated or self.deleted or self.unused or self.uncommitted)

    def __str__(self) -> str:
        parts = []
        if self.created:
            parts.append(
                f"Created schemas ({len(self.created)}): "
                + ", ".join(f"`{s}`" for s in self.created)
            )
        if self.updated:
            parts.append(
                f"Updated schemas ({len(self.updated)}): "
                + ", ".join(f"`{s}`" for s in self.updated)
            )
        if self.deleted:
            parts.append(
                f"Deleted schemas ({len(self.deleted)}): "
                + ", ".join(f"`{s}`" for s in self.deleted)
            )
        if self.unused:
            parts.append(
                f"Unused schemas ({len(self.unused)}): " + ", ".join(f"`{s}`" for s in self.unused)
            )

        return "\n".join(parts)

    def print_summary(self, terminalreporter: pytest.TerminalReporter, update_mode: bool) -> None:
        """
        Prints schema summary to pytest terminal output.
        Pairs of "<name>.schema.json" + "<name>.json" are merged into one line:
        "<name>.schema.json + original" (if original is present).
        """

        def _iter_merged(names: List[str]) -> Generator[tuple[str, Optional[str]], None, None]:
            """
            Iterates over (display, schema_key):
            - display: string to display (may have " + original")
            - schema_key: file name of the schema (<name>.schema.json) to find diffs,
                or None if it's not a schema.
            Preserves the original list order: merging happens at .schema.json
            position; single .json outputs are left as is.
            """
            names = list(names)  # порядок важен
            schema_sfx = ".schema.json"
            json_sfx = ".json"

            # множество баз, где имеются схемы/оригиналы
            bases_with_schema = {n[: -len(schema_sfx)] for n in names if n.endswith(schema_sfx)}
            bases_with_original = {
                n[: -len(json_sfx)]
                for n in names
                if n.endswith(json_sfx) and not n.endswith(schema_sfx)
            }

            for n in names:
                if n.endswith(schema_sfx):
                    base = n[: -len(schema_sfx)]
                    if base in bases_with_original:
                        yield f"{n} + original", n  # display, schema_key
                    else:
                        yield n, n
                elif n.endswith(json_sfx) and not n.endswith(schema_sfx):
                    base = n[: -len(json_sfx)]
                    # если есть парная схема — .json не выводим отдельно
                    if base in bases_with_schema:
                        continue
                    yield n, None
                else:
                    # на всякий случай — прочие имена
                    yield n, n

        if not self.has_any_info():
            return

        terminalreporter.write_sep("=", "Schema Summary")

        # Created
        if self.created:
            terminalreporter.write_line(f"Created schemas ({len(self.created)}):", green=True)
            for display, _key in _iter_merged(self.created):
                terminalreporter.write_line(f"  - {display}", green=True)

        # Updated
        if self.updated:
            terminalreporter.write_line(f"Updated schemas ({len(self.updated)}):", yellow=True)
            for display, key in _iter_merged(self.updated):
                terminalreporter.write_line(f"  - {display}", yellow=True)
                # Показываем diff, если он есть под ключом схемы (.schema.json)
                if key and key in self.updated_diffs:
                    terminalreporter.write_line("    Changes:", yellow=True)
                    for line in self.updated_diffs[key].split("\n"):
                        if line.strip():
                            terminalreporter.write_line(f"      {line}")
                    terminalreporter.write_line("")  # разделение
                elif key:
                    terminalreporter.write_line(
                        "    (Schema unchanged - no differences detected)", cyan=True
                    )

        # Uncommitted
        if self.uncommitted:
            terminalreporter.write_line(
                f"Uncommitted minor updates ({len(self.uncommitted)}):", bold=True
            )
            for display, key in _iter_merged(self.uncommitted):
                terminalreporter.write_line(f"  - {display}", cyan=True)
                if key and key in self.uncommitted_diffs:
                    terminalreporter.write_line("    Detected changes:", cyan=True)
                    for line in self.uncommitted_diffs[key].split("\n"):
                        if line.strip():
                            terminalreporter.write_line(f"      {line}")
                    terminalreporter.write_line("")  # разделение
            terminalreporter.write_line("Use --schema-update to commit these changes", cyan=True)

        # Deleted
        if self.deleted:
            terminalreporter.write_line(f"Deleted schemas ({len(self.deleted)}):", red=True)
            for display, _key in _iter_merged(self.deleted):
                terminalreporter.write_line(f"  - {display}", red=True)

        # Unused (только если не update_mode)
        if self.unused and not update_mode:
            terminalreporter.write_line(f"Unused schemas ({len(self.unused)}):")
            for display, _key in _iter_merged(self.unused):
                terminalreporter.write_line(f"  - {display}")
            terminalreporter.write_line("Use --schema-update to delete unused schemas", yellow=True)


GLOBAL_STATS = SchemaStats()
