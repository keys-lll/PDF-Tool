#!/usr/bin/env bash
#
# 在完成 `gh auth login` 之後，建立 GitHub 倉庫、推送 main 與 v1.1.0，
# 並建立附帶 .deb 的 GitHub Release。
#
# 用法：
#   ./packaging/publish-github.sh
#   VISIBILITY=public ./packaging/publish-github.sh
#   REPO_NAME=my-pdf-merger ./packaging/publish-github.sh
#
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$ROOT_DIR"

REPO_NAME="${REPO_NAME:-pdf-page-merger}"
VISIBILITY="${VISIBILITY:-private}"
TAG="v1.1.0"
DEB="$ROOT_DIR/dist/pdf-page-merger_1.1.0-1_all.deb"
SUMS="$ROOT_DIR/dist/SHA256SUMS"
WINDOWS_ZIP="$ROOT_DIR/dist/PDF-Page-Merger-1.1.0-windows-x64.zip"
NOTES="$ROOT_DIR/docs/release-notes-v1.1.0.md"
DESCRIPTION="PDF 併頁器 — merge PDFs and reorder pages with per-file password support"

case "$VISIBILITY" in
    private) VISIBILITY_FLAG="--private" ;;
    public) VISIBILITY_FLAG="--public" ;;
    *)
        echo "VISIBILITY 只能是 private 或 public（目前：$VISIBILITY）" >&2
        exit 1
        ;;
esac

if ! command -v gh >/dev/null 2>&1; then
    echo "找不到 GitHub CLI。請先安裝並登入：" >&2
    echo "  sudo apt install gh" >&2
    echo "  gh auth login" >&2
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "尚未登入 GitHub CLI。請先執行：" >&2
    echo "  gh auth login" >&2
    exit 1
fi

if [ ! -d .git ]; then
    echo "目前資料夾不是 Git 倉庫。" >&2
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "工作區有未提交的變更，請先提交後再發佈：" >&2
    git status --short >&2
    exit 1
fi

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" != "main" ]; then
    echo "目前分支是「$BRANCH」，請切到 main 後再發佈。" >&2
    exit 1
fi

if ! git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null; then
    echo "找不到標籤 $TAG，請先建立版本標籤。" >&2
    exit 1
fi

if [ ! -f "$DEB" ]; then
    echo "找不到 .deb，先重新建置…"
    "$ROOT_DIR/packaging/build-deb.sh"
fi
if [ ! -f "$SUMS" ]; then
    echo "找不到 SHA256SUMS，請重新建置 .deb。" >&2
    exit 1
fi
(cd "$ROOT_DIR/dist" && sha256sum -c SHA256SUMS >/dev/null)
if [ ! -f "$NOTES" ]; then
    echo "找不到發佈說明：$NOTES" >&2
    exit 1
fi

ASSETS=("$DEB" "$SUMS")
if [ -f "$WINDOWS_ZIP" ]; then
    ASSETS+=("$WINDOWS_ZIP")
else
    echo "提示：找不到 Windows zip，將只發佈 Linux 套件。"
fi

if git remote get-url origin >/dev/null 2>&1; then
    echo "使用既有 origin：$(git remote get-url origin)"
    git push -u origin main
else
    echo "建立 GitHub 倉庫 $REPO_NAME（$VISIBILITY）…"
    gh repo create "$REPO_NAME" "$VISIBILITY_FLAG" \
        --source="$ROOT_DIR" \
        --remote=origin \
        --push \
        --description="$DESCRIPTION"
fi

git push origin "$TAG"

if gh release view "$TAG" >/dev/null 2>&1; then
    echo "Release $TAG 已存在，更新說明與附件…"
    gh release edit "$TAG" \
        --title="PDF 併頁器 $TAG" \
        --notes-file="$NOTES"
    gh release upload "$TAG" "${ASSETS[@]}" --clobber
else
    echo "建立 Release $TAG…"
    gh release create "$TAG" "${ASSETS[@]}" \
        --title="PDF 併頁器 $TAG" \
        --notes-file="$NOTES" \
        --verify-tag
fi

echo
echo "發佈完成。"
gh release view "$TAG" --json url --jq .url 2>/dev/null || true
