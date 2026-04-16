import pytest
from unittest.mock import patch, MagicMock
from videotagger.core.video_merger import VideoMerger, MergeError


@pytest.fixture
def merger():
    return VideoMerger(ffmpeg_path="ffmpeg")


def test_single_file_copies_in_place(tmp_path, merger):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"fake video data")
    dst = tmp_path / "out.mp4"
    merger.merge([str(src)], str(dst))
    assert dst.exists()
    assert dst.read_bytes() == b"fake video data"


def _make_mock_proc(returncode: int):
    proc = MagicMock()
    proc.stderr = iter([])
    proc.returncode = returncode
    proc.poll.return_value = returncode
    return proc


def test_multiple_files_tries_copy_first(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"

    with patch("subprocess.Popen", return_value=_make_mock_proc(0)) as mock_popen:
        merger.merge([str(src1), str(src2)], str(dst))

    cmd = mock_popen.call_args[0][0]
    assert "-c" in cmd
    assert "copy" in cmd


def test_falls_back_to_h264_when_copy_fails(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"

    call_count = 0

    def side_effect(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        return _make_mock_proc(1 if call_count == 1 else 0)

    with patch("subprocess.Popen", side_effect=side_effect):
        merger.merge([str(src1), str(src2)], str(dst))

    assert call_count == 2


def test_raises_merge_error_when_both_passes_fail(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"

    with patch("subprocess.Popen", return_value=_make_mock_proc(1)):
        with pytest.raises(MergeError):
            merger.merge([str(src1), str(src2)], str(dst))


def test_progress_callback_called(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"
    messages = []

    with patch("subprocess.Popen", return_value=_make_mock_proc(0)):
        merger.merge([str(src1), str(src2)], str(dst), on_progress=messages.append)

    assert any("pass 1" in m.lower() or "copy" in m.lower() for m in messages)
