# Quality Tuning Guide

This guide covers all quality/effect control parameters and their defaults for each modality.

---

## Text (MiniMax-M3)

| Parameter | Default | Range | When to adjust |
|-----------|---------|-------|----------------|
| `temperature` | **0.7** | 0~2 | Lower (0~0.3) for deterministic output like code/facts; higher (0.8~1.2) for creative writing |
| `top_p` | **0.95** (API) | 0~1 | Lower with low temperature for strict control; usually left default |
| `max_completion_tokens` | **1024** | >= 1 | Raise for long-form content; M3 supports up to 512K |
| `thinking` | **adaptive** | disabled/enabled/adaptive | `enabled` forces reasoning for complex problems; `disabled` for speed |

**Recommended combos:**

| Scenario | temperature | thinking |
|----------|-------------|----------|
| Coding / math | 0.1~0.3 | enabled |
| Creative writing | 0.8~1.2 | adaptive |
| Translation / summarization | 0.2~0.5 | disabled |
| Complex analysis | 0.5~0.8 | enabled |

---

## Image (image-01)

| Parameter | Default | Range | When to adjust |
|-----------|---------|-------|----------------|
| `aspect_ratio` | **1:1** | 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9 | Match target display/use case |
| `width` + `height` | **aspect_ratio takes precedence** | 512~2048, multiple of 8 | Custom resolution; both must be set together |
| `n` | **1** | 1~9 | Increase to batch generate and pick the best |
| `seed` | **random** | integer | Set for reproducibility (same prompt + seed = similar result) |
| `prompt_optimizer` | **false** | true/false | Enable if results are inconsistent; disable for precise control |
| `model` | **image-01** | image-01, image-01-live | Use `image-01-live` for style presets |

**Resolution mapping (aspect_ratio -> pixels):**

| aspect_ratio | Resolution |
|-------------|------------|
| 1:1 | 1024x1024 |
| 16:9 | 1280x720 |
| 4:3 | 1152x864 |
| 3:2 | 1248x832 |
| 2:3 | 832x1248 |
| 3:4 | 864x1152 |
| 9:16 | 720x1280 |
| 21:9 | 1344x576 |

**Tips:**
- For photorealistic portraits, use `--n 3` and pick the best
- Set `--seed` when iterating on a specific composition
- Enable `--prompt-optimizer` for casual use; disable when prompt is carefully crafted

---

## Video (MiniMax-Hailuo-2.3)

| Parameter | Default | Range | When to adjust |
|-----------|---------|-------|----------------|
| `model` | **MiniMax-Hailuo-2.3** | Hailuo-2.3, Hailuo-02, T2V-01-Director, T2V-01 | `Hailuo-2.3` for best quality; `Hailuo-02` for speed |
| `resolution` | **1080P** | 720P, 768P, 1080P | Higher for final output; lower for prototyping |
| `duration` | **6** | 6 or 10 (Hailuo-2.3/02); 6 only (T2V-01) | 10s for longer scenes; costs more |
| `prompt_optimizer` | **true** | true/false | Disable when using camera directives for precise control |

**Duration x Resolution matrix:**

| Model | 6s | 10s |
|-------|----|-----|
| MiniMax-Hailuo-2.3 | 768P, 1080P | 768P |
| MiniMax-Hailuo-02 | 768P, 1080P | 768P |
| T2V-01 / T2V-01-Director | 720P | - (not supported) |

**Camera directives for precise control:**

| Type | Directives |
|------|------------|
| Horizontal pan | `[左移]`, `[右移]` |
| Horizontal tilt | `[左摇]`, `[右摇]` |
| Dolly | `[推进]`, `[拉远]` |
| Crane | `[上升]`, `[下降]` |
| Vertical tilt | `[上摇]`, `[下摇]` |
| Zoom | `[变焦推近]`, `[变焦拉远]` |
| Other | `[晃动]`, `[跟随]`, `[固定]` |

- Combine up to 3 directives in one `[]`: `[推进, 上升]`
- Sequence by placing multiple in prompt: `...[推进]... [拉远]`

---

