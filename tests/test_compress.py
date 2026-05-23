"""Tests for envpack.compress."""

import pytest

from envpack.compress import (
    CompressError,
    CompressResult,
    CompressionLevel,
    compress,
    compress_text,
    decompress,
    decompress_text,
)


def test_compress_returns_bytes():
    result = compress(b"hello world")
    assert isinstance(result, bytes)


def test_round_trip_bytes():
    original = b"KEY=value\nOTHER=123\n" * 50
    assert decompress(compress(original)) == original


def test_round_trip_text():
    original = "SECRET=abc\nDB_URL=postgres://localhost/db\n" * 30
    assert decompress_text(compress_text(original)) == original


def test_compressed_smaller_than_original_for_repetitive_data():
    original = b"REPEATED=value\n" * 100
    compressed = compress(original)
    assert len(compressed) < len(original)


def test_compression_level_none_still_round_trips():
    original = b"FAST=1\n"
    assert decompress(compress(original, CompressionLevel.NONE)) == original


def test_compression_level_best_still_round_trips():
    original = b"BEST=1\n" * 20
    assert decompress(compress(original, CompressionLevel.BEST)) == original


def test_compress_raises_on_non_bytes():
    with pytest.raises(CompressError):
        compress("not bytes")  # type: ignore[arg-type]


def test_decompress_raises_on_non_bytes():
    with pytest.raises(CompressError):
        decompress("not bytes")  # type: ignore[arg-type]


def test_decompress_raises_on_invalid_data():
    with pytest.raises(CompressError):
        decompress(b"this is not compressed data")


def test_compress_result_ratio_zero_original():
    result = CompressResult(original_size=0, compressed_size=0)
    assert result.ratio == 1.0


def test_compress_result_summary_contains_sizes():
    result = CompressResult(original_size=200, compressed_size=80)
    summary = result.summary()
    assert "200" in summary
    assert "80" in summary
    assert "120" in summary  # bytes saved


def test_compress_result_ratio():
    result = CompressResult(original_size=100, compressed_size=40)
    assert result.ratio == pytest.approx(0.4)


def test_empty_bytes_round_trip():
    assert decompress(compress(b"")) == b""
