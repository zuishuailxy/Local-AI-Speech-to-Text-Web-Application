"""Text normalization used after Chinese ASR.

Whisper's ``language="zh"`` token does not select Simplified or Traditional
script; the same model can emit either.  The web UI and sample references use
Simplified Chinese, so normalize the final Chinese text with a local, offline
converter.
"""

from __future__ import annotations

import zhconv


def to_simplified(text: str) -> str:
    """Convert Traditional Chinese to Simplified Chinese; other text is unchanged."""

    if not text:
        return text
    return zhconv.convert(text, "zh-cn")


__all__ = ["to_simplified"]
