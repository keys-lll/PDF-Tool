"""Background jobs used by the desktop UI."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from pdf_engine import (
    MergeCancelled,
    PageSpec,
    PdfSource,
    PdfWorkError,
    PdfWorkspace,
    ThumbnailCancelled,
    merge_pages,
)


class ThumbnailSignals(QObject):
    finished = Signal(str, object)  # source id, list[str]
    failed = Signal(str, str)  # source id, message


class ThumbnailWorker(QRunnable):
    def __init__(self, workspace: PdfWorkspace, source: PdfSource) -> None:
        super().__init__()
        self.signals = ThumbnailSignals()
        self._workspace = workspace
        self._source = source
        self._cancel_event = threading.Event()
        self.source_id = source.id
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self._cancel_event.set()

    @Slot()
    def run(self) -> None:
        try:
            paths = self._workspace.render_thumbnails(
                self._source, cancel_event=self._cancel_event
            )
        except ThumbnailCancelled:
            return
        except PdfWorkError as exc:
            if self._cancel_event.is_set():
                return
            self.signals.failed.emit(self.source_id, str(exc))
        except Exception:
            if self._cancel_event.is_set():
                return
            self.signals.failed.emit(
                self.source_id, "產生縮圖時發生未預期的錯誤，但 PDF 仍可合併。"
            )
        else:
            if not self._cancel_event.is_set():
                self.signals.finished.emit(
                    self.source_id, [str(path) for path in paths]
                )


class MergeSignals(QObject):
    progress = Signal(int, int)
    succeeded = Signal(str)
    failed = Signal(str)
    cancelled = Signal()


class MergeWorker(QRunnable):
    def __init__(self, pages: list[PageSpec], output: Path) -> None:
        super().__init__()
        self.signals = MergeSignals()
        self._pages = pages
        self._output = output
        self._cancel_event = threading.Event()
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self._cancel_event.set()

    def _emit_progress(self, current: int, total: int) -> None:
        step = max(1, total // 200)
        if current in (0, total) or current % step == 0:
            self.signals.progress.emit(current, total)

    @Slot()
    def run(self) -> None:
        try:
            result = merge_pages(
                self._pages,
                self._output,
                progress=self._emit_progress,
                cancel_event=self._cancel_event,
            )
        except MergeCancelled:
            self.signals.cancelled.emit()
        except PdfWorkError as exc:
            self.signals.failed.emit(str(exc))
        except Exception:
            self.signals.failed.emit("合併時發生未預期的錯誤，請再試一次。")
        else:
            self.signals.succeeded.emit(str(result))
