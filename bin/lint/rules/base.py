from __future__ import annotations

from abc import ABC, abstractmethod

from config import LintConfig
from loader import InventoryContext
from reporter import Reporter


class Rule(ABC):
    name: str = "unnamed-rule"

    def __init__(self, cfg: LintConfig):
        self.cfg = cfg

    @abstractmethod
    def run(self, ctx: InventoryContext, reporter: Reporter) -> None:
        raise NotImplementedError