## Music (music-2.6)

| Parameter | Default | Range | When to adjust |
|-----------|---------|-------|----------------|
| `model` | **music-2.6** | music-2.6, music-2.6-free, music-cover, music-cover-free | `music-2.6` for paid/high RPM; `*-free` for limited free tier |
| `is_instrumental` | **false** | true/false | true for background music without vocals |
| `lyrics_optimizer` | **false** | true/false | true to auto-generate lyrics from prompt |
| `output_format` | **hex** | hex/url | `url` for direct download link; `hex` for raw data |
| `audio_setting.format` | **mp3** | mp3, wav, flac | wav/flac for higher quality |
| `audio_setting.sample_rate` | **44100** | Hz | Higher for better fidelity |
| `audio_setting.bitrate` | **256000** | bps | Higher for better compression quality |

**Lyrics structure tags:**

```
[Intro], [Verse], [Pre Chorus], [Chorus], [Interlude], [Bridge],
[Outro], [Post Chorus], [Transition], [Break], [Hook], [Build Up]
```

---

## Speech (speech-2.8-hd)

| Parameter | Default | Range | When to adjust |
|-----------|---------|-------|----------------|
| `model` | **speech-2.8-hd** | speech-2.8-hd, speech-2.8-turbo, speech-2.6-hd, speech-2.6-turbo, speech-02-hd, speech-02-turbo, speech-01-hd, speech-01-turbo | `*-hd` for quality; `*-turbo` for speed |
| `voice_setting.voice_id` | **male-qn-qingse** | system voices | Query available voices via `POST /v1/query_voice {"voice_type": "system"}` |
| `voice_setting.speed` | **1.0** | 0.5~2.0 | < 1 slower; > 1 faster |
| `voice_setting.vol` | **1.0** | 0.1~10.0 | < 1 quieter; > 1 louder |
| `voice_setting.pitch` | **0** | -12~12 | Negative deeper; positive higher |
| `voice_setting.emotion` | **none** | happy, sad, angry, etc. | Match content mood |
| `audio_setting.format` | **mp3** | mp3, wav, flac | wav/flac for lossless |
| `audio_setting.sample_rate` | **32000** | Hz | 44100 or 48000 for higher fidelity |
| `audio_setting.bitrate` | **128000** | bps | 256000 for better quality |
| `audio_setting.channel` | **1** | 1, 2 | 2 for stereo |

**Emotion tags (speech-2.8 models only):**

| Tag | Effect |
|-----|--------|
| `(laughs)` | Laughter |
| `(chuckle)` | Chuckle |
| `(coughs)` | Cough |
| `(clear-throat)` | Clear throat |
| `(breath)` | Normal breathing |
| `(pant)` | Panting |
| `(sighs)` | Sigh |
| `(sneezes)` | Sneeze |

Insert directly in text: `今天很开心呢(laughs)`

---

## Summary Defaults Table

| Modality | Parameter | Default | Set by |
|----------|-----------|---------|--------|
| Text | temperature | **0.7** | CLI `--temperature` |
| Text | top_p | **0.95** (API) | CLI `--top-p` |
| Text | max_completion_tokens | **1024** | CLI `--max-tokens` |
| Text | thinking | **adaptive** | CLI `--thinking` |
| Image | aspect_ratio | **1:1** | CLI `--aspect-ratio` |
| Image | n | **1** | CLI `--n` |
| Image | seed | **random** | CLI `--seed` |
| Image | prompt_optimizer | **false** | CLI `--prompt-optimizer` |
| Video | resolution | **1080P** | CLI `--resolution` |
| Video | duration | **6** | CLI `--duration` |
| Video | prompt_optimizer | **true** | CLI `--prompt-optimizer` |
| Music | is_instrumental | **false** | CLI `--instrumental` |
| Music | output_format | **hex** | CLI `--output-format` |
| Speech | speed | **1.0** | CLI `--speed` |
| Speech | vol | **1.0** | CLI `--vol` |
| Speech | pitch | **0** | CLI `--pitch` |
| Speech | audio_format | **mp3** | CLI `--audio-format` |
