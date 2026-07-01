---
name: minimax-generation
description: Call MiniMax APIs for text, image, video, music, and speech generation. Use when the user asks to use MiniMax models, MiniMax-M3, Hailuo video, MiniMax image/music/speech/TTS, api.minimaxi.com, or to generate text, images, videos, music, or speech via MiniMax.
---

# MiniMax Generation

Use this skill to call MiniMax text, image, video, music, and speech synthesis APIs through `https://api.minimaxi.com`.

## Quick Start

1. Read `references/api.md` when endpoint details, parameters, or response fields are needed.
2. Read `references/tuning.md` for quality control parameters, defaults, and recommended combos for each modality.
3. Use `scripts/minimax_api.py` for real API calls instead of rewriting curl by hand.
4. Require an API key in `MINIMAX_API_KEY` or `MINIMAX_API_TOKEN`. Never print the key.
5. For light live verification, run `smoke-test`. It tests text, streaming, tool-calling, and image by default. Add `--include-video`, `--include-music`, and `--include-speech` for additional modalities.

## Quotas & Plans

| Plan tier | Text | Image | Music | Speech | Video |
|-----------|------|-------|-------|--------|-------|
| **Plus** (大多数用户) | ✅ | ✅ | ✅ | ✅ | ❌ 需额外订阅 |
| **Video 专用包** | - | - | - | - | ✅ |

- **Plus 订阅**：文本、图像、语音、音乐 **共享同一额度池**。当调用报错 `2056: Token 额度限制` 时，说明这四个模态的总额度已用完，需充值或等待重置。
- **视频**：与 Plus 额度独立，需要单独开通视频生成包。如未订阅，视频任务会直接返回 `2056` 或相关权限不足的错误。

## Commands

Text generation:

```bash
python scripts/minimax_api.py text --prompt "Write a concise product tagline for an AI assistant."
```

Streaming text:

```bash
python scripts/minimax_api.py text --prompt "Write a short product intro." --stream
```

Image generation:

```bash
python scripts/minimax_api.py image --prompt "A luminous floating city above a misty canyon at sunrise, cinematic realism" --aspect-ratio 16:9
```

Download the generated image to local disk (recommended when the returned URL may not render inline in your chat client):

```bash
python scripts/minimax_api.py image --prompt "A luminous floating city above a misty canyon at sunrise, cinematic realism" --aspect-ratio 16:9 --download
```

Save to a specific file:

```bash
python scripts/minimax_api.py image --prompt "Sunset over ocean" --aspect-ratio 16:9 --download --output-file sunset.png
```

Image-to-image:

```bash
python scripts/minimax_api.py image --prompt "Turn the scene into a rainy cyberpunk night while preserving composition" --image https://example.com/input.png
```

Video generation with polling:

```bash
python scripts/minimax_api.py video --prompt "A cinematic shot of a cat walking on the beach at sunset" --poll
```

Image-to-video:

```bash
python scripts/minimax_api.py video --prompt "Animate subtle camera movement and natural lighting" --image https://example.com/image.png --poll
```

Retrieve a video task:

```bash
python scripts/minimax_api.py video-get <task_id>
```

Music generation:

```bash
python scripts/minimax_api.py music --prompt "轻快, 欢乐, 钢琴独奏, 阳光明媚的早晨" --instrumental
```

Speech synthesis:

```bash
python scripts/minimax_api.py speech --text "你好，这是语音合成测试" --output-file output.mp3
```

Light live smoke test (text + image only, no video or audio quota consumed):

```bash
python scripts/minimax_api.py smoke-test
```

Full modality smoke test (text + image + music + speech + video):

```bash
python scripts/minimax_api.py smoke-test --include-video --include-music --include-speech
```

> **Note:** `--include-video` requires a separate video subscription. If your plan is Plus (no video pack), video tests will fail with `2056` (quota/permission).

## Workflow

- Prefer `MiniMax-M3` for text chat/completions. It supports 1M context, multimodal input (text + image + video), tool calling, and thinking content. M2.x models support text and tool calling only.
- Prefer `image-01` for text-to-image and image-to-image. Use `aspect_ratio` for standard sizes, or `width` + `height` for custom dimensions (512-2048, multiples of 8). Use `image-01-live` for style presets.
- Prefer `MiniMax-Hailuo-2.3` for video generation. It supports 6s/10s durations, 768P/1080P resolutions, and camera movement directives like `[推进]`, `[拉远]`, `[上升]`. The API is asynchronous: create a task first, then poll or query by `task_id`.
- For music, use `music-2.6` (paid) or `music-2.6-free` (rate-limited). Set `is_instrumental` for pure music without vocals. Use `lyrics_optimizer` to auto-generate lyrics from the prompt.
- For speech (T2A), use `speech-01-turbo`. Query available voices with `POST /v1/query_voice {"voice_type": "system"}`. Save the hex audio output to a file with `--output-file`.
- For image and video generation, convert any non-English user prompt to a fluent English generation prompt before calling the API. The script handles this automatically unless `--no-translate` is passed.
- All responses include a `base_resp` field with `status_code` and `status_msg`. Non-zero `status_code` indicates an error.

## Output Handling

- Return generated image/video/music URLs directly by default. Do not download, save, or inspect generated media unless the user explicitly asks for a local file.
- **Known issue:** Generated image URLs are signed Aliyun OSS links. Some chat clients (including Kimi Desktop) may fail to render them inline because the client's preview request sends a `HEAD` probe or includes a `Referer`/`Origin` header that the OSS signature does not authorize. If this happens, use `--download` to save the image locally and return the file path.
- For image responses, expect URL-style results in `data.image_urls[]`.
- For video responses, query by `task_id` to get status and `file_id` on success.
- For music responses, `data.audio` contains hex-encoded audio or a URL depending on `output_format`.
- For speech responses, `data.audio` contains hex-encoded audio. Use `--output-file` to save.
- URL expiry: image and music URLs are valid for 24 hours.
- If a request fails, report HTTP status and `base_resp` error without exposing the API key.
