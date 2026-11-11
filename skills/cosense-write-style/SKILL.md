---
name: cosense-write-style
description: Cosense(Scrapbox)プロジェクト(scrapbox.io/{project_name})のページに対して、まとめ・議事録・要望整理などのテキストを追記・編集する作業の作法とスタイルを定義する。ユーザーがCosenseページURLを貼って「このページに記載して」「Cosenseにまとめて」「○○ページに追記して」などと依頼したときに必ず使用する。AI署名、作業後の声かけ文化、テンプレ連携などのプロジェクト固有の作法を適用する。書き込みは第一推奨として cosense CLI (helpfeel公式) の previewEdit → submitEdit に委譲する。
---

# Cosense 書き込み作法・スタイル適用スキル

## このスキルの位置づけ (重要)

このスキルは **プロジェクト固有のCosense作法** を担うスキルであり、**Cosenseの読み書きそのものは helpfeel公式の `cosense` skill (CLI) に委譲する**。

- **`cosense` skill (公式CLI)** = ページの読み取り・編集の「エンジン」。helpfeelが公式提供しているため、こちらの手順・記法・コマンド仕様には手を加えず追従する。
- **`cosense-write-style` skill (このファイル)** = プロジェクトの現場ルール(`[author:Clawd.icon]` / `[author:モッフィー.icon]` 署名の使い分け、作業後の声かけ文化、`:ticketlog` テンプレ枠、意図せぬリンク化の回避、公開ページ確認など)を上乗せする「作法レイヤー」。

したがって、**書き込みロジックの詳細(previewEdit/submitEditのops組み立て、リンク選定、承認フロー等)は原則 `cosense` skill の `edit-page.md` に従い、このスキルではそこに載っていないプロジェクト固有の判断だけを規定する**。

## このスキルの目的

Cosense (Scrapbox) プロジェクト `scrapbox.io/{project_name}` のページに、AIが整理した内容をスピーディーに書き込めるようにする。ユーザーがAIとの対話で整理した内容を、毎回手動でコピペしてCosenseに転記する手間をなくす。

## いつ使うか

- ユーザーが Cosense ページのURL (`https://scrapbox.io/{project_name}/...`) を貼って「ここに記載して」「Cosenseにまとめて」と依頼したとき
- ユーザーが「○○ページに追記して」「Cosenseに書いて」と言ったとき
- 既存ページが空でも、すでに内容があっても末尾追記で対応する

## 前提

- 書き込み対象は `scrapbox.io/{project_name}` プロジェクト配下のページであること
- 別プロジェクトに書く場合は、その都度ユーザーに確認すること

---

## 実行経路の選択 (最初に必ず判断する)

書き込みには2つの経路がある。**CLI経路を第一推奨とし、使えないときだけブラウザ経路にフォールバックする**。

### 判断フロー

1. **まず `cosense` CLI が使えるか確認する** (`cosense whoami` を試す、または `bash_tool` が利用可能か)
   - 使える → **経路A (CLI委譲)** を採用 【推奨】
2. **CLIが使えない (Claude Chat 等、bash/CLIが無い環境)**
   - `Claude in Chrome` が使える → **経路B (ブラウザ操作)** にフォールバック
   - どちらも使えない → 書き込みは不可。整形済みテキストをチャットに出し「手動でCosenseに貼ってください」と案内する (経路C)

### 環境別の目安

| 環境 | 既定経路 | 理由 |
|---|---|---|
| **Claude Cowork** | 経路A (CLI) | bash + CLI が使える。最速・最も安全 |
| **Claude Code** | 経路A (CLI) | 同上 |
| **Antigravity (IDE Agent)** | 経路A (CLI) | 同上 |
| **Claude Chat (ブラウザ)** | 経路B (ブラウザ) | bash/CLIが無い。`Claude in Chrome` で操作 |
| いずれも不可 | 経路C (手動案内) | 整形テキストだけ渡す |

**環境名で決め打ちせず、実際に `cosense whoami` / bash可否を確かめてから経路を確定する**。CLIが入っていない場合は `npm install -g @helpfeel/cosense-cli` を案内 (Node 24+ 前提) するか、経路Bに切り替える。

---

## 経路A: CLI委譲 (第一推奨)

**書き込みそのものは `cosense` skill の手順に完全に従う**。ここではプロジェクト作法の上乗せだけを示す。

### 手順

1. `cosense` skill の `edit-page.md` に従って対象ページを読む (`browsePage` → `readPage`)
2. 本文をCosense記法で組み立てる。このとき **下記「プロジェクト共通作法」を必ず適用**する
   - 実行しているツールに合わせて適切なAI署名（`[author:Clawd.icon]` または `[author:モッフィー.icon]`）を付ける
   - 意図せぬリンク化を避ける (ブラケットは見出し・アイコン専用)
   - `:ticketlog` テンプレ枠なら空タブ行を埋める形にする
