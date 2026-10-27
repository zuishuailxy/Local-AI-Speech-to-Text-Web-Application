"""Pydantic response models for the public API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str = Field(description="Recognized text")
    language: str = Field(description="Requested language: zh or en")
    duration_seconds: float = Field(ge=0, description="Decoded audio duration")
    processing_seconds: float = Field(ge=0, description="Server-side processing time")


__all__ = ["TranscriptionResponse"]
