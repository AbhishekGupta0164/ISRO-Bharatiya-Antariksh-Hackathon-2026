"""Exposure engine typed helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExposureInput:
    distance: float
    pollution: float


@dataclass(frozen=True)
class ExposureResult:
    exposure: float
