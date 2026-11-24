# ローカル動画・ボイスメモ・音声ファイル・音楽の文字起こし手順

字幕データが存在しないローカル動画（`.mp4`, `.mov`, `.mkv`）、ボイスメモ（`.m4a`, `.aac`, `.ogg`）、音声ファイル（`.wav`, `.mp3`）、音楽ファイルを文字起こしする手順。

---

## 0. ソース取得・ファイル名サニタイズ（iPhoneボイスメモ等）

- **Google Drive 連携の標準方針**: iPhone ボイスメモ側の自動書き起こしテキストではなく、**音声ファイル（`.m4a`）を Google Drive にアップロードし、Whisper 系エンジンで文字起こしする** 流れを標準とする（タイムスタンプ精度および `initial_prompt` による固有名詞ヒントが効くため）。
- **Windows 環境でのファイル名サニタイズ**:
  iPhone ボイスメモの自動命名ファイル（例：`2026-11-23T16:30:02+09:00 場所名.m4a`）には Windows のファイル名に使用できないコロン `:` が含まれる。ダウンロード・保存する際は `01_163002.m4a` のように **連番＋安全なファイル名へサニタイズ** して保存する。

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

> [!NOTE]
> `uv run` 実行時にデフォルトで最新 Python（3.15 等）が選ばれると、`ctranslate2` や `onnxruntime` の wheel が見つからず依存解決に失敗する場合がある。必ず **`--python 3.12`** のように対応 Python バージョンを明示指定すること。

### 推奨: `faster-whisper`（Python / CPU環境でも比較的軽量）
ファイルパスを直接 `model.transcribe()` に渡すと `PyAV` の `av.open(..., metadata_errors="ignore")` で `TypeError` が発生しデコードに失敗することがある。そのため、変換済みの 16kHz mono WAV を Python 標準の `wave` + `numpy` で `float32` 配列として直接読み込んで渡す。

```bash
uv run --python 3.12 --with faster-whisper --with numpy python -c "
import wave
import numpy as np
from faster_whisper import WhisperModel

with wave.open('scratch/audio.wav', 'rb') as wf:
    frames = wf.readframes(wf.getnframes())
    audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe(
    audio_array,
    language='ja',
    vad_filter=True,
    initial_prompt='固有名詞や専門用語のヒントがあればここに記述'
)
for s in segments:
    m1, sec1 = divmod(int(s.start), 60)
    print(f'({m1:02d}:{sec1:02d}) {s.text.strip()}')
"
```

- **モデル選定と GPU（CUDA）環境での推奨**:
  - 速度優先・下書き（CPU）: `small` または `base`（ただし `small` 以下は日本語の同音異義語変換が弱いため、下書き用途にとどめる）
  - **精度優先（NVIDIA GPU / CUDA 環境推奨）**: 日本語認識の精度を高めるため、NVIDIA GPU 等がある環境では CUDA 版 PyTorch を用いて **`medium` または `large-v3`** を使用することを推奨する（`device='cuda'`, `compute_type='float16'`）。
  - **`uv` での CUDA 指定のヒント**: `uv run --python 3.12 --torch-backend=auto ...`（uv 0.5 以降の自動バックエンド判定）や、`--index-url https://download.pytorch.org/whl/cu124` 等の CUDA 対応インデックス指定により GPU 版 PyTorch を利用できる。
- **精度向上のコツ**: `initial_prompt` に会話のテーマ、話者名、頻出する専門用語を少し渡すだけで固有名詞の誤変換が大幅に減る。
- **`openai-whisper` を使う場合**: `uvx --python 3.12 --from openai-whisper whisper scratch/audio.wav --language ja --model small --output_format vtt` のようにVTTで出力し、`scripts/parse_vtt.py` で整形することも可能。

### 話者分離（Speaker Diarization）付き文字起こし（`WhisperX` / `pyannote.audio`）
複数話者がいる会議・インタビュー等では、`WhisperX` と `pyannote.audio` を用いて「誰の発言か」を区別する。

1. **HuggingFace トークンの設定（初回のみ）**:
   - HuggingFace 上で以下3つのリポジトリの利用規約に同意し、`Read` 権限のアクセストークンを発行する：
     - `pyannote/speaker-diarization-3.1`
     - `pyannote/segmentation-3.0`
     - `pyannote/speaker-diarization-community-1`
   - 環境変数 `HF_TOKEN`（または `HUGGINGFACE_TOKEN`）を設定する（PowerShell例: `$env:HF_TOKEN="hf_..."`）。
