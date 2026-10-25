"""PDF operations for the desktop page merger.

The UI depends on this module for reading, unlocking, rendering thumbnails
and writing merged documents. Keeping these operations free of Qt makes them
straightforward to test.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from pypdf import PdfReader, PdfWriter
from pypdf.errors import FileNotDecryptedError, PdfReadError


class PdfWorkError(Exception):
    """An error that can be shown to the user as-is."""


class PasswordRequired(PdfWorkError):
    def __init__(self) -> None:
        super().__init__("這份 PDF 已加密，需要輸入密碼。")


class IncorrectPassword(PdfWorkError):
    def __init__(self) -> None:
        super().__init__("密碼不正確，請再試一次。")


class MergeCancelled(Exception):
    """Raised internally when the user cancels a merge."""


class ThumbnailCancelled(Exception):
    """Raised internally when a thumbnail job is cancelled."""


@dataclass
class PdfSource:
    id: str
    path: Path
    name: str
    page_count: int = 0
    encrypted: bool = False
    status: str = "new"  # new | ready | locked | error
    working_path: Path | None = None
    error: str | None = None

    @property
    def is_ready(self) -> bool:
        return self.status == "ready" and self.working_path is not None


@dataclass(frozen=True)
class PageSpec:
    source_path: Path
    page_index: int
    source_name: str = ""


def _friendly_error(exc: BaseException) -> str:
    if isinstance(exc, FileNotFoundError):
        return "找不到檔案，可能已被移動或刪除。"
    if isinstance(exc, PermissionError):
        return "沒有權限讀取這個檔案。"
    if isinstance(exc, PdfReadError):
        return "無法讀取 PDF，檔案可能已損毀或格式不受支援。"
    message = str(exc).strip()
    if message:
        return f"讀取 PDF 失敗：{message}"
    return "讀取 PDF 失敗。"


class PdfWorkspace:
    """Owns loaded sources and all decrypted/temporary copies."""

    def __init__(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="pdf-page-merger-"))
        self._thumbs_root = self.temp_root / "thumbs"
        self._thumbs_root.mkdir(parents=True, exist_ok=True)
        self.sources: dict[str, PdfSource] = {}
        self._closed = False

    def add_source(self, path: str | Path) -> PdfSource:
        source_path = Path(path).expanduser()
        if not source_path.is_file():
            raise PdfWorkError("找不到檔案，可能已被移動或刪除。")
        try:
            source_path = source_path.resolve()
        except OSError:
            pass
        source = PdfSource(
            id=uuid.uuid4().hex,
            path=source_path,
            name=source_path.name,
        )
        self.sources[source.id] = source
        return source

    def inspect(self, source: PdfSource, password: str | None = None) -> None:
        """Read a PDF, unlock it if needed and create a working copy.

        Raises PasswordRequired when a password is needed and none was given,
        or IncorrectPassword when the supplied password does not open the file.
        """
        if source.id not in self.sources:
            raise PdfWorkError("這份 PDF 已從清單移除。")

        stream = None
        try:
            stream = open(source.path, "rb")
            reader = PdfReader(stream, strict=False)
            reader_encrypted = bool(reader.is_encrypted)

            if reader_encrypted:
                try:
                    opened = reader.decrypt(password or "")
                except Exception as exc:  # unsupported/broken encryption
                    source.status = "error"
                    source.error = "無法解密這份 PDF，可能使用了不支援的加密方式。"
                    raise PdfWorkError(source.error) from exc

                if not opened:
                    source.encrypted = True
                    source.status = "locked"
                    source.working_path = None
                    source.page_count = 0
                    if password is None:
                        raise PasswordRequired()
                    raise IncorrectPassword()

            page_count = len(reader.pages)
            if page_count == 0:
                source.status = "error"
                source.error = "這份 PDF 沒有任何頁面。"
                raise PdfWorkError(source.error)

            working_path = source.path
            if reader_encrypted:
                working_path = self.temp_root / f"decrypted-{source.id}.pdf"
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                try:
                    if reader.metadata and reader.metadata.title:
                        writer.add_metadata({"/Title": str(reader.metadata.title)})
                except Exception:
                    pass
                with open(working_path, "wb") as output:
                    writer.write(output)

            source.encrypted = reader_encrypted
            source.page_count = page_count
            source.working_path = working_path
            source.status = "ready"
            source.error = None
        except (PasswordRequired, IncorrectPassword):
            raise
        except PdfWorkError:
            raise
        except FileNotDecryptedError as exc:
            source.status = "locked"
            source.error = None
            raise PasswordRequired() from exc
        except Exception as exc:
            source.status = "error"
            source.error = _friendly_error(exc)
            raise PdfWorkError(source.error) from exc
        finally:
            if stream is not None:
                stream.close()

    def remove_source(self, source_id: str) -> None:
        source = self.sources.pop(source_id, None)
        if source is None:
            return
        if (
            source.encrypted
            and source.working_path
            and source.working_path.is_relative_to(self.temp_root)
        ):
            try:
                source.working_path.unlink(missing_ok=True)
            except OSError:
                pass
        shutil.rmtree(self._thumbs_root / source_id, ignore_errors=True)

    def thumbnail_dir(self, source_id: str) -> Path:
        path = self._thumbs_root / source_id
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def render_thumbnails(
        self,
        source: PdfSource,
        width: int = 360,
        cancel_event: threading.Event | None = None,
        backend: str = "auto",
    ) -> list[Path]:
        """Render every page to a compact JPEG and return the paths in order.

        The default backend uses pdftoppm when it is available and otherwise
        falls back to the bundled PDFium renderer. The fallback makes the
        Windows build independent of an external poppler installation.
        """
        if not source.is_ready or source.working_path is None:
            raise PdfWorkError("這份 PDF 尚未解鎖。")
        if cancel_event is not None and cancel_event.is_set():
            raise ThumbnailCancelled()
        if width <= 0:
            raise PdfWorkError("縮圖尺寸無效。")

        tool = shutil.which("pdftoppm")
        if backend == "auto":
            backend = "poppler" if tool else "pdfium"
        output_dir = self.thumbnail_dir(source.id)

        if backend == "poppler":
            if not tool:
                raise PdfWorkError("找不到縮圖工具 pdftoppm，請安裝 poppler-utils。")
            return self._render_thumbnails_poppler(
                source, output_dir, width, cancel_event, tool
            )
        if backend == "pdfium":
            return self._render_thumbnails_pdfium(
                source, output_dir, width, cancel_event
            )
        raise ValueError(f"Unknown thumbnail backend: {backend}")

    def _render_thumbnails_poppler(
        self,
        source: PdfSource,
        output_dir: Path,
        width: int,
        cancel_event: threading.Event | None,
        tool: str,
    ) -> list[Path]:
        prefix = output_dir / "page"
        command = [
            tool,
            "-jpeg",
            "-jpegopt",
            "quality=85",
            "-scale-to",
            str(width),
            "-f",
            "1",
            "-l",
            str(source.page_count),
            str(source.working_path),
            str(prefix),
        ]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            raise PdfWorkError("無法啟動縮圖工具，但 PDF 仍可直接合併。") from exc

        stderr = b""
        deadline = time.monotonic() + 600
        try:
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    process.terminate()
                    try:
                        _, stderr = process.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        _, stderr = process.communicate()
                    raise ThumbnailCancelled()
                if time.monotonic() > deadline:
                    process.terminate()
                    try:
                        process.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                    raise PdfWorkError("產生縮圖逾時，但 PDF 仍可直接合併。")
                try:
                    _, stderr = process.communicate(timeout=0.15)
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

        if cancel_event is not None and cancel_event.is_set():
            raise ThumbnailCancelled()
        if process.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            if detail:
                raise PdfWorkError(f"無法產生縮圖：{detail.splitlines()[-1]}")
            raise PdfWorkError("無法產生縮圖，但 PDF 仍可直接合併。")

        files = sorted(
            output_dir.glob("page-*.jpg"),
            key=lambda path: int(match.group(1))
            if (match := re.search(r"page-(\d+)\.jpg$", path.name))
            else 0,
        )
        if not files:
            raise PdfWorkError("沒有產生任何縮圖，但 PDF 仍可直接合併。")
        return files[: source.page_count]

    def _render_thumbnails_pdfium(
        self,
        source: PdfSource,
        output_dir: Path,
        width: int,
        cancel_event: threading.Event | None,
    ) -> list[Path]:
        try:
            import pypdfium2 as pdfium
            from PIL import Image  # noqa: F401  (PyInstaller must collect Pillow)
        except ImportError as exc:
            raise PdfWorkError(
                "找不到縮圖工具。請安裝 poppler-utils，或安裝 pypdfium2 與 Pillow。"
            ) from exc

        document = None
        paths: list[Path] = []
        try:
            document = pdfium.PdfDocument(str(source.working_path))
            page_count = min(source.page_count, len(document))
            if page_count <= 0:
                raise PdfWorkError("沒有可產生縮圖的頁面。")

            for page_index in range(page_count):
                if cancel_event is not None and cancel_event.is_set():
                    raise ThumbnailCancelled()
                page = None
                bitmap = None
                image = None
                try:
                    page = document[page_index]
                    page_width, page_height = page.get_size()
                    longest_side = max(page_width, page_height)
                    if longest_side <= 0:
                        raise PdfWorkError("頁面尺寸無效，無法產生縮圖。")
                    bitmap = page.render(scale=width / longest_side)
                    image = bitmap.to_pil()
                    output_path = output_dir / f"page-{page_index + 1}.jpg"
                    image.save(output_path, "JPEG", quality=85)
                    paths.append(output_path)
                finally:
                    if image is not None:
                        image.close()
                    if bitmap is not None:
                        bitmap.close()
                    if page is not None:
                        page.close()

            if cancel_event is not None and cancel_event.is_set():
                raise ThumbnailCancelled()
            if not paths:
                raise PdfWorkError("沒有產生任何縮圖，但 PDF 仍可直接合併。")
            return paths
        except (ThumbnailCancelled, PdfWorkError):
            raise
        except Exception as exc:
            raise PdfWorkError(f"無法產生縮圖：{exc}") from exc
        finally:
            if document is not None:
                document.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for source_id in list(self.sources):
            self.remove_source(source_id)
        shutil.rmtree(self.temp_root, ignore_errors=True)


def merge_pages(
    pages: Sequence[PageSpec],
    output: str | Path,
    progress: Callable[[int, int], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> Path:
    """Merge pages in the given order into a new, unencrypted PDF."""
    if not pages:
        raise PdfWorkError("目前沒有可合併的頁面。")

    target = Path(output).expanduser()
    if not target.parent.is_dir():
        raise PdfWorkError("輸出資料夾不存在，請選擇其他位置。")
    target_resolved = target.resolve()
    for page in pages:
        try:
            if page.source_path.resolve() == target_resolved:
                raise PdfWorkError("輸出檔不可覆蓋來源 PDF，請改用其他檔名。")
        except OSError:
            pass

    total = len(pages)
    writer = PdfWriter()
    streams = []
    readers: dict[Path, PdfReader] = {}
    temporary_path: Path | None = None

    def check_cancelled() -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise MergeCancelled()

    try:
        if progress:
            progress(0, total)
        for current, page in enumerate(pages, start=1):
            check_cancelled()
            try:
                reader = readers.get(page.source_path)
                if reader is None:
                    stream = open(page.source_path, "rb")
                    streams.append(stream)
                    reader = PdfReader(stream, strict=False)
                    if reader.is_encrypted:
                        raise PdfWorkError("來源 PDF 需要密碼，請重新解鎖後再試。")
                    readers[page.source_path] = reader
                if page.page_index < 0 or page.page_index >= len(reader.pages):
                    raise PdfWorkError(
                        f"「{page.source_name or page.source_path.name}」的頁面已變更。"
                    )
                writer.add_page(reader.pages[page.page_index])
            except PdfWorkError:
                raise
            except Exception as exc:
                label = page.source_name or page.source_path.name
                raise PdfWorkError(f"合併「{label}」時發生錯誤：{exc}") from exc
            if progress:
                progress(current, total)

        check_cancelled()
        writer.add_metadata(
            {
                "/Title": target.stem,
                "/Creator": "PDF 併頁器",
                "/Producer": "PDF 併頁器",
            }
        )

        handle, temp_name = tempfile.mkstemp(
            prefix=".pdf-page-merger-", suffix=".tmp.pdf", dir=target.parent
        )
        os.close(handle)
        temporary_path = Path(temp_name)
        with open(temporary_path, "wb") as output_stream:
            writer.write(output_stream)
            output_stream.flush()
            os.fsync(output_stream.fileno())
        check_cancelled()
        os.replace(temporary_path, target)
        temporary_path = None
        return target
    except MergeCancelled:
        raise
    except PdfWorkError:
        raise
    except Exception as exc:
        raise PdfWorkError(f"儲存合併檔時發生錯誤：{exc}") from exc
    finally:
        for stream in streams:
            try:
                stream.close()
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
