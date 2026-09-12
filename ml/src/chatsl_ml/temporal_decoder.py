from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TemporalDecoderConfig:
    start_motion: float = 0.035
    end_motion: float = 0.018
    min_votes: int = 2
    high_confidence: float = 0.85
    release_windows: int = 1


@dataclass
class Vote:
    count: int = 0
    confidence_sum: float = 0.0
    confidence_max: float = 0.0

    def add(self, confidence: float) -> None:
        self.count += 1
        self.confidence_sum += confidence
        self.confidence_max = max(self.confidence_max, confidence)

    @property
    def score(self) -> float:
        return self.confidence_sum + self.confidence_max * 0.25


@dataclass(frozen=True)
class DecoderUpdate:
    phase: str
    status: str
    committed: dict[str, Any] | None = None


@dataclass
class TemporalSignDecoder:
    config: TemporalDecoderConfig = field(default_factory=TemporalDecoderConfig)
    phase: str = "idle"
    votes: dict[str, Vote] = field(default_factory=dict)
    quiet_windows: int = 0
    locked_label: str = ""

    def reset(self) -> None:
        self.phase = "idle"
        self.votes.clear()
        self.quiet_windows = 0
        self.locked_label = ""

    def update(self, result: dict[str, Any]) -> DecoderUpdate:
        quality = result.get("quality") or {}
        motion = float(quality.get("motion_score", 0.0))
        prediction = result.get("prediction")
        accepted = bool(result.get("accepted") and prediction)

        if self.phase == "idle":
            if motion < self.config.start_motion:
                return DecoderUpdate("idle", "Hareket bekleniyor")
            self.phase = "active"
            self.votes.clear()
            self.quiet_windows = 0
            self._add_vote(prediction if accepted else None)
            return DecoderUpdate("active", "Hareket basladi")

        if self.phase == "active":
            self._add_vote(prediction if accepted else None)
            if motion > self.config.end_motion:
                self.quiet_windows = 0
                return DecoderUpdate("active", self._candidate_status())

            self.quiet_windows += 1
            if self.quiet_windows < self.config.release_windows:
                return DecoderUpdate("active", "Hareketin bitmesi bekleniyor")

            committed = self._finish_segment()
            self.phase = "cooldown"
            self.quiet_windows = 0
            if committed:
                return DecoderUpdate(
                    "cooldown",
                    f"{committed['label']} algilandi",
                    committed,
                )
            return DecoderUpdate(
                "cooldown",
                "Hareket yeterince net degildi",
            )

        if motion <= self.config.end_motion:
            self.quiet_windows += 1
        else:
            self.quiet_windows = 0

        if self.quiet_windows >= self.config.release_windows:
            self.phase = "idle"
            self.quiet_windows = 0
            self.locked_label = ""
            return DecoderUpdate("idle", "Yeni hareket bekleniyor")
        return DecoderUpdate("cooldown", "Yeni hareket icin ellerini dinlendir")

    def _add_vote(self, prediction: dict[str, Any] | None) -> None:
        if not prediction:
            return
        label = str(prediction.get("label") or "").strip()
        if not label:
            return
        confidence = float(prediction.get("confidence", 0.0))
        self.votes.setdefault(label, Vote()).add(confidence)

    def _candidate_status(self) -> str:
        winner = self._winner()
        if not winner:
            return "Hareket yorumlaniyor"
        label, vote = winner
        return f"{label} adayi ({vote.count})"

    def _winner(self) -> tuple[str, Vote] | None:
        if not self.votes:
            return None
        return max(
            self.votes.items(),
            key=lambda item: (item[1].score, item[1].count),
        )

    def _finish_segment(self) -> dict[str, Any] | None:
        winner = self._winner()
        self.votes.clear()
        if not winner:
            return None

        label, vote = winner
        accepted = (
            vote.count >= self.config.min_votes
            or vote.confidence_max >= self.config.high_confidence
        )
        if not accepted or label == self.locked_label:
            return None

        self.locked_label = label
        return {
            "label": label,
            "confidence": vote.confidence_sum / vote.count,
            "votes": vote.count,
        }
