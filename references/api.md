# MiniMax API Reference

Base host: `https://api.minimaxi.com`

Authentication: `Authorization: Bearer YOUR_API_KEY`

Content type: `application/json`

## Text

Endpoint: `POST /v1/chat/completions`

Models: `MiniMax-M3`, `MiniMax-M2.7`, `MiniMax-M2.7-highspeed`, `MiniMax-M2.5`, `MiniMax-M2.5-highspeed`, `MiniMax-M2.1`, `MiniMax-M2.1-highspeed`, `MiniMax-M2`

M3 supports text, image, video input, tool calling, and thinking. M2.x series supports text and tool calling only.

Required:

- `model`: model ID
- `messages`: OpenAI-compatible chat messages (text + image_url for multimodal)

Optional:

- `temperature`: [0, 2], default 1
- `top_p`: [0, 1], default 0.95 for M3, 0.9 for M2.x
- `max_completion_tokens`: integer
- `stream`: boolean
- `tools`: array (function tools)
- `thinking`: `{type: "disabled" | "enabled" | "adaptive"}` for M3
- `service_tier`: `"standard"` or `"priority"`

Response includes `choices[].message.content`, `usage`, and `base_resp`.

## Image

Endpoint: `POST /v1/image_generation`

Models: `image-01`, `image-01-live`

Required:

- `model`: image model ID
- `prompt`: text description, max 1500 chars

Optional:

- `aspect_ratio`: `1:1`, `16:9`, `4:3`, `3:2`, `2:3`, `3:4`, `9:16`, `21:9` (image-01 only)
- `width` + `height`: [512, 2048], must be multiples of 8. `aspect_ratio` takes precedence if both set.
- `response_format`: `url` (default) or `base64`. URLs expire in 24h.
- `n`: number of images [1, 9], default 1
- `seed`: integer for reproducibility
- `prompt_optimizer`: boolean, auto-optimize prompt
- `reference_image`: URL for image-to-image

Response: `data.image_urls[]`, `metadata`, `base_resp`.

## Video

Create endpoint: `POST /v1/video_generation`

Query endpoint: `GET /v1/query/video_generation?task_id={task_id}`

Models: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-02`, `T2V-01-Director`, `T2V-01`

Required:

- `model`: video model ID
- `prompt`: text description, max 2000 chars

Optional:

- `first_image`: URL for image-to-video
- `last_image`: URL for first-last-frame video
- `duration`: video length in seconds (model-dependent, see below)
- `resolution`: `720P`, `768P`, `1080P` (model-dependent)
- `prompt_optimizer`: boolean, default true
- `callback_url`: webhook for async notifications

Duration and resolution matrix:

| Model | 6s | 10s | Supported resolutions |
|---|---|---|---|
| MiniMax-Hailuo-2.3 | 768P, 1080P | 768P | 768P (default), 1080P |
| MiniMax-Hailuo-02 | 768P, 1080P | 768P | 768P (default), 1080P |
| T2V-01 / T2V-01-Director | 720P | - | 720P (default) |

Camera movement directives (Hailuo-2.3, Hailuo-02, *-Director): `[左移]`, `[右移]`, `[推进]`, `[拉远]`, `[上升]`, `[下降]`, etc.

Query response status values: `Preparing`, `Queueing`, `Processing`, `Success`, `Fail`.

On `Success`, response includes `file_id` for download.

## Music

Endpoint: `POST /v1/music_generation`

Models: `music-2.6`, `music-2.6-free`, `music-cover`, `music-cover-free`

Required:

- `model`: music model ID
- `prompt`: style/mood/scene description

Optional:

- `lyrics`: song lyrics with structure tags (`[Verse]`, `[Chorus]`, etc.)
- `is_instrumental`: boolean, default false
- `lyrics_optimizer`: boolean, auto-generate lyrics from prompt
- `output_format`: `hex` (default) or `url`
- `stream`: boolean
- `audio_setting`: `{sample_rate, bitrate, format}`

`music-2.6-free` / `music-cover-free` are rate-limited free versions.

Response: `data.audio` (hex string or URL), `extra_info` with duration/bitrate.

## Speech (T2A)

Endpoint: `POST /v1/t2a_v2`

Models: `speech-2.8-hd`, `speech-2.8-turbo`, `speech-2.6-hd`, `speech-2.6-turbo`, `speech-02-hd`, `speech-02-turbo`, `speech-01-hd`, `speech-01-turbo`

Required:

- `model`: speech model ID
- `text`: text to synthesize, max 10000 chars
- `voice_setting.voice_id`: voice ID
- `stream`: boolean, default false

Optional:

- `voice_setting.speed`: speech speed (0.5-2.0)
- `voice_setting.vol`: volume (0.1-10.0)
- `voice_setting.pitch`: pitch adjustment (-12 to 12)
- `voice_setting.emotion`: emotion tag (e.g., happy, sad, angry)
- `audio_setting.sample_rate`: sample rate
- `audio_setting.bitrate`: bitrate
- `audio_setting.format`: `mp3`, `wav`, `flac`
- `audio_setting.channel`: 1 (mono) or 2 (stereo)
- `subtitle_enable`: boolean, return subtitle info

Response: `data.audio` (hex encoded audio data).

## Voice Management

Query voices: `POST /v1/query_voice` with body `{"voice_type": "system"}` for system voices.

## File Management

Upload: `POST /v1/files`
List: `GET /v1/files`
Retrieve: `GET /v1/files/{file_id}`
Download: `GET /v1/files/{file_id}/content`

## Error Codes

Common `base_resp.status_code` values:

- `0`: success
- `401`: unauthorized (check API key)
- `400`: invalid request parameters
- `429`: rate limit exceeded
- `500`: server error
- `1000`: general error

## Rate Limits

Refer to `https://platform.minimaxi.com/docs/guides/rate-limits` for per-model RPM/TPM limits.
