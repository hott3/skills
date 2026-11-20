# ローカル動画・ボイスメモ・音声ファイル・音楽の文字起こし手順

字幕データが存在しないローカル動画（`.mp4`, `.mov`, `.mkv`）、ボイスメモ（`.m4a`, `.aac`, `.ogg`）、音声ファイル（`.wav`, `.mp3`）、音楽ファイルを文字起こしする手順。

---

## 1. `ffmpeg` による音声前処理

音声認識エンジン（Whisper系）は **16kHz / モノラル / PCM WAV** 入力が最も安定し、処理も高速になる。

```bash
# 動画または音声ファイルから 16kHz mono WAV を抽出
ffmpeg -y -i "<INPUT_FILE>" -vn -ac 1 -ar 16000 -c:a pcm_s16le "scratch/audio.wav"
```

### 長時間音声（30分以上）の分割
メモリ不足やタイムアウトを防ぐため、10〜15分単位で分割して処理する。

```bash
mkdir -p scratch/chunks
ffmpeg -y -i "scratch/audio.wav" -f segment -segment_time 600 -c copy "scratch/chunks/part_%03d.wav"
```

---

## 2. 文字起こしエンジン（ASR）の実行

### 推奨: `faster-whisper`（Python / CPU環境でも比較的軽量）
```bash
uv run --with faster-whisper python3 -c "
from faster_whisper import WhisperModel

model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe(
    'scratch/audio.wav',
    language='ja',
    vad_filter=True,
    initial_prompt='固有名詞や専門用語のヒントがあればここに記述'
)
for s in segments:
    m1, sec1 = divmod(int(s.start), 60)
    print(f'({m1:02d}:{sec1:02d}) {s.text.strip()}')
"
```

- **モデル選定の目安**:
  - 速度優先・下書き（CPU）: `small` または `base`
  - 精度優先（CPUでも余裕がある / GPU環境）: `medium` または `large-v3`
- **精度向上のコツ**: `initial_prompt` に会話のテーマ、話者名、頻出する専門用語を少し渡すだけで固有名詞の誤変換が大幅に減る。
- **`openai-whisper` を使う場合**: `uvx --from openai-whisper whisper scratch/audio.wav --language ja --model small --output_format vtt` のようにVTTで出力し、`scripts/parse_vtt.py` で整形することも可能。

---

## 3. ソース別の注意点

### ボイスメモ・会議録音
- 冒頭や無音区間のノイズで幻覚（ハルシネーション：「ご視聴ありがとうございました」等の不要な出力）が出ることがあるため、`vad_filter=True`（無音区間スキップ）を必ず有効にする。
- 複数話者がいる場合は、話者の切り替わりが分かるように改行や `[話者A]` 等のラベル整理を検討する（Cosense出力時は `(話者A)` のようにブラケットを避ける）。

### ローカル動画
- 字幕がないローカル動画でも、画面内にスライドやテロップが映っている場合は、`references/youtube.md` と同様に `ffmpeg` でフレームを切り出して固有名詞の誤字を照合する。

### 音楽・歌・ライブ音源
- BGMや伴奏が大きいと音声認識の精度が落ちるため、必要に応じてボーカル分離（`demucs` 等）を行ってから `vocals.wav` に対してASRを実行する。
- 歌詞部分とMC（語り）部分が混在する場合は、両者を区別してセクション分けする。
- 既存楽曲の歌詞は著作権上の配慮が必要なケースがあるため、公開場所や共有範囲（個人メモか公開ページか）をユーザーに確認する。
