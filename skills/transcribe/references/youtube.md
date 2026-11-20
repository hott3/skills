# YouTube（単体動画・再生リスト）文字起こし手順

YouTube URLが指定された場合は、動画本体をダウンロードして音声認識にかける前に、**まず既存の字幕・自動生成字幕を取得する**のが最も高速で確実である。

---

## 1. メタデータ・タイトルの取得（日本語優先）

YouTubeはアクセス元のIPや環境によって再生リスト・動画タイトルを英語等に自動翻訳して返すことがある。元の日本語タイトルを取得するには `--extractor-args "youtube:lang=ja"` を指定する。

```bash
uvx yt-dlp --extractor-args "youtube:lang=ja" --flat-playlist \
  --print "%(playlist_index)02d | %(id)s | %(duration_string)s | %(title)s" \
  "<PLAYLIST_OR_VIDEO_URL>"
```

## 2. 字幕の優先取得（`--skip-download`）

まずは利用可能な字幕を確認し、オリジナル言語（`ja-orig` / `ja` 等）のVTTをダウンロードする。

```bash
# 利用可能な字幕一覧の確認
uvx yt-dlp --list-subs "<VIDEO_URL>"

# 字幕のみ一括ダウンロード（再生リスト対応）
mkdir -p scratch/subs
uvx yt-dlp --extractor-args "youtube:lang=ja" \
  --write-subs --write-auto-subs \
  --sub-langs "ja-orig,ja" --sub-format vtt \
  --skip-download \
  -o "scratch/subs/%(playlist_index)02d_%(id)s.%(ext)s" \
  "<PLAYLIST_OR_VIDEO_URL>"
```

- 字幕が取得できなかった動画のみ、音声をダウンロードして [local-audio-video.md](local-audio-video.md) のASR手順へフォールバックする。

## 3. VTTのパースと整形

YouTubeの自動生成VTTは、以下のような特徴を持つため、そのままでは重複だらけで読めない。
- 2行ロール表示により、前のキューの行が次のキューに重複して含まれる
- インラインタイムスタンプ `<00:00:04.640><c>...</c>` が含まれる
- `&amp;` 等のHTMLエンティティが含まれる

同梱の `scripts/parse_vtt.py` を使ってクリーンなテキストに変換する。

```bash
# Markdown形式（**[MM:SS]** タイムスタンプ付き）
python3 scripts/parse_vtt.py scratch/subs/01_*.ja-orig.vtt --format markdown --interval 60

# Cosenseコードブロック向け（(MM:SS) 形式・[]/# 無害化）
python3 scripts/parse_vtt.py scratch/subs/01_*.ja-orig.vtt --format cosense --interval 60
```

## 4. 映像キャプチャによる誤字検証（重要）

自動字幕では固有名詞・専門用語・数字が誤変換されやすい。動画内のスライドやテロップを確認するため、必要な箇所の静止画を切り出して目視照合する。

1. **低〜中解像度で動画を取得**（テロップが読めれば十分なので `height<=720` や `480` で高速に落とす）:
   ```bash
   uvx yt-dlp -f "bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]/best" \
     -o "scratch/videos/%(id)s.mp4" "<VIDEO_URL>"
   ```
   ※ 再生リスト全本を一括ダウンロードするとタイムアウトしやすいため、検証が必要な動画から順に取得するか、1本ずつ処理する。

2. **問題箇所のタイムスタンプを切り出してタイル画像化**:
   1枚ずつ画像を読むとコンテキスト消費が大きいため、`ffmpeg` で `3x3` 等のコンタクトシートにまとめる。
   ```bash
   mkdir -p scratch/frames
   for ts in 00:00:14 00:01:15 00:02:28 00:03:02; do
     fname=$(echo "$ts" | tr ':' '_')
     ffmpeg -y -ss "$ts" -i "scratch/videos/<ID>.mp4" -vframes 1 -q:v 3 "scratch/frames/${fname}.jpg" 2>/dev/null
   done
   ffmpeg -y -pattern_type glob -i "scratch/frames/*.jpg" \
     -filter_complex "scale=640:360,tile=3x3" "scratch/frames/grid.jpg" 2>/dev/null
   ```
3. 生成した `grid.jpg` を確認し、テロップ・スライドの正確な表記に基づいて [proofreading-and-output.md](proofreading-and-output.md) の対応表を作成する。
