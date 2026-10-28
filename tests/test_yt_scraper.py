"""Tests fuer die yt-dlp-Aufrufe im Scraper (Login-/Bot-Check-Fix)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import yt_scraper  # noqa: E402


class FailedResult:
    returncode = 1
    stdout = ""
    stderr = ""


def test_base_cmd_enables_remote_ejs_solver(monkeypatch):
    monkeypatch.delenv("YT_DLP_COOKIES", raising=False)
    monkeypatch.delenv("YT_DLP_COOKIES_FROM_BROWSER", raising=False)
    cmd = yt_scraper.ytdlp_base_cmd()
    assert cmd[0] == "yt-dlp"
    assert cmd[cmd.index("--remote-components") + 1] == "ejs:github"
    assert "--cookies" not in cmd
    assert "--cookies-from-browser" not in cmd


def test_base_cmd_uses_cookie_file_from_env(monkeypatch, tmp_path):
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n")
    monkeypatch.setenv("YT_DLP_COOKIES", str(cookies))
    cmd = yt_scraper.ytdlp_base_cmd()
    assert cmd[cmd.index("--cookies") + 1] == str(cookies)


def test_base_cmd_ignores_missing_cookie_file(monkeypatch, tmp_path):
    monkeypatch.setenv("YT_DLP_COOKIES", str(tmp_path / "fehlt.txt"))
    monkeypatch.delenv("YT_DLP_COOKIES_FROM_BROWSER", raising=False)
    assert "--cookies" not in yt_scraper.ytdlp_base_cmd()


def test_base_cmd_uses_browser_cookies_from_env(monkeypatch):
    monkeypatch.delenv("YT_DLP_COOKIES", raising=False)
    monkeypatch.setenv("YT_DLP_COOKIES_FROM_BROWSER", "firefox")
    cmd = yt_scraper.ytdlp_base_cmd()
    assert cmd[cmd.index("--cookies-from-browser") + 1] == "firefox"


def test_all_ytdlp_calls_use_base_cmd(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FailedResult()

    monkeypatch.setattr(yt_scraper.subprocess, "run", fake_run)
    yt_scraper.search_youtube("test", 1)
    yt_scraper.get_video_metadata("https://www.youtube.com/watch?v=abc")
    yt_scraper.get_transcript("https://www.youtube.com/watch?v=abc", "abc")
    assert len(calls) >= 3
    for cmd in calls:
        assert "--remote-components" in cmd


def test_transcript_survives_single_language_error(monkeypatch):
    """A 429 on one (auto-translated) track must not abort the other tracks."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FailedResult()

    monkeypatch.setattr(yt_scraper.subprocess, "run", fake_run)
    yt_scraper.get_transcript("https://www.youtube.com/watch?v=abc", "abc")
    for cmd in calls:
        assert "--ignore-errors" in cmd


def test_bot_check_in_transcript_is_reported(monkeypatch, capsys):
    class BotResult(FailedResult):
        stderr = "ERROR: [youtube] abc: Sign in to confirm you’re not a bot. Use --cookies-from-browser"

    monkeypatch.setattr(yt_scraper.subprocess, "run", lambda cmd, **kw: BotResult())
    assert yt_scraper.get_transcript("https://www.youtube.com/watch?v=abc", "abc") is None
    assert "YT_DLP_COOKIES" in capsys.readouterr().err


SRT = "1\n00:00:00,000 --> 00:00:01,000\n{}\n"


def fake_subs(available: dict[str, str], calls: list):
    """yt-dlp-Ersatz: legt fuer jede verfuegbare Spur eine .srt im -o-Ordner an."""
    class Ok(FailedResult):
        returncode = 0

    def run(cmd, **kwargs):
        calls.append(cmd)
        outdir = Path(cmd[cmd.index("-o") + 1]).parent
        for lang, text in available.items():
            (outdir / f"abc.{lang}.srt").write_text(SRT.format(text))
        return Ok()
    return run


def test_transcript_prefers_original_language_over_translation(monkeypatch):
    """Englisches Video mit deutscher Spur: das Original muss gewinnen, nicht die alphabetisch erste Datei."""
    calls = []
    monkeypatch.setattr(yt_scraper.subprocess, "run",
                        fake_subs({"de-DE": "Uns beiden ist die Liebe nicht fremd", "en": "We're no strangers to love"}, calls))
    text = yt_scraper.get_transcript("https://www.youtube.com/watch?v=abc", "abc", language="en")
    assert text == "We're no strangers to love"


def test_transcript_requests_no_translated_tracks(monkeypatch):
    """Muster wie 'en.*' ziehen Uebersetzungsspuren (z. B. en-de-DE), die in HTTP 429 laufen."""
    calls = []
    monkeypatch.setattr(yt_scraper.subprocess, "run", fake_subs({}, calls))
    yt_scraper.get_transcript("https://www.youtube.com/watch?v=abc", "abc", language="en")
    for cmd in calls:
        langs = cmd[cmd.index("--sub-langs") + 1].split(",")
        assert set(langs) <= {"en", "en-orig"}


def test_transcript_without_known_language_still_avoids_wildcards(monkeypatch):
    calls = []
    monkeypatch.setattr(yt_scraper.subprocess, "run", fake_subs({}, calls))
    yt_scraper.get_transcript("https://www.youtube.com/watch?v=abc", "abc")
    for cmd in calls:
        assert ".*" not in cmd[cmd.index("--sub-langs") + 1]


def test_metadata_includes_language(monkeypatch):
    class Ok(FailedResult):
        returncode = 0
        stdout = '{"id": "abc", "title": "t", "language": "en"}'

    monkeypatch.setattr(yt_scraper.subprocess, "run", lambda cmd, **kw: Ok())
    assert yt_scraper.get_video_metadata("https://www.youtube.com/watch?v=abc")["language"] == "en"
