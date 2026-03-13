"""Tests for chrome_cdp.helpers — pure utility functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from chrome_cdp.helpers import (
    MIN_TARGET_PREFIX_LEN,
    SOCK_PREFIX,
    get_display_prefix_length,
    get_ws_url,
    list_daemon_sockets,
    resolve_prefix,
    sock_path,
)

# ── sock_path ──────────────────────────────────────────────────────────────


class TestSockPath:
    def test_basic(self):
        result = sock_path("ABC123")
        assert result == f"{SOCK_PREFIX}ABC123.sock"

    def test_empty_target(self):
        result = sock_path("")
        assert result == f"{SOCK_PREFIX}.sock"

    def test_long_target(self):
        tid = "A" * 64
        result = sock_path(tid)
        assert result == f"{SOCK_PREFIX}{tid}.sock"


# ── resolve_prefix ─────────────────────────────────────────────────────────


class TestResolvePrefix:
    def test_exact_match(self):
        candidates = ["AABB1122", "CCDD3344", "EEFF5566"]
        assert resolve_prefix("AABB1122", candidates) == "AABB1122"

    def test_partial_match(self):
        candidates = ["AABB1122CCDD", "EEFF5566GGHH"]
        assert resolve_prefix("AABB", candidates) == "AABB1122CCDD"

    def test_case_insensitive(self):
        candidates = ["AABB1122CCDD"]
        assert resolve_prefix("aabb", candidates) == "AABB1122CCDD"

    def test_ambiguous_prefix_raises(self):
        candidates = ["AABB1122", "AABB3344"]
        with pytest.raises(ValueError, match="Ambiguous prefix"):
            resolve_prefix("AABB", candidates)

    def test_no_match_raises(self):
        candidates = ["AABB1122", "CCDD3344"]
        with pytest.raises(ValueError, match="No target matching"):
            resolve_prefix("ZZZZ", candidates)

    def test_no_match_with_hint(self):
        candidates = ["AABB1122"]
        with pytest.raises(ValueError, match='Run "cdp list"'):
            resolve_prefix("ZZZZ", candidates, "target", 'Run "cdp list".')

    def test_custom_noun(self):
        with pytest.raises(ValueError, match="No daemon matching"):
            resolve_prefix("ZZZZ", [], "daemon")

    def test_single_candidate(self):
        assert resolve_prefix("A", ["AABB1122"]) == "AABB1122"

    def test_empty_prefix_matches_all_raises(self):
        candidates = ["AAA", "BBB"]
        with pytest.raises(ValueError, match="Ambiguous"):
            resolve_prefix("", candidates)

    def test_empty_prefix_single_candidate(self):
        assert resolve_prefix("", ["AAA"]) == "AAA"


# ── get_display_prefix_length ──────────────────────────────────────────────


class TestGetDisplayPrefixLength:
    def test_empty_list(self):
        assert get_display_prefix_length([]) == MIN_TARGET_PREFIX_LEN

    def test_single_id(self):
        result = get_display_prefix_length(["AABB1122CCDD3344"])
        assert result == MIN_TARGET_PREFIX_LEN

    def test_unique_at_min_length(self):
        # IDs that differ in the first character — min prefix is enough
        ids = ["AABB1122CCDD3344", "BBCC2233DDEE5566"]
        result = get_display_prefix_length(ids)
        assert result == MIN_TARGET_PREFIX_LEN

    def test_ids_sharing_long_prefix(self):
        # Share first 10 chars, differ at 11th
        ids = ["AABB1122CCX11111", "AABB1122CCY22222"]
        result = get_display_prefix_length(ids)
        # Must be at least 11 to distinguish
        assert result >= 11

    def test_case_insensitive_prefixes(self):
        # These are same when uppercased for prefix check
        ids = ["aabb1122CCDD3344", "AABB1122CCDD9999"]
        result = get_display_prefix_length(ids)
        # Must go past the shared prefix AABB1122CCDD
        assert result > MIN_TARGET_PREFIX_LEN

    def test_identical_ids_returns_max_len(self):
        ids = ["AABB1122", "AABB1122"]
        result = get_display_prefix_length(ids)
        assert result == len("AABB1122")


# ── list_daemon_sockets ────────────────────────────────────────────────────


class TestListDaemonSockets:
    @patch("chrome_cdp.helpers.os.listdir")
    def test_finds_sockets(self, mock_listdir):
        mock_listdir.return_value = [
            "cdp-ABC123.sock",
            "cdp-DEF456.sock",
            "other-file.txt",
        ]
        result = list_daemon_sockets()
        assert len(result) == 2
        assert result[0]["target_id"] == "ABC123"
        assert result[0]["socket_path"] == "/tmp/cdp-ABC123.sock"
        assert result[1]["target_id"] == "DEF456"

    @patch("chrome_cdp.helpers.os.listdir")
    def test_empty_tmp(self, mock_listdir):
        mock_listdir.return_value = []
        assert list_daemon_sockets() == []

    @patch("chrome_cdp.helpers.os.listdir")
    def test_no_matching_sockets(self, mock_listdir):
        mock_listdir.return_value = ["foo.sock", "bar.txt", "cdp-pages.json"]
        assert list_daemon_sockets() == []

    @patch("chrome_cdp.helpers.os.listdir", side_effect=OSError("Permission denied"))
    def test_oserror_returns_empty(self, _mock_listdir):
        assert list_daemon_sockets() == []


# ── get_ws_url ─────────────────────────────────────────────────────────────


class TestGetWsUrl:
    def test_reads_devtools_port_file(self, tmp_path):
        port_file = tmp_path / "DevToolsActivePort"
        port_file.write_text("9222\n/devtools/browser/abc-123\n")

        with (
            patch("chrome_cdp.helpers.Path.home", return_value=tmp_path),
            patch.object(
                Path,
                "read_text",
                return_value="9222\n/devtools/browser/abc-123\n",
            ),
        ):
            result = get_ws_url()
            assert result == "ws://127.0.0.1:9222/devtools/browser/abc-123"

    def test_file_not_found_raises(self):
        with (
            patch.object(Path, "read_text", side_effect=FileNotFoundError),
            pytest.raises(FileNotFoundError),
        ):
            get_ws_url()