3. `cosense` skill の `previewEdit` でdry-run → リンク計画の承認フロー (公式手順どおり)
4. 承認後 `submitEdit` で確定
5. **作業後の声かけ** (後述「一緒に作業した人間への声かけ」) を、同じ編集opsの中で追記する
6. ユーザーに完了報告 (ページURL・追記見出し構成・Cosenseにもコメントを残した旨)

### CLI経路での注意

- ops の anchor (行id) 指定・新規/既存判定 (`persistent`)・リンク選定基準は **すべて `cosense` skill 側の規定に従う**。このスキルで再定義しない
- 声かけコメントも1つの `insertBefore` / 子行op として previewEdit に含める
- 迷ったら `cosense <command> --help` で正確な引数・戻り値スキーマを確認する

---

## 経路B: ブラウザ操作フォールバック (CLIが使えない環境)

Claude Chat のように bash/CLI が無く、`Claude in Chrome` だけが使える環境向け。Cosense公式UserScript API (`cosense.Page.insertLine` / `updateLine` / `waitForSave`) を javascript_tool 経由で叩く。UserScript不要。

### 前提 (経路B)

- プロジェクトの Cosense にログイン済みのブラウザに `Claude in Chrome` で接続できること

### ワークフロー全体像 (経路B)

1. 提示されたCosenseページURLをタブで開く
2. **REST APIでページの現状を取得**して、空ページか/既存内容ありかを確認 (Read)
3. 投入する本文をCosense記法で整形し、配列にまとめる (プロジェクト共通作法を適用)
4. **`cosense.Page.insertLine` をループ呼び出し** → `waitForSave()` で保存確定 (Write)
5. 余分な空行が残っていれば、ブラウザ操作 (クリック + Deleteキー) で削除
6. スクリーンショットで反映を確認
7. **一緒に作業した人間に一言声をかける** (後述)
8. ユーザーに結果報告

#### B-ステップ1: 該当ページをブラウザで開く

```
1. mcp__Claude_in_Chrome__tabs_context_mcp(createIfEmpty: true) でタブを準備
2. mcp__Claude_in_Chrome__navigate でCosenseページURLを開く
3. 数秒待ってからスクリーンショットを撮る
```

#### B-ステップ2: REST APIでページ現状を取得 (Read)

読み取りは公式REST APIが最速で安全。書き込みは提供されていない。

```javascript
fetch('/api/pages/{project_name}/<ページタイトルURLエンコード>', {credentials: 'include'})
  .then(r => r.json())
  .then(d => JSON.stringify({
    title: d.title,
    linesCount: d.lines?.length,
    lines: d.lines?.map(l => l.text),
    persistent: d.persistent
  }, null, 2))
```

- `persistent: true` → 既存ページ / `linesCount` → 現状行数(タイトル含む) / `lines[0]` がタイトル

#### B-ステップ3: 本文をCosense記法で整形

「プロジェクト共通作法」と「Cosense記法早見表」(後述) に従って整形する。大きな本文は `create_file` で一度書き出し `view` で目視確認してから配列リテラルに転記するとリカバリーが速い。

#### B-ステップ4: 一括投入 (Write)

末尾追記方式が最も安全。

```javascript
(async () => {
  const body = [
    "[** 投入する見出し]",
    " 本文行1",
    " 本文行2",
  ];
  try {
    let baseIndex = window.cosense.Page.lines.length;
    for (let i = 0; i < body.length; i++) {
      window.cosense.Page.insertLine(body[i], baseIndex + i);
    }
    await window.cosense.Page.waitForSave();
    return JSON.stringify({status:'ok', insertedCount:body.length, finalLineCount:window.cosense.Page.lines.length});
  } catch (e) {
    return JSON.stringify({status:'error', message:e.message});
  }
})()
```

制約: `insertLine`/`updateLine` に**行削除機能はない**。行を減らすには次のキーボード操作に頼る。

#### B-ステップ5: 余分な空行・既存ブロックの削除 (必要時のみ)

**軽量削除** (数行): 削除したい空行付近をクリック → `Delete` を必要回数。

**大量削除** (推奨): `Shift+Down` で範囲選択 → `Delete`一回。`Delete`連打は取りこぼしが出る。

```javascript
[
  {action: "left_click", coordinate: [<x>, <y>]},
  {action: "key", text: "Home"},
  {action: "key", text: "shift+Down", repeat: <行数>},
  {action: "wait", duration: 1},
  {action: "key", text: "Delete"},
  {action: "wait", duration: 2},
  {action: "screenshot"}
]
```

