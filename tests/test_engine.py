from __future__ import annotations

import importlib.util
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from pdf_engine import (  # noqa: E402
    IncorrectPassword,
    MergeCancelled,
    PageSpec,
    PasswordRequired,
    PdfWorkError,
    PdfWorkspace,
    ThumbnailCancelled,
    merge_pages,
)


def make_pdf(
    path: Path,
    widths: list[int],
    user_password: str | None = None,
    owner_password: str | None = None,
) -> Path:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=500)
    if user_password is not None:
        writer.encrypt(user_password, owner_password=owner_password)
    with open(path, "wb") as stream:
        writer.write(stream)
    return path


def page_widths(path: Path, password: str | None = None) -> list[float]:
    reader = PdfReader(str(path))
    if reader.is_encrypted and password is not None:
        reader.decrypt(password)
    return [float(page.mediabox.width) for page in reader.pages]


class WorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="pdf-engine-test-")
        self.root = Path(self.temp.name)
        self.workspace = PdfWorkspace()

    def tearDown(self) -> None:
        self.workspace.close()
        self.temp.cleanup()

    def test_inspect_unencrypted(self) -> None:
        path = make_pdf(self.root / "plain.pdf", [300, 320])
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)

        self.assertEqual(source.status, "ready")
        self.assertEqual(source.page_count, 2)
        self.assertFalse(source.encrypted)
        self.assertEqual(source.working_path, path.resolve())

    def test_password_required_wrong_and_unlock(self) -> None:
        path = make_pdf(
            self.root / "locked.pdf",
            [300, 310, 320],
            user_password="secret",
            owner_password="owner",
        )
        source = self.workspace.add_source(path)

        with self.assertRaises(PasswordRequired):
            self.workspace.inspect(source)
        self.assertEqual(source.status, "locked")

        with self.assertRaises(IncorrectPassword):
            self.workspace.inspect(source, "wrong")
        self.assertEqual(source.status, "locked")

        self.workspace.inspect(source, "secret")
        self.assertEqual(source.status, "ready")
        self.assertEqual(source.page_count, 3)
        self.assertTrue(source.encrypted)
        self.assertNotEqual(source.working_path, source.path.resolve())
        self.assertTrue(source.working_path is not None and source.working_path.exists())
        working_reader = PdfReader(str(source.working_path))
        self.assertFalse(working_reader.is_encrypted)
        self.assertEqual(len(working_reader.pages), 3)

    def test_owner_password_only_opens_without_prompt(self) -> None:
        path = make_pdf(
            self.root / "owner-only.pdf",
            [300, 320],
            user_password="",
            owner_password="owner",
        )
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)
        self.assertEqual(source.status, "ready")
        self.assertEqual(source.page_count, 2)
        self.assertTrue(source.encrypted)

    def test_corrupt_pdf_sets_error(self) -> None:
        path = self.root / "broken.pdf"
        path.write_bytes(b"this is not a pdf")
        source = self.workspace.add_source(path)
        with self.assertRaises(PdfWorkError):
            self.workspace.inspect(source)
        self.assertEqual(source.status, "error")
        self.assertTrue(source.error)

    def test_missing_file_rejected(self) -> None:
        with self.assertRaises(PdfWorkError):
            self.workspace.add_source(self.root / "missing.pdf")

    def test_render_thumbnails(self) -> None:
        path = make_pdf(self.root / "thumbs.pdf", [300, 310, 320])
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)
        thumbnails = self.workspace.render_thumbnails(source, width=160)
        self.assertEqual(len(thumbnails), 3)
        for thumbnail in thumbnails:
            self.assertTrue(thumbnail.exists())
            self.assertGreater(thumbnail.stat().st_size, 100)
            self.assertEqual(thumbnail.suffix, ".jpg")

    def test_render_thumbnails_honours_cancellation(self) -> None:
        path = make_pdf(self.root / "cancel.pdf", [300, 310])
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(ThumbnailCancelled):
            self.workspace.render_thumbnails(source, cancel_event=cancel)

    @unittest.skipUnless(
        importlib.util.find_spec("pypdfium2") is not None
        and importlib.util.find_spec("PIL") is not None,
        "pypdfium2 and Pillow are not installed",
    )
    def test_render_thumbnails_pdfium_backend(self) -> None:
        from PIL import Image

        path = make_pdf(self.root / "pdfium.pdf", [300, 310, 320])
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)
        thumbnails = self.workspace.render_thumbnails(
            source, width=120, backend="pdfium"
        )
        self.assertEqual(len(thumbnails), 3)
        for thumbnail in thumbnails:
            self.assertTrue(thumbnail.exists())
            with Image.open(thumbnail) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertLessEqual(max(image.size), 120)

    @unittest.skipUnless(
        importlib.util.find_spec("pypdfium2") is not None
        and importlib.util.find_spec("PIL") is not None,
        "pypdfium2 and Pillow are not installed",
    )
    def test_pdfium_thumbnails_honour_cancellation(self) -> None:
        path = make_pdf(self.root / "pdfium-cancel.pdf", [300, 310])
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(ThumbnailCancelled):
            self.workspace.render_thumbnails(
                source, backend="pdfium", cancel_event=cancel
            )

    @unittest.skipUnless(
        importlib.util.find_spec("pypdfium2") is not None
        and importlib.util.find_spec("PIL") is not None,
        "pypdfium2 and Pillow are not installed",
    )
    def test_pdfium_calls_are_serialized_across_threads(self) -> None:
        barrier = threading.Barrier(2)
        workspaces = []
        sources = []
        errors: list[BaseException] = []

        try:
            for index in range(2):
                workspace = PdfWorkspace()
                source = workspace.add_source(
                    make_pdf(self.root / f"threaded-{index}.pdf", [300, 310])
                )
                workspace.inspect(source)
                workspaces.append(workspace)
                sources.append(source)

            def render(workspace: PdfWorkspace, source) -> None:
                try:
                    barrier.wait(timeout=10)
                    workspace.render_thumbnails(
                        source, width=100, backend="pdfium"
                    )
                except BaseException as exc:  # collected for the main thread
                    errors.append(exc)

            threads = [
                threading.Thread(target=render, args=(workspace, source))
                for workspace, source in zip(workspaces, sources)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)

            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
        finally:
            for workspace in workspaces:
                workspace.close()

    def test_remove_source_and_cleanup(self) -> None:
        path = make_pdf(
            self.root / "cleanup.pdf",
            [300, 310],
            user_password="secret",
            owner_password="owner",
        )
        source = self.workspace.add_source(path)
        self.workspace.inspect(source, "secret")
        working = source.working_path
        self.assertTrue(working is not None and working.exists())
        self.workspace.remove_source(source.id)
        self.assertNotIn(source.id, self.workspace.sources)
        self.assertFalse(working.exists())

    def test_workspace_close_removes_temp_root(self) -> None:
        root = self.workspace.temp_root
        path = make_pdf(self.root / "closed.pdf", [300])
        source = self.workspace.add_source(path)
        self.workspace.inspect(source)
        self.workspace.close()
        self.assertFalse(root.exists())


class MergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="pdf-merge-test-")
        self.root = Path(self.temp.name)
        self.a = make_pdf(self.root / "a.pdf", [300, 310])
        self.b = make_pdf(self.root / "b.pdf", [320, 330])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_merge_page_order(self) -> None:
        output = self.root / "merged.pdf"
        specs = [
            PageSpec(self.b, 1, "b.pdf"),
            PageSpec(self.a, 0, "a.pdf"),
            PageSpec(self.a, 1, "a.pdf"),
            PageSpec(self.b, 0, "b.pdf"),
        ]
        progress: list[tuple[int, int]] = []
        result = merge_pages(
            specs, output, progress=lambda current, total: progress.append((current, total))
        )
        self.assertEqual(result, output)
        self.assertEqual(page_widths(output), [330, 300, 310, 320])
        self.assertEqual(progress[0], (0, 4))
        self.assertEqual(progress[-1], (4, 4))
        reader = PdfReader(str(output))
        self.assertEqual(reader.metadata.title, "merged")
        self.assertFalse(reader.is_encrypted)
        self.assertEqual(list(self.root.glob(".pdf-page-merger-*")), [])

    def test_merge_duplicate_pages(self) -> None:
        output = self.root / "duplicate.pdf"
        merge_pages(
            [PageSpec(self.a, 0, "a.pdf"), PageSpec(self.a, 0, "a.pdf")],
            output,
        )
        self.assertEqual(page_widths(output), [300, 300])

    def test_cancelled_merge_leaves_no_output(self) -> None:
        output = self.root / "cancelled.pdf"
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(MergeCancelled):
            merge_pages(
                [PageSpec(self.a, 0, "a.pdf")],
                output,
                cancel_event=cancel,
            )
        self.assertFalse(output.exists())

    def test_merge_refuses_to_overwrite_source(self) -> None:
        original = page_widths(self.a)
        with self.assertRaises(PdfWorkError):
            merge_pages([PageSpec(self.a, 0, "a.pdf")], self.a)
        self.assertEqual(page_widths(self.a), original)

    def test_empty_merge_rejected(self) -> None:
        with self.assertRaises(PdfWorkError):
            merge_pages([], self.root / "empty.pdf")

    def test_unreadable_source_cleans_partial_output(self) -> None:
        bad = self.root / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        output = self.root / "bad-output.pdf"
        with self.assertRaises(PdfWorkError):
            merge_pages([PageSpec(self.a, 0, "a.pdf"), PageSpec(bad, 0, "bad.pdf")], output)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".pdf-page-merger-*")), [])


class IntegrationWithSamplesTests(unittest.TestCase):
    samples = PROJECT / "tests" / "samples"

    def test_encrypted_sample_can_be_unlocked_and_merged(self) -> None:
        if not (self.samples / "機密_董事會附件.pdf").exists():
            self.skipTest("sample PDFs have not been generated")
        with tempfile.TemporaryDirectory(prefix="pdf-sample-test-") as temp:
            workspace = PdfWorkspace()
            try:
                source = workspace.add_source(self.samples / "機密_董事會附件.pdf")
                with self.assertRaises(PasswordRequired):
                    workspace.inspect(source)
                workspace.inspect(source, "open123")
                self.assertEqual(source.page_count, 2)
                report = workspace.add_source(self.samples / "季度營運報告.pdf")
                workspace.inspect(report)
                output = Path(temp) / "sample-merged.pdf"
                merge_pages(
                    [
                        PageSpec(source.working_path, 1, source.name),
                        PageSpec(report.working_path, 0, report.name),
                    ],
                    output,
                )
                reader = PdfReader(str(output))
                self.assertEqual(len(reader.pages), 2)
            finally:
                workspace.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
