"""Optional compression for snapshot payloads before encryption."""

import zlib
from dataclasses import dataclass
from enum import Enum


class CompressError(Exception):
    """Raised when compression or decompression fails."""


class CompressionLevel(int, Enum):
    NONE = 0
    FAST = 1
    DEFAULT = 6
    BEST = 9


@dataclass(frozen=True)
class CompressResult:
    original_size: int
    compressed_size: int

    @property
    def ratio(self) -> float:
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size

    def summary(self) -> str:
        saved = self.original_size - self.compressed_size
        pct = (1.0 - self.ratio) * 100
        return (
            f"{self.original_size}B -> {self.compressed_size}B "
            f"(saved {saved}B, {pct:.1f}%)"
        )


def compress(data: bytes, level: CompressionLevel = CompressionLevel.DEFAULT) -> bytes:
    """Compress *data* using zlib and return the compressed bytes."""
    if not isinstance(data, (bytes, bytearray)):
        raise CompressError("data must be bytes")
    try:
        return zlib.compress(data, level)
    except zlib.error as exc:
        raise CompressError(f"compression failed: {exc}") from exc


def decompress(data: bytes) -> bytes:
    """Decompress zlib-compressed *data* and return the original bytes."""
    if not isinstance(data, (bytes, bytearray)):
        raise CompressError("data must be bytes")
    try:
        return zlib.decompress(data)
    except zlib.error as exc:
        raise CompressError(f"decompression failed: {exc}") from exc


def compress_text(text: str, level: CompressionLevel = CompressionLevel.DEFAULT) -> bytes:
    """Encode *text* to UTF-8 then compress it."""
    return compress(text.encode("utf-8"), level)


def decompress_text(data: bytes) -> str:
    """Decompress *data* and decode the result as UTF-8."""
    return decompress(data).decode("utf-8")
