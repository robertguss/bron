"""A finding is one problem a check found, printed as `file:line: check-id: message`."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int | None
    check: str
    message: str

    def render(self, root: Path) -> str:
        try:
            shown = self.path.relative_to(root)
        except ValueError:
            shown = self.path
        location = f"{shown}:{self.line}" if self.line else f"{shown}"
        return f"{location}: {self.check}: {self.message}"
