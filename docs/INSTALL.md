# 安裝、建置與測試

功能與操作介紹請見 [README](../README.md)。本文件說明安裝、開發環境、打包、
測試與發佈流程，對應版本 **1.1.1**。

## 下載

版本發佈後可從 [GitHub Releases](https://github.com/keys-lll/PDF-Tool/releases)
下載：

- Windows：`PDF-Page-Merger-1.1.1-windows-x64.zip`
- Debian／Ubuntu：`pdf-page-merger_1.1.1-1_all.deb`
- `SHA256SUMS`：下載檔完整性校驗

若此版本尚未發佈，本機建置的檔案位於專案的 `dist/` 資料夾。

## Windows 可攜版

1. 解壓縮 `PDF-Page-Merger-1.1.1-windows-x64.zip`。
2. 執行 `PDF-Page-Merger` 資料夾內的 `PDF-Page-Merger.exe`。
3. 保留 `_internal` 資料夾，不要只複製 exe。

不需要 Python、poppler 或管理員權限。Windows 版內建 PDFium 縮圖引擎。
這是未簽章執行檔，SmartScreen 可能顯示警告；確認下載來源後可選擇
「更多資訊」→「仍要執行」。

## Debian／Ubuntu 套件

```bash
sudo apt install ./pdf-page-merger_1.1.1-1_all.deb
```

apt 會自動補齊 `python3-pypdf` 等缺少的依賴。安裝後可從應用程式選單啟動
「PDF 併頁器」，或執行：

```bash
pdf-page-merger
```

驗證下載：

```bash
sha256sum -c SHA256SUMS
```

移除：

```bash
sudo apt remove pdf-page-merger
```

## 從原始碼啟動

需要圖形桌面環境與 Python 3.10 以上：

```bash
cd /home/liao/.zcode/workspace/449f8f0c-0603-4541-b26e-8bccd39a56b8/pdf-merger
./run.sh
```

`run.sh` 會在第一次啟動時建立 `.venv` 並安裝 `requirements.txt`。也可以直接
把 PDF 拖到 `run.sh` 上，或執行：

```bash
./run.sh 報告.pdf 附件.pdf
```

若要建立原始碼版本的桌面選單捷徑（不要和 `.deb` 版本同時安裝）：

```bash
./install-desktop-entry.sh
```

## 環境需求

### Windows

- Windows 10／11 x64
- 可攜版已包含 PySide6、pypdf、cryptography、PDFium 與 Pillow

### Linux

- Python 3.10 以上（從原始碼啟動時）
- `python3-pyside6.qtwidgets`
- `python3-pypdf` 5.0 以上
- `python3-cryptography`
- `poppler-utils`，或安裝 `pypdfium2` 與 `Pillow` 作為內建替代後端
- 建議：`fonts-noto-cjk`、`xdg-utils`

若使用 `.deb`，apt 會處理主要依賴，並把 `poppler-utils` 列為必要套件。
`fonts-noto-cjk` 與 `xdg-utils` 則列為 Recommends。

## 重新打包 Linux `.deb`

```bash
./packaging/build-deb.sh
```

輸出為 `dist/pdf-page-merger_1.1.1-1_all.deb`，並更新 `dist/SHA256SUMS`。
可用環境變數改版號：

```bash
VERSION=1.1.1 REVISION=1 ./packaging/build-deb.sh
```

建置只需要 `dpkg-deb`、`gzip` 與 `desktop-file-validate`（後者為選用驗證）。

## 建置 Windows 可攜版

Windows 版本由 GitHub Actions 的 Windows runner 建置：

```bash
gh workflow run windows.yml --ref main -f version=1.1.1
gh run watch <run-id>
```

流程會：

1. 安裝 `requirements-build.txt`。
2. 產生範例 PDF 並執行 25 項測試。
3. 用 PyInstaller 建立 `PDF-Page-Merger` 可攜資料夾。
4. 檢查 `pdfium.dll` 已包含。
5. 執行凍結版本的 `--smoke-test`。
6. 上傳 `PDF-Page-Merger-1.1.1-windows-x64.zip` artifact。

也可以在 Windows 本機執行：

```powershell
python -m pip install -r requirements-build.txt
.\windows\build.ps1 -Version 1.1.1
```

## 測試

先執行一次 `./run.sh` 建立 `.venv`（或手動建立虛擬環境並安裝
`requirements.txt`）：

```bash
cd /home/liao/.zcode/workspace/449f8f0c-0603-4541-b26e-8bccd39a56b8/pdf-merger
QT_QPA_PLATFORM=offscreen .venv/bin/python tests/make_samples.py
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

測試涵蓋：

- 加密 PDF 的密碼需求、錯誤密碼、正確解鎖，以及只有擁有者密碼的情況。
- 解密工作副本、poppler 與 PDFium 縮圖、跨執行緒序列化與取消。
- 任意頁序合併、重複頁、取消合併、拒絕覆蓋來源、錯誤清理。
- GUI 的加入檔案、縮圖載入、實際滑鼠拖曳換位、頁面刪除、解鎖狀態、
  合併輸出與進度對話框重入。

範例檔會產生在 `tests/samples/`，其中 `機密_董事會附件.pdf` 的密碼是
`open123`。

## 發佈到 GitHub

版本庫已包含版本標籤與發佈說明。登入 GitHub CLI 後可建立 Release：

```bash
gh auth login
./packaging/publish-github.sh
```

腳本使用既有 `origin`，推送 `main` 與目前版本標籤，並附上 `.deb`、
Windows zip（若存在）與 `SHA256SUMS`。

## 專案結構

```text
pdf-merger/
├── main.py                  # 程式入口
├── main_window.py           # 主視窗與操作流程
├── ui_pages.py              # 頁面縮圖畫廊、拖曳排序
├── ui_widgets.py            # 來源列、密碼對話框
├── pdf_engine.py            # 解密、縮圖、合併（無 Qt 相依）
├── workers.py               # 背景縮圖與合併工作
├── icons.py / theme.py      # 介面圖示與樣式
├── platform_support.py      # Windows／Linux 字型選擇
├── assets/                  # SVG／PNG／ICO 應用程式圖示
├── packaging/               # .deb 建置腳本、desktop、man、changelog
├── windows/                 # PyInstaller 建置腳本、版本資源與 Windows 說明
├── .github/workflows/       # Windows CI 建置流程
├── docs/                    # 安裝文件、Release notes、截圖
├── dist/                    # 建置產物（不進版本庫）
├── tests/                   # 單元測試、GUI 測試、範例 PDF 產生器
├── THIRD_PARTY_NOTICES.md   # Windows bundle 的第三方授權說明
├── run.sh
└── install-desktop-entry.sh
```

## 密碼與暫存檔

- 密碼只存在記憶體中，不會寫入設定檔或日誌。
- 解密後的工作副本與縮圖位於系統暫存資料夾（Linux 通常為
  `/tmp/pdf-page-merger-*`，Windows 為 `%TEMP%\pdf-page-merger-*`）。
- 正常關閉程式時會刪除暫存資料夾；強制終止時可能留在系統暫存目錄。
- 來源 PDF 永遠不會被修改，輸出是新的未加密 PDF。
