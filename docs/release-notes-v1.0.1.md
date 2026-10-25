# PDF 併頁器 v1.0.1

修正 v1.0.0 在合併完成或取消時，進度對話框關閉後仍被更新而產生的
`AttributeError`。建議所有 v1.0.0 使用者升級。

## 下載

- `pdf-page-merger_1.0.1-1_all.deb` — Debian／Ubuntu 安裝套件
- `SHA256SUMS` — 下載檔完整性校驗

## 安裝或升級

```bash
sudo apt install ./pdf-page-merger_1.0.1-1_all.deb
```

apt 會自動安裝缺少的 `python3-pypdf` 等依賴。安裝後可從應用程式選單啟動
「PDF 併頁器」，或執行：

```bash
pdf-page-merger
```

## 修正內容

- 合併完成訊號可能在 `QProgressDialog.setValue()` 處理事件時重入，導致進度框
  已關閉後仍呼叫 `setLabelText()`。
- 現在會先更新標籤、最後才設值，並在關閉進度框前先清除內部參照。
- 新增對應的重入回歸測試，測試總數為 21 項。

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
