#!/usr/bin/env python3
"""YouTube Scraper with dual mode: search queries and batch URL processing.

Uses yt-dlp to extract metadata and transcripts/subtitles from YouTube videos.

Usage:
    # Search mode
    python yt_scraper.py search "machine learning 2026" --max-results 10

    # Batch URL mode
    python yt_scraper.py urls https://youtube.com/watch?v=xxx https://youtube.com/watch?v=yyy

    # Batch URL mode from file (one URL per line)
    python yt_scraper.py urls --from-file urls.txt
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a string."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:120]


def search_youtube(query: str, max_results: int = 10) -> list[dict]:
    """Search YouTube and return video metadata."""
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json",
        "--no-download",
        "--flat-playlist",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] yt-dlp search failed: {result.stderr}", file=sys.stderr)
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            videos.append(
                {
                    "id": data.get("id", ""),
                    "url": data.get("url") or f"https://www.youtube.com/watch?v={data.get('id', '')}",
                    "title": data.get("title", "Unknown"),
                    "channel": data.get("channel") or data.get("uploader", "Unknown"),
                    "view_count": data.get("view_count", 0),
                    "duration": data.get("duration", 0),
                    "upload_date": data.get("upload_date", ""),
                }
            )
        except json.JSONDecodeError:
            continue
    return videos


def get_video_metadata(url: str) -> dict | None:
    """Extract full metadata for a single video URL."""
    cmd = [
        "yt-dlp",
        url,
        "--dump-json",
        "--no-download",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[WARN] Metadata extraction failed for {url}: {result.stderr}", file=sys.stderr)
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    return {
        "id": data.get("id", ""),
        "url": url,
        "title": data.get("title", "Unknown"),
        "channel": data.get("channel") or data.get("uploader", "Unknown"),
        "view_count": data.get("view_count", 0),
        "duration": data.get("duration", 0),
        "duration_string": data.get("duration_string", ""),
        "upload_date": data.get("upload_date", ""),
        "description": data.get("description", ""),
        "categories": data.get("categories", []),
        "tags": data.get("tags", []),
        "like_count": data.get("like_count", 0),
        "comment_count": data.get("comment_count", 0),
    }


def get_transcript(url: str, video_id: str) -> str | None:
    """Extract transcript/subtitles for a video. Tries auto-subs if manual unavailable."""
    # Try multiple subtitle strategies
    strategies = [
        # 1. Manual subtitles (preferred)
        ["--write-subs", "--sub-langs", "en,de,en.*,de.*"],
        # 2. Auto-generated subtitles
        ["--write-auto-subs", "--sub-langs", "en,de,en.*,de.*"],
    ]

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        for sub_args in strategies:
            cmd = [
                "yt-dlp",
                url,
                "--skip-download",
                *sub_args,
                "--sub-format", "vtt/srt/best",
                "--convert-subs", "srt",
                "-o", os.path.join(tmpdir, "%(id)s.%(ext)s"),
            ]
            subprocess.run(cmd, capture_output=True, text=True)

            # Look for subtitle files
            for f in Path(tmpdir).glob(f"{video_id}*.srt"):
                return _parse_srt(f.read_text(encoding="utf-8", errors="replace"))
            for f in Path(tmpdir).glob(f"{video_id}*.vtt"):
                return _parse_vtt(f.read_text(encoding="utf-8", errors="replace"))

    return None


def _parse_srt(content: str) -> str:
    """Extract plain text from SRT subtitle content."""
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        # Skip sequence numbers, timestamps, and empty lines
        if not line or re.match(r"^\d+$", line) or "-->" in line:
            continue
        # Strip HTML tags
        clean = re.sub(r"<[^>]+>", "", line)
        if clean:
            lines.append(clean)
    # Deduplicate consecutive identical lines (common in auto-subs)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


def _parse_vtt(content: str) -> str:
    """Extract plain text from VTT subtitle content."""
    lines = []
    header_passed = False
    for line in content.split("\n"):
        line = line.strip()
        if not header_passed:
            if line == "":
                header_passed = True
            continue
        if not line or "-->" in line or line.startswith("NOTE"):
            continue
        clean = re.sub(r"<[^>]+>", "", line)
        if clean:
            lines.append(clean)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "Unknown"
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_date(date_str: str) -> str:
    """Format YYYYMMDD into readable date."""
    if not date_str or len(date_str) != 8:
        return date_str or "Unknown"
    try:
        return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def process_videos(videos: list[dict], run_dir: Path) -> list[dict]:
    """Process a list of videos: fetch full metadata + transcripts, save to files."""
    results = []
    total = len(videos)

    for i, video in enumerate(videos, 1):
        url = video["url"]
        vid_id = video.get("id", "")
        title = video.get("title", "Unknown")
        print(f"[{i}/{total}] Processing: {title}")

        # Get full metadata if not already present
        if "description" not in video:
            meta = get_video_metadata(url)
            if meta:
                video.update(meta)
                vid_id = video["id"]

        # Get transcript
        print(f"  -> Extracting transcript...")
        transcript = get_transcript(url, vid_id)

        video["transcript"] = transcript
        video["has_transcript"] = transcript is not None

        # Save individual transcript file
        safe_name = sanitize_filename(f"{vid_id}_{video.get('title', 'unknown')}")
        transcript_file = run_dir / f"{safe_name}.md"

        md_content = f"""# {video.get('title', 'Unknown')}

