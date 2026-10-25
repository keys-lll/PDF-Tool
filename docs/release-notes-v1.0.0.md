# PDF 併頁器 v1.0.0

第一個正式版本：在 Linux 桌面上合併多份 PDF，並用縮圖逐頁調整順序。

## 下載

- `pdf-page-merger_1.0.0-1_all.deb` — Debian／Ubuntu 安裝套件
- `SHA256SUMS` — 下載檔完整性校驗

## 安裝

```bash
sudo apt install ./pdf-page-merger_1.0.0-1_all.deb
```

apt 會自動安裝缺少的 `python3-pypdf` 等依賴。安裝後可從應用程式選單啟動
「PDF 併頁器」，或執行：

```bash
pdf-page-merger
```

## 重點功能

- 一次加入多份 PDF，支援拖放。
- 全頁縮圖畫廊，拖曳即時換位，靠近邊緣會自動捲動。
- 每份加密 PDF 分別輸入密碼；可重試、取消或稍後解鎖。
- 可多選頁面刪除，也可用上移／下移按鈕與快速鍵。
- 合併前提醒未解鎖的 PDF。
- 暫存檔原子替換，避免留下損壞的半成品。
- 密碼只存在記憶體；解密暫存檔在正常關閉程式後刪除。
- 附桌面選單、icon 與 `pdf-page-merger(1)` man page。

## 系統需求

- Linux，Python 3.10 以上
- `python3-pyside6.qtwidgets`
- `python3-pypdf` 5.0 以上
- `python3-cryptography`
- `poppler-utils`
- 建議：`fonts-noto-cjk`、`xdg-utils`

## 驗證下載

```bash
sha256sum -c SHA256SUMS
```

## 已知限制

- 合併結果不保證保留書籤、表單欄位、附件或數位簽章。
- 輸出 PDF 不會重新加密。
- `.deb` 以 Ubuntu 26.04 的套件名建置。
- 尚未提供 Windows 或 macOS 版本。

完整變更請見倉庫根目錄的 `CHANGELOG.md`。
