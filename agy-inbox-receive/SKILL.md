---
name: agy-inbox-receive
description: >-
  Google Drive の Antigravity-Inbox にある Gemini からの引き継ぎ案件（壁打ち Doc や話題別バンドルフォルダ）を取得し、
  文脈の蒸留・成果物（Canvas プロトタイプ等）の展開・タスク化を行ったうえで、元データを即座に Antigravity-Archive へ移動するスキル。
  「Inbox を確認して」「Gemini から引き継いで」「agy-inbox-receive」「壁打ちを取り込んで」などと指示されたときに使用する。
---

# agy-inbox-receive（Antigravity 引き継ぎ受け取り＆即アーカイブスキル）

Gemini（`agy-inbox-send`）から Google Drive の `Antigravity-Inbox` へ送られた未処理の壁打ち・長文コンテキスト・Canvas 成果物を Antigravity セッションへ取り込み、タスク化と同時に元データを `Antigravity-Archive` へ移動して Inbox を常に空（未処理のみ）に保つスキルです。

## 基本ルールと設計思想

- **未タスク化＝Inbox、タスク化完了＝即アーカイブ**: コミュニケーション・未整理の試作は Inbox に留め、Antigravity セッションに統合・タスク化した瞬間に `Antigravity-Archive` へ移動する。
- **安全性最優先**:
  - 取得・展開・タスク化が**すべて完了するまでアーカイブ移動を実行しない**（途中で失敗・中断したら Inbox に残す）。
  - ファイルを削除（`trash` / `delete`）しない。必ず `Antigravity-Archive` への移動（`gdrive mutate mv`）を使う。
  - ローカルの既存ファイルを無断で上書きしない（展開先はユーザーに確認するか、新規ディレクトリへ配置する）。

## 対象 Google Drive フォルダの解決

このスキルでは個人固有のフォルダ ID をハードコードせず、毎回フォルダ名から動的に ID を解決します。

- 受信箱フォルダ名: **`Antigravity-Inbox`**
- アーカイブフォルダ名: **`Antigravity-Archive`**

まず `gdrive` で両フォルダの ID を検索して取得する（`Type` が `folder` で名前が完全一致するものを選択する）。

```bash
gdrive readonly search --name-contains "Antigravity-Inbox"
gdrive readonly search --name-contains "Antigravity-Archive"
```

※ 対象フォルダが見つからない場合は勝手に作成せず、ユーザーにフォルダ作成可否を確認する（初回のみ `gdrive mutate mkdir "Antigravity-Inbox"` / `"Antigravity-Archive"` で作成可能）。

## 実行手順

### 1. CLI の準備と認証確認
`gdrive` と `gdocs` の CLI が使える状態か確認する（未初期化なら各プラグインの setup スクリプトを実行する）。
認証エラー（needs authentication 等）が出た場合は、認証バイパスは行わず、ユーザーにプラグインカードまたはサインインを案内して待機する。

### 2. `Antigravity-Inbox` の未処理アイテム一覧を取得
解決した `<INBOX_FOLDER_ID>` に対して `readonly` コマンドで中身を確認する。

```bash
gdrive readonly ls <INBOX_FOLDER_ID>
```

- **0 件の場合**: 「`Antigravity-Inbox` は空です（未処理の引き継ぎはありません）」と報告して終了する。
- **1 件の場合**: 対象名と種別（単体ファイル［Google Doc / Markdown］か話題フォルダか）を伝え、取り込みを進めてよいか確認（ユーザーがすでに「最新を取り込んで」と明示している場合はそのままステップ 3 へ進んでよい）。
- **複数件の場合**: 番号付き一覧（名前・種別・更新日時）を提示し、どれを取り込むか **1 問だけ** ユーザーに選んでもらう。

### 3. パッケージ内容の取得と読み込み
選んだアイテムの種別・MIME タイプに応じて中身を取得する。作業用の一時展開先は会話のスクラッチディレクトリ（または OS の一時フォルダ）を使う。

- **取得コマンドの使い分け（MIME タイプ判定）**:
  - **Google ドキュメント（`application/vnd.google-apps.document` / `document`）**: `gdocs readonly export <DOC_ID> --format md --output <TEMP_DIR>/<FILENAME>.md` で Markdown としてエクスポートする。
  - **Markdown・テキスト・コード成果物（`text/markdown`, `.md`, `.txt`, `.tsx`, `.html`, `.py`, `.zip` 等）**: `gdrive readonly download <FILE_ID> --out <TEMP_DIR>/<FILENAME>` でそのままダウンロードする。
- **A. 単体ファイル（壁打ち Doc / `.md`）の場合**:
  上記ルールで 1 ファイルを `<TEMP_DIR>/` へ取得し、内容を読み込む。
- **B. 話題別フォルダ（バンドル）の場合**:
  1. `gdrive readonly tree <TOPIC_FOLDER_ID>` と `gdrive readonly ls <TOPIC_FOLDER_ID>` でフォルダ内の全ファイルと `Type`（MIME タイプ）を確認する。
  2. フォルダ内の各ファイルを上記「取得コマンドの使い分け」に従ってすべて `<TEMP_DIR>/` へ取得し、仕様メモ（`.md` / Google Doc）と成果物ファイル（`.tsx` / `.html` 等）を読み込む。

### 4. 文脈蒸留・成果物展開・タスク化
読み込んだ内容をもとに、現在の Antigravity セッションへ統合する。

1. **文脈蒸留（長文コンテキスト対策）**:
   - 長大な文章や仕様が含まれている場合、会話コンテキストを圧迫しないよう、要点を構造化して整理する。
   - ユーザーから保存の希望がある場合（または開発仕様として残すべき場合）は、ワークスペース内（例：`docs/inbox/<topic>.md` 等、パスは事前に確認）またはセッション内アーティファクトに仕様メモとして保存する。
2. **成果物（プロトタイプ）の展開**:
   - 同梱されたコードやアセットがある場合は、ワークスペース内のどこへ展開するか（例：`prototypes/<topic>/` や既存構成に合わせた場所）をユーザーに確認してから配置する。
3. **タスク化と最初の一手**:
   - 壁打ちの内容を「このセッションで進める具体的なタスクリスト」と「未決事項（判断が必要なポイント）」に変換して提示し、すぐ作業に入れる状態を作る。

### 5. 即アーカイブ（`Antigravity-Archive` へ移動）
ステップ 4 の読み込み・統合・タスク化が完了したら、**取り込み完了の証跡として**元のアイテム（単体 Doc または話題フォルダ丸ごと）を `Antigravity-Archive` へ移動する。

```bash
gdrive mutate mv <ITEM_ID> <ARCHIVE_FOLDER_ID>
```

移動後、ユーザーに以下を簡潔に報告する：
- 取り込んだ話題名とタスク化（または展開）した内容の要点
- `Antigravity-Inbox` から `Antigravity-Archive` へ移動済みであること（Inbox が整理された状態であること）