## Metadata
- **Channel:** {video.get('channel', 'Unknown')}
- **URL:** {video.get('url', '')}
- **Duration:** {format_duration(video.get('duration', 0))}
- **Views:** {video.get('view_count', 0):,}
- **Upload Date:** {format_date(video.get('upload_date', ''))}
- **Likes:** {(video.get('like_count') or 0):,}
- **Comments:** {(video.get('comment_count') or 0):,}

## Description
{video.get('description', 'N/A')}

## Transcript
{transcript if transcript else '*No transcript available for this video.*'}
"""
        transcript_file.write_text(md_content, encoding="utf-8")
        video["file_path"] = str(transcript_file)
        results.append(video)
        print(f"  -> Saved: {transcript_file.name}")

    return results


def save_index(results: list[dict], run_dir: Path, query: str | None = None):
    """Save an index/summary file for the run."""
    index_file = run_dir / "_index.json"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "total_videos": len(results),
        "videos_with_transcript": sum(1 for v in results if v.get("has_transcript")),
        "videos": [
            {
                "id": v.get("id"),
                "title": v.get("title"),
                "channel": v.get("channel"),
                "url": v.get("url"),
                "duration": v.get("duration"),
                "view_count": v.get("view_count"),
                "upload_date": v.get("upload_date"),
                "has_transcript": v.get("has_transcript"),
                "file_path": v.get("file_path"),
            }
            for v in results
        ],
    }
    index_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nIndex saved: {index_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="YouTube Scraper - Search & Batch URL modes")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Search mode
    search_parser = subparsers.add_parser("search", help="Search YouTube for videos")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max-results", "-n", type=int, default=10, help="Max results (default: 10)")

    # URL batch mode
    url_parser = subparsers.add_parser("urls", help="Process specific YouTube URLs")
    url_parser.add_argument("video_urls", nargs="*", help="YouTube video URLs")
    url_parser.add_argument("--from-file", "-f", help="Read URLs from file (one per line)")

    # Common args (added to each subparser so they work after the subcommand)
    for sp in [search_parser, url_parser]:
        sp.add_argument("--output-dir", "-o", help="Override output directory")
        sp.add_argument("--json-only", action="store_true", help="Also output JSON index to stdout")

    args = parser.parse_args()

    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR

    if args.mode == "search":
        run_name = f"{timestamp}_search_{sanitize_filename(args.query)}"
        run_dir = base_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        print(f"Searching YouTube for: '{args.query}' (max {args.max_results} results)")
        videos = search_youtube(args.query, args.max_results)
        if not videos:
            print("No results found.")
            sys.exit(1)

        print(f"Found {len(videos)} videos. Processing...\n")
        results = process_videos(videos, run_dir)
        summary = save_index(results, run_dir, query=args.query)

    elif args.mode == "urls":
        urls = list(args.video_urls) if args.video_urls else []
        if args.from_file:
            with open(args.from_file) as f:
                urls.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))

        if not urls:
            print("No URLs provided. Pass URLs as arguments or use --from-file.", file=sys.stderr)
            sys.exit(1)

        run_name = f"{timestamp}_batch_{len(urls)}videos"
        run_dir = base_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        videos = [{"url": url, "id": ""} for url in urls]
        print(f"Processing {len(urls)} URLs...\n")
        results = process_videos(videos, run_dir)
        summary = save_index(results, run_dir)

    # Print summary
    print(f"\n{'='*60}")
    print(f"DONE: {summary['total_videos']} videos processed")
    print(f"  With transcripts: {summary['videos_with_transcript']}")
    print(f"  Output directory:  {run_dir}")
    print(f"{'='*60}")

    if args.json_only:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
