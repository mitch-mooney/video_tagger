from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Callable, List


class MergeError(Exception):
    pass


class VideoMerger:
    """Merges multiple video files into one using FFmpeg concat demuxer.

    Tries -c copy (lossless, fast) first. Falls back to H.264/AAC transcode
    if sources have mismatched codecs.
    """

    def __init__(self, ffmpeg_path: str):
        self._ffmpeg = ffmpeg_path
        self._proc: subprocess.Popen | None = None

    def merge(
        self,
        sources: List[str],
        output: str,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        """Merge sources into output.

        Single source: copied directly (no FFmpeg needed).
        Multiple sources: concat demuxer with copy, then H.264 fallback.
        Raises MergeError if FFmpeg fails on both passes.
        """
        if len(sources) == 1:
            shutil.copy2(sources[0], output)
            return

        fd, filelist_path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for src in sources:
                    escaped = src.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            base_cmd = [
                self._ffmpeg, "-y", "-f", "concat", "-safe", "0",
                "-i", filelist_path,
            ]

            if on_progress:
                on_progress("Merging — pass 1: copy (fast)…")
            if self._run(base_cmd + ["-c", "copy", output], on_progress):
                return

            if on_progress:
                on_progress("Copy pass failed — re-encoding to H.264…")
            if self._run(
                base_cmd + ["-c:v", "libx264", "-crf", "18", "-c:a", "aac", output],
                on_progress,
            ):
                return

            raise MergeError(
                "FFmpeg failed to merge the video files on both passes. "
                "Check that all source files are valid and not corrupted."
            )
        finally:
            if os.path.exists(filelist_path):
                os.unlink(filelist_path)

    def cancel(self) -> None:
        """Terminate a running FFmpeg process."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def _run(
        self,
        cmd: List[str],
        on_progress: Callable[[str], None] | None,
    ) -> bool:
        self._proc = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in self._proc.stderr:
            if on_progress and "time=" in line:
                for part in line.split():
                    if part.startswith("time="):
                        on_progress(f"Processed: {part[5:]}")
                        break
        self._proc.wait()
        return self._proc.returncode == 0