2. **`WhisperX` による実行例（単語レベルでの話者切り替わり分割）**:
   `result['segments']` 単位で話者を取得すると、10〜30秒の1ブロック内に複数話者の掛け合いが混在することがある。そのため、`words` レベルに付与された `speaker` ラベルの切り替わり位置で発話を分割・改行して出力する（GPU環境では `--torch-backend=auto` の併用と `device='cuda'`, `compute_type='float16'`, モデル `medium` / `large-v3` を推奨）。
   ```bash
   uv run --python 3.12 --torch-backend=auto --with whisperx python -c "
   import os
   import whisperx
   from whisperx.diarize import DiarizationPipeline

   device = 'cpu'        # GPU環境では 'cuda'（medium / large-v3 推奨）
   compute_type = 'int8' # GPU環境では 'float16'
   audio = whisperx.load_audio('scratch/audio.wav')

   model = whisperx.load_model('small', device, compute_type=compute_type, language='ja')
   result = model.transcribe(audio, batch_size=8)

   model_a, metadata = whisperx.load_align_model(language_code='ja', device=device)
   result = whisperx.align(result['segments'], model_a, metadata, audio, device)

   diarize_model = DiarizationPipeline(model_name='pyannote/speaker-diarization-3.1', token=os.environ['HF_TOKEN'], device=device)
   diarize_segments = diarize_model(audio)
   result = whisperx.assign_word_speakers(diarize_segments, result)

   # segments 単位だと複数話者が混在するため、words レベルの話者切り替わりで分割する
   turns = []
   last_spk = 'SPEAKER_00'
   for seg in result['segments']:
       words = seg.get('words') or []
       if not words:
           spk = seg.get('speaker') or last_spk
           last_spk = spk
           text = seg.get('text', '').strip()
           if text:
               turns.append([seg['start'], spk, text])
           continue
       for w in words:
           spk = w.get('speaker') or last_spk
           last_spk = spk
           token = w.get('word', '')
           if not token:
               continue
           start = w.get('start', seg['start'])
           if not turns or turns[-1][1] != spk:
               turns.append([start, spk, token])
           else:
               turns[-1][2] += token

   for start, spk, text in turns:
       m1, sec1 = divmod(int(start), 60)
       print(f'({m1:02d}:{sec1:02d}) ({spk}) {text.strip()}')
   "
   ```
   > [!NOTE]
   > - 句読点やアライメントに失敗した単語では `w.get('speaker')` が欠落する場合があるため、上記のように直前の話者（`last_spk`）へフォールバックさせる。
   > - `asr_options={'initial_prompt': '...'}` を併用する場合、無音・雑音区間にプロンプト語句がそのまま出力されるハルシネーションが起きることがあるため、対応表レビュー時に除外対象として確認する。
3. **話者名の確定フロー**:
   - 初回出力時は `(SPEAKER_00)` / `(SPEAKER_01)` の仮ラベルを付与して整形し、**対応表レビュー時**（[references/proofreading-and-output.md](proofreading-and-output.md)）に実際の話者名（例：`SPEAKER_00` → `話者A`、`SPEAKER_01` → `話者B`）をユーザーに確認して一括置換する。

---

## 3. ソース別の注意点

### ボイスメモ・会議録音
- 冒頭や無音区間のノイズで幻覚（ハルシネーション：「ご視聴ありがとうございました」等の不要な出力）が出ることがあるため、`vad_filter=True`（無音区間スキップ）を必ず有効にする。
- 複数話者がいる場合は、上記 `WhisperX` による話者分離を行い、Cosense出力時は `[話者A]` ではなく **`(話者A)`** のようにブラケットを避けて記載する。

### ローカル動画
- 字幕がないローカル動画でも、画面内にスライドやテロップが映っている場合は、`references/youtube.md` と同様に `ffmpeg` でフレームを切り出して固有名詞の誤字を照合する。

### 音楽・歌・ライブ音源
- BGMや伴奏が大きいと音声認識の精度が落ちるため、必要に応じてボーカル分離（`demucs` 等）を行ってから `vocals.wav` に対してASRを実行する。
- 歌詞部分とMC（語り）部分が混在する場合は、両者を区別してセクション分けする。
- 既存楽曲の歌詞は著作権上の配慮が必要なケースがあるため、公開場所や共有範囲（個人メモか公開ページか）をユーザーに確認する。