- 行数はREST APIの `lines.length` から計算。Shift+Down連打は1ターン70行ほどまで。それ以上は分割
- 削除後は `window.cosense.Page.lines.length` を再取得して想定通り減ったか確認
- **`Ctrl+Shift+End` は効かない** (Scrapbox独自キーバインド)。範囲拡張は `Shift+Down` 連打で代替

#### B-ステップ6: 反映確認

スクリーンショットで、見出し階層・箇条書きインデント・URLリンク化・意図せぬ `[テスト]` 系リンク(ページ下部Links欄)を確認。

### 経路B のハマりポイント

- **`cosense.Page` が存在しない**: `window.cosense.Page` と `window.scrapbox.Page` の両方で保存用APIオブジェクトが公開されている。片方が無ければもう片方を試す。無ければ読み込み中なので数秒待つ
- **行データ取得がセキュリティ層でブロック** (`[BLOCKED: Cookie/query string data]`): 本文中のURLや長い英数字が機密誤判定される。回避策: URLマスク `l.text.replace(/https?:\/\/[^\s]+/g,'[URL]')` / 長数字マスク `replace(/\d{12,}/g,'N')` / `lines.slice(0,15)` で範囲を狭める / `fetch`より `window.cosense.Page.lines` 経由の方が弾かれにくい
- **`insertLine` の index=0 は禁止**: index=0 はタイトルの前に挿入されタイトルが変わる。本文先頭でも `index=1` から
- **index計算のズレ**: `insertLine` を呼ぶたび後続行のindexが1ずつ後ろにずれる。複数枠を順に埋めるときは追加行数を足して再計算

---

## 経路C: 手動案内 (書き込み手段が無いとき)

CLIもブラウザも使えない場合は、整形済みのCosense記法テキストをチャット内コードブロックで提示し、「お手数ですがこのままCosenseに貼り付けてください」と案内する。実行しているAIに応じた署名（`[author:Clawd.icon]` または `[author:モッフィー.icon]`）は付けたまま渡す。

---

## プロジェクト共通作法 (全経路で必須)

ここが本スキルの本体。経路A/B/Cのどれでも、書き込む本文にこれらを適用する。

### 1. アイコン署名ルール (必須)

#### AIツールごとの使い分け
プロジェクトのCosenseには、AI執筆を示すアイコン運用がある。作業を行っているAIツール（実行中のエージェント）に応じて、以下の通り署名アイコンを適切に切り替えて使用する。

- **Claude**（Claude Code / Claude Cowork等）の場合: **`[author:Clawd.icon]`** を使用
  * アイコンは `scrapbox.io/{project_name}/author:Clawd` ページに設定されている。
- **Antigravity**（IDE Agent）の場合: **`[author:モッフィー.icon]`** を使用
  * アイコンは `scrapbox.io/{project_name}/author:モッフィー` ページに設定されている。

#### 適用ルール
- **各セクション/各枠の末尾の行末に1個** が基本(各行末に毎回付けると煩雑)
- 人が書いた既存テキストには付けない。AIが新しく書いた範囲だけに付ける
- ユーザーから「項目末ごとに付けて」等の指示があればそれに従う
- ❌ `.icon` を付け忘れて `[author:Clawd]` や `[author:モッフィー]` とだけ記述しない。必ず `[author:Clawd.icon]` / `[author:モッフィー.icon]` と記述すること。

### 2. 一緒に作業した人間への声かけ (デフォルト振る舞い)

**依頼されたから書くのではなく、AIが自発的にやる**。Cosenseで何かを書いたら、一緒に作業した人間(=依頼者)に一言声をかける。チャットの最終報告とは別に、Cosenseページ上にも「一緒に作業した感」を残す。これはプロジェクトのCosense文化であり、チームメンバーの一人として関わる姿勢が期待されている。

#### どこに書くか (優先順)

1. **作業報告ブロックがあれば、そこのタブ空行に書く**
2. **同じページ末尾にユーザー自身のメモがあれば、その下に書く**
3. **迷ったらユーザーに「どこに書きましょうか?」と聞く**(書く姿勢は持ちつつ場所判断は誠実に)

消極的な「依頼がないから書かない」は避ける。「書きたいけど場所が分からないので教えて」と聞く方が自然。

#### 典型的な作業報告ブロック

hott3さんはページ末尾に作業日報メモを残すことがある:

```
2026/5/18
依頼された内容を確認した[hott3.icon]
	
	
```

`[hott3.icon]` の下のタブ空行は **AIが一言コメントを残す欄**。何も指示されなくても書き込む。

#### 一言コメントの書き方

- **トーン**: 同僚に話しかけるような親しげで簡潔なテキスト。形式的すぎず冷たすぎず
- **内容**: 何をしたかの一言要約 + 次への軽い励まし/一緒に進める姿勢 + ねぎらいを含めてもよい
- **長さ**: 1行(40〜70文字程度)。長文は避ける
- **末尾**: 必ず実行ツールに応じた署名（`[author:Clawd.icon]` または `[author:モッフィー.icon]`）を付与する

**Claudeの一言コメントの例:**
```
	お疲れさまです、要望をページにまとめました。仕分け、一緒に進めましょう [author:Clawd.icon]
	整理お疲れさまでした!次は仕分け作業からですね [author:Clawd.icon]
```

**Antigravityの一言コメントの例:**
```
	お疲れさまです、要望をページにまとめました。仕分け、一緒に進めましょう [author:モッフィー.icon]
	整理お疲れさまでした!次は仕分け作業からですね [author:モッフィー.icon]
```

- 空タブ行(`\t`のみ)であることを確認してから書く。既存コメントは上書きしない
- 複数の `[hott3.icon]` 行があれば最新(最下部)を対象にする
- 毎回同じ定型文にせず、その日の作業内容に応じてバリエーションを持たせる
- 経路Aでは編集opsに含め、経路Bでは `updateLine` で書く

### 3. `:ticketlog` 等の既存テンプレ枠への埋め込み

プロジェクトには `#:ticketlog` タグ付きチケット管理テンプレを使ったページがある:

```
タイトル
#:ticketlog
[hr | ---.icon]
担当者
	[ユーザー名.icon]
該当チケット
	{チケットurl}
やること
	(空タブ行)
ゴール
	(空タブ行)
参考
	(空タブ行)
[hr | ---.icon]
```

空タブ行(行頭が `\t` だけ)を埋めるときの原則:

- **末尾追加ではなく、既存タブ空行を上書きする**(経路Aなら該当行を anchor に replace、経路Bなら `updateLine`)
- 「すでにある空行は使い切る、足りない分だけ挿入」が基本
- インデントは **半角スペースではなくタブ文字 `\t`** で統一
- 見出しは `\t` の後に `[* xxx]` を置く: `'\t[* アプリ内ブラウザ]'`

### 4. Cosense記法早見表 (よく使うもの)

| 記法 | 効果 | 注意 |
|---|---|---|
| `[** タイトル]` | 大きい見出し | 章ヘッダー |
| `[* タイトル]` | 中見出し | 節ヘッダー |
| `[/icons/check.icon]` | チェックマーク | TODO |
| ` テキスト` (先頭スペース) | 箇条書き1段 | 行頭スペース数で階層 |
| `> 引用文` | 引用 | |
| `[xxx]` | 内部リンク | **意図しないリンク化に注意** |
| URL裸書き | 自動リンク化 | `[https://... 表示テキスト]` で表示文字指定可 |

### 5. ブラケット記法の意図せぬリンク化を避ける (重要)

`[xxx]` で囲むとその文字列がCosense内部リンクになる。`[テスト]` `[確認]` 等の一般語を囲むとページ下部のLinks欄が意図せぬページで埋まる。

- **ブラケットは見出し(`[** ]` `[* ]`)とアイコン(`[/icons/.icon]`)専用**
- 通常テキスト中の固有名詞・項目名は囲まない
- 既存ページ名と意図的にリンクしたい場合のみ明示的に `[ページ名]` を使う (経路A of `cosense` skill の基準に従う)

### 6. 公開ページ・お客様がいる場への書き込み

Cosenseはプライベート向けだが、まれに公開設定のページがある。書き込み前にページ右上の鍵(非公開)/グローブ(公開)アイコンを確認する。公開ページに書く場合は、お客様向けの体裁が必要か必ずユーザーに確認する。

---

## 完了報告 (全経路で必須)

ユーザーに以下を報告:

- 書き込んだCosenseページのURL (再掲)
- 使った経路 (CLI / ブラウザ / 手動案内)
- 追記した見出し構成 (章レベル `[** xxx]` をリスト)
- Cosense上にも一言コメントを残した旨
- 次アクション (空行整形が必要、読み直してほしい等)

報告例:

> Cosenseページに記載完了しました (CLI経由)。
> - ページ: https://scrapbox.io/{project_name}/{page_name}
> - 構成: クライアント確認・要望まとめ / 1. アプリ内ブラウザ / 2. アプリ内UIの改修 / 次のアクション / 関連リンク
> - Cosense上にも一言コメントを残しておきました。ご確認お願いします。

---

## 効率化のヒント

- **経路A(CLI)を最優先**: 座標クリックやレンダリング待ちが不要で最も速く安全。CLIから試す
- **本文配列はファイルに一度書き出す**: 大きな本文はファイルを一度作成して確認してから使う
- **テスト1行 → 本番投入 of 2段構え**: 長い本文(30行以上)はまず1行テストして記法解釈を確認してから本番へ

## 関連スキル

- **`cosense` (helpfeel公式CLI)** — ページの読み書きエンジン。書き込みの詳細手順・リンク選定・承認フローはこちらに従う。公式追従のため改変しない
