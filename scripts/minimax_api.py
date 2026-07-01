#!/usr/bin/env python3
"""Small CLI for MiniMax text, image, video, music, and speech generation APIs."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "https://api.minimaxi.com"
DEFAULT_TEXT_MODEL = "MiniMax-M3"
DEFAULT_IMAGE_MODEL = "image-01"
DEFAULT_VIDEO_MODEL = "MiniMax-Hailuo-2.3"
DEFAULT_MUSIC_MODEL = "music-2.6"
DEFAULT_SPEECH_MODEL = "speech-2.8-hd"
DEFAULT_VOICE_ID = "male-qn-qingse"
SIZE_RE = re.compile(r"^[1-9]\d*x[1-9]\d*$")

# Image aspect_ratio to dimensions mapping (for image-01 model)
ASPECT_RATIO_MAP = {
    "1:1": (1024, 1024),
    "16:9": (1280, 720),
    "4:3": (1152, 864),
    "3:2": (1248, 832),
    "2:3": (832, 1248),
    "3:4": (864, 1152),
    "9:16": (720, 1280),
    "21:9": (1344, 576),
}

VIDEO_DURATIONS = {
    ("MiniMax-Hailuo-2.3", "768P"): [6, 10],
    ("MiniMax-Hailuo-2.3", "1080P"): [6],
    ("MiniMax-Hailuo-02", "768P"): [6, 10],
    ("MiniMax-Hailuo-02", "1080P"): [6],
}


def get_api_key() -> str:
    for name in ("MINIMAX_API_KEY", "MINIMAX_API_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value
    raise SystemExit(
        "Missing API key. Set MINIMAX_API_KEY or MINIMAX_API_TOKEN."
    )


def request_json(method: str, path: str, payload: dict[str, Any] | None = None, query: dict[str, str] | None = None) -> dict[str, Any]:
    url = BASE_URL + path
    if query:
        url = url + "?" + urllib.parse.urlencode(query)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed for {path}: {exc}") from exc


def request_text(method: str, path: str, payload: dict[str, Any] | None = None, query: dict[str, str] | None = None) -> str:
    url = BASE_URL + path
    if query:
        url = url + "?" + urllib.parse.urlencode(query)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed for {path}: {exc}") from exc


def request_bytes(method: str, path: str, payload: dict[str, Any] | None = None, query: dict[str, str] | None = None) -> bytes:
    url = BASE_URL + path
    if query:
        url = url + "?" + urllib.parse.urlencode(query)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed for {path}: {exc}") from exc


def stream_summary(payload: dict[str, Any]) -> dict[str, Any]:
    raw = request_text("POST", "/v1/chat/completions", payload)
    event_count = 0
    done = False
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if data == "[DONE]":
            done = True
        elif data:
            event_count += 1
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            try:
                delta = event["choices"][0].get("delta", {})
            except (KeyError, IndexError, TypeError, AttributeError):
                continue
            content = delta.get("content")
            if isinstance(content, str):
                content_parts.append(content)
            reasoning = delta.get("reasoning_content") or delta.get("reasoning")
            if isinstance(reasoning, str):
                reasoning_parts.append(reasoning)
    result: dict[str, Any] = {
        "type": "text-stream",
        "content": "".join(content_parts) or None,
        "events": event_count,
        "done": done,
        "raw_prefix": raw[:200],
    }
    if reasoning_parts:
        result["reasoning_content"] = "".join(reasoning_parts)
    return result


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def parse_json_arg(name: str, value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON for {name}: {exc.msg} at position {exc.pos}") from exc


def needs_english_translation(prompt: str) -> bool:
    return any(ord(ch) > 127 for ch in prompt)


def translate_prompt_to_english(prompt: str) -> str:
    payload = {
        "model": DEFAULT_TEXT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Translate the user's image/video generation prompt into fluent English. "
                    "Preserve all concrete visual details, style words, camera motion, lighting, "
                    "composition constraints, and negative instructions. Return only the English prompt."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_completion_tokens": 800,
    }
    data = request_json("POST", "/v1/chat/completions", payload)
    try:
        translated = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"Prompt translation failed: {json.dumps(data, ensure_ascii=False)}") from exc
    if not translated:
        raise SystemExit("Prompt translation failed: empty translated prompt")
    return translated


def prepare_generation_prompt(prompt: str, translate: bool = True) -> tuple[str, str | None]:
    if translate and needs_english_translation(prompt):
        translated = translate_prompt_to_english(prompt)
        return translated, translated
    return prompt, None


def extract_text_content(data: dict[str, Any]) -> str | None:
    try:
        content = data["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    return content if isinstance(content, str) else None


def extract_reasoning_content(data: dict[str, Any]) -> str | None:
    try:
        msg = data["choices"][0].get("message", {})
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    for key in ("reasoning_content", "reasoning"):
        val = msg.get(key)
        if isinstance(val, str):
            return val
    return None


def output_result(
    result_type: str,
    raw: dict[str, Any],
    *,
    prompt_used: str | None = None,
    translated_prompt: str | None = None,
    urls: list[str] | None = None,
    status: str | None = None,
    next_steps: list[str] | None = None,
    raw_only: bool = False,
) -> None:
    if raw_only:
        print_json(raw)
        return
    summary: dict[str, Any] = {"type": result_type}
    if status:
        summary["status"] = status
    if urls:
        summary["urls"] = urls
    if prompt_used:
        summary["prompt_used"] = prompt_used
    if translated_prompt:
        summary["translated_prompt"] = translated_prompt
    if next_steps:
        summary["next_steps"] = next_steps
    summary["raw"] = raw
    print_json(summary)


def extract_image_urls(data: dict[str, Any]) -> list[str]:
    urls = []
    if isinstance(data.get("url"), str):
        urls.append(data["url"])
    if isinstance(data.get("image_url"), str):
        urls.append(data["image_url"])
    nested_data = data.get("data", {})
    if isinstance(nested_data, dict):
        image_urls = nested_data.get("image_urls", [])
        if isinstance(image_urls, list):
            for item in image_urls:
                if isinstance(item, str):
                    urls.append(item)
    if isinstance(nested_data, list):
        for item in nested_data:
            if isinstance(item, dict):
                for key in ("url", "image_url"):
                    if isinstance(item.get(key), str):
                        urls.append(item[key])
    return urls


def download_media(url: str, output_dir: str, filename: str | None = None) -> str:
    """Download a URL to a local file, inferring extension from URL or Content-Type."""
    if filename is None:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mp3", ".wav", ".flac"):
            ext = ".jpg"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"minimax_image_{timestamp}{ext}"
    output_path = os.path.join(output_dir, filename)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    with open(output_path, "wb") as f:
        f.write(data)
    return output_path


def extract_video_info(data: dict[str, Any]) -> tuple[list[str], str | None, str | None]:
    """Extract video URLs, file_id, and status from video query response."""
    urls = []
    status = None
    file_id = None
    if isinstance(data.get("status"), str):
        status = data["status"]
    if isinstance(data.get("file_id"), str):
        file_id = data["file_id"]
    # Check for video URL in various locations
    for key in ("video_url", "url", "download_url"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)
    # Nested data
    nested = data.get("data", {})
    if isinstance(nested, dict):
        for key in ("video_url", "url", "download_url", "audio"):
            value = nested.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                urls.append(value)
    return list(dict.fromkeys(urls)), file_id, status


def extract_music_url(data: dict[str, Any]) -> str | None:
    """Extract music audio URL or hex data from response."""
    nested = data.get("data", {})
    if isinstance(nested, dict):
        audio = nested.get("audio")
        if isinstance(audio, str):
            return audio
    return None


def check_base_resp(data: dict[str, Any]) -> None:
    base_resp = data.get("base_resp", {})
    if isinstance(base_resp, dict):
        status_code = base_resp.get("status_code", 0)
        if status_code != 0:
            status_msg = base_resp.get("status_msg", "Unknown error")
            raise SystemExit(f"MiniMax API error {status_code}: {status_msg}")


# ---- Text ----

def cmd_text(args: argparse.Namespace) -> None:
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})
    payload: dict[str, Any] = {
        "model": args.model or DEFAULT_TEXT_MODEL,
        "messages": messages,
        "temperature": args.temperature,
    }
    if args.max_tokens is not None:
        payload["max_completion_tokens"] = args.max_tokens
    if args.top_p is not None:
        payload["top_p"] = args.top_p
    if args.stream:
        payload["stream"] = True
    if args.tools_json:
        payload["tools"] = parse_json_arg("--tools-json", args.tools_json)
    if args.tool_choice_json:
        payload["tool_choice"] = parse_json_arg("--tool-choice-json", args.tool_choice_json)
    if args.thinking:
        payload["thinking"] = {"type": args.thinking}
    if args.stream:
        print_json(stream_summary(payload))
    else:
        data = request_json("POST", "/v1/chat/completions", payload)
        check_base_resp(data)
        content = extract_text_content(data)
        reasoning = extract_reasoning_content(data)
        wrapped: dict[str, Any] = {
            "type": "text",
            "content": content,
            "raw": data,
        }
        if reasoning:
            wrapped["reasoning_content"] = reasoning
        print_json(data if args.raw else wrapped)


# ---- Image ----

def cmd_image(args: argparse.Namespace) -> None:
    if args.size:
        validate_size(args.size)
    prompt, translated_prompt = prepare_generation_prompt(args.prompt, not args.no_translate)
    payload: dict[str, Any] = {
        "model": args.model or DEFAULT_IMAGE_MODEL,
        "prompt": prompt,
    }
    if args.size:
        w, h = args.size.split("x")
        payload["width"] = int(w)
        payload["height"] = int(h)
    elif args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio
    else:
        payload["aspect_ratio"] = "16:9"
    if args.n is not None:
        payload["n"] = args.n
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.response_format:
        payload["response_format"] = args.response_format
    if args.prompt_optimizer:
        payload["prompt_optimizer"] = True
    # Image-to-image: reference image
    if args.image:
        payload["reference_image"] = args.image if isinstance(args.image, str) else args.image[0]
    data = request_json("POST", "/v1/image_generation", payload)
    check_base_resp(data)
    urls = extract_image_urls(data)
    img_type = "image-to-image" if args.image else "text-to-image"
    summary: dict[str, Any] = {
        "type": img_type,
        "urls": urls,
        "prompt_used": prompt,
    }
    if translated_prompt:
        summary["translated_prompt"] = translated_prompt
    if args.download:
        output_dir = args.output_dir or "."
        os.makedirs(output_dir, exist_ok=True)
        local_paths = []
        for i, url in enumerate(urls):
            filename = None
            if args.output_file:
                base, ext = os.path.splitext(args.output_file)
                filename = f"{base}_{i}{ext}" if len(urls) > 1 else args.output_file
            path = download_media(url, output_dir, filename)
            local_paths.append(path)
        summary["local_paths"] = local_paths
    summary["raw"] = data
    print_json(summary if not args.raw else data)


# ---- Video ----

def validate_video_duration(model: str, resolution: str, duration: int) -> None:
    key = (model, resolution)
    valid = VIDEO_DURATIONS.get(key, [6])
    if duration not in valid:
        raise SystemExit(f"Invalid duration {duration} for {model}@{resolution}. Valid: {valid}")


def build_video_payload(args: argparse.Namespace) -> dict[str, Any]:
    prompt, translated_prompt = prepare_generation_prompt(args.prompt, not getattr(args, "no_translate", False))
    args._prompt_used = prompt
    args._translated_prompt = translated_prompt
    payload: dict[str, Any] = {
        "model": args.model or DEFAULT_VIDEO_MODEL,
        "prompt": prompt,
    }
    if args.resolution:
        payload["resolution"] = args.resolution
    if args.duration is not None:
        payload["duration"] = args.duration
    if args.image:
        payload["first_image"] = args.image if isinstance(args.image, str) else args.image[0]
        if isinstance(args.image, list) and len(args.image) > 1:
            payload["last_image"] = args.image[1]
    if hasattr(args, "prompt_optimizer") and args.prompt_optimizer is not None:
        payload["prompt_optimizer"] = args.prompt_optimizer
    if hasattr(args, "callback_url") and args.callback_url:
        payload["callback_url"] = args.callback_url
    return payload


def poll_video(task_id: str, timeout: int, interval: int) -> dict[str, Any]:
    deadline = time.time() + timeout
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = request_json("GET", "/v1/query/video_generation", query={"task_id": task_id})
        check_base_resp(last)
        status = str(last.get("status", ""))
        if status:
            print(f"video {task_id}: status={status}", file=sys.stderr)
        if status in {"Success", "Fail"}:
            return last
        time.sleep(interval)
    raise SystemExit(f"Timed out waiting for video {task_id}. Last response: {json.dumps(last)}")


def cmd_video(args: argparse.Namespace) -> None:
    if args.duration is not None and args.model in ("MiniMax-Hailuo-2.3", "MiniMax-Hailuo-02"):
        res = args.resolution or "1080P"
        validate_video_duration(args.model or DEFAULT_VIDEO_MODEL, res, args.duration)
    created = request_json("POST", "/v1/video_generation", build_video_payload(args))
    check_base_resp(created)
    task_id = created.get("task_id")
    if not task_id:
        raise SystemExit(f"Video create response did not include task_id: {json.dumps(created)}")
    if not args.poll:
        output_result(
            "video-task",
            created,
            prompt_used=getattr(args, "_prompt_used", None),
            translated_prompt=getattr(args, "_translated_prompt", None),
            status="created",
            next_steps=[f"python scripts/minimax_api.py video-get {task_id}"],
            raw_only=args.raw,
        )
        return
    data = poll_video(str(task_id), args.timeout, args.interval)
    urls, file_id, status = extract_video_info(data)
    output_result(
        "video-result",
        data,
        prompt_used=getattr(args, "_prompt_used", None),
        translated_prompt=getattr(args, "_translated_prompt", None),
        urls=urls,
        status=status,
        raw_only=args.raw,
    )


def cmd_video_get(args: argparse.Namespace) -> None:
    data = request_json("GET", "/v1/query/video_generation", query={"task_id": args.task_id})
    check_base_resp(data)
    urls, file_id, status = extract_video_info(data)
    output_result(
        "video-result",
        data,
        urls=urls,
        status=status,
        next_steps=[] if urls else [f"python scripts/minimax_api.py video-get {args.task_id}"],
        raw_only=args.raw,
    )


# ---- Music ----

def cmd_music(args: argparse.Namespace) -> None:
    payload: dict[str, Any] = {
        "model": args.model or DEFAULT_MUSIC_MODEL,
        "prompt": args.prompt,
    }
    if args.lyrics:
        payload["lyrics"] = args.lyrics
    if args.instrumental:
        payload["is_instrumental"] = True
    if args.lyrics_optimizer:
        payload["lyrics_optimizer"] = True
    if args.stream:
        payload["stream"] = True
    if args.output_format:
        payload["output_format"] = args.output_format
    # Audio settings
    audio_setting: dict[str, Any] = {}
    if args.sample_rate:
        audio_setting["sample_rate"] = args.sample_rate
    if args.bitrate:
        audio_setting["bitrate"] = args.bitrate
    if args.audio_format:
        audio_setting["format"] = args.audio_format
    if audio_setting:
        payload["audio_setting"] = audio_setting
    data = request_json("POST", "/v1/music_generation", payload)
    check_base_resp(data)
    audio = extract_music_url(data)
    result: dict[str, Any] = {"type": "music", "audio": audio, "raw": data}
    # Decode hex to file if requested
    if args.output_file and audio and not audio.startswith(("http://", "https://")):
        try:
            decoded = bytes.fromhex(audio)
            with open(args.output_file, "wb") as f:
                f.write(decoded)
            result["saved_to"] = args.output_file
            result["audio"] = f"<hex data saved to {args.output_file}>"
        except ValueError:
            pass
    print_json(result if not args.raw else data)


# ---- Speech ----

def cmd_speech(args: argparse.Namespace) -> None:
    payload: dict[str, Any] = {
        "model": args.model or DEFAULT_SPEECH_MODEL,
        "text": args.text,
        "stream": False,
        "voice_setting": {
            "voice_id": args.voice_id or DEFAULT_VOICE_ID,
        },
    }
    if args.speed is not None:
        payload["voice_setting"]["speed"] = args.speed
    if args.vol is not None:
        payload["voice_setting"]["vol"] = args.vol
    if args.pitch is not None:
        payload["voice_setting"]["pitch"] = args.pitch
    if args.emotion:
        payload["voice_setting"]["emotion"] = args.emotion
    audio_setting: dict[str, Any] = {}
    if args.sample_rate:
        audio_setting["sample_rate"] = args.sample_rate
    if args.bitrate:
        audio_setting["bitrate"] = args.bitrate
    if args.audio_format:
        audio_setting["format"] = args.audio_format
    if args.channel:
        audio_setting["channel"] = args.channel
    if audio_setting:
        payload["audio_setting"] = audio_setting
    data = request_json("POST", "/v1/t2a_v2", payload)
    check_base_resp(data)
    # Try to extract audio hex
    audio_hex = None
    nested = data.get("data", {})
    if isinstance(nested, dict):
        audio_hex = nested.get("audio")
    result: dict[str, Any] = {"type": "speech", "raw": data}
    if args.output_file and audio_hex:
        try:
            decoded = bytes.fromhex(audio_hex)
            with open(args.output_file, "wb") as f:
                f.write(decoded)
            result["saved_to"] = args.output_file
            result["audio_hex_preview"] = audio_hex[:100] + "..."
        except ValueError:
            result["audio"] = audio_hex
    else:
        result["audio"] = audio_hex
    print_json(result if not args.raw else data)


# ---- Smoke Test ----

def require_ok(name: str, data: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise SystemExit(f"{name} response missing {missing}: {json.dumps(data)}")
    print(f"{name}: ok")


def check_tool_call(name: str, data: dict[str, Any], strict: bool = False) -> None:
    try:
        tool_calls = data["choices"][0]["message"].get("tool_calls")
    except (KeyError, IndexError, TypeError, AttributeError):
        tool_calls = None
    if not tool_calls:
        message = f"{name}: request accepted, but response did not include tool_calls"
        if strict:
            raise SystemExit(f"{message}: {json.dumps(data, ensure_ascii=False)}")
        print(message, file=sys.stderr)
        return
    print(f"{name}: ok")


def extract_image_url(data: dict[str, Any]) -> str:
    candidates = extract_image_urls(data)
    if not candidates:
        raise SystemExit(f"Could not find image URL in response: {json.dumps(data, ensure_ascii=False)}")
    return candidates[0]


def cmd_smoke_test(args: argparse.Namespace) -> None:
    results: dict[str, Any] = {}
    # 1. Basic text
    text = request_json(
        "POST",
        "/v1/chat/completions",
        {
            "model": DEFAULT_TEXT_MODEL,
            "messages": [{"role": "user", "content": "Reply with exactly: MiniMax text ok"}],
            "max_completion_tokens": 20,
            "temperature": 0,
        },
    )
    check_base_resp(text)
    require_ok("text", text, ("choices",))
    results["text"] = text

    # 2. Streaming text
    text_stream = stream_summary(
        {
            "model": DEFAULT_TEXT_MODEL,
            "messages": [{"role": "user", "content": "Reply with exactly: MiniMax stream ok"}],
            "max_completion_tokens": 20,
            "temperature": 0,
            "stream": True,
        }
    )
    if text_stream["events"] < 1 and not text_stream["done"]:
        raise SystemExit(f"text-stream response did not look like SSE: {json.dumps(text_stream)}")
    print("text-stream: ok")
    results["text_stream"] = text_stream

    # 3. Tool calling
    text_tools = request_json(
        "POST",
        "/v1/chat/completions",
        {
            "model": DEFAULT_TEXT_MODEL,
            "messages": [{"role": "user", "content": "Use the get_test_value tool."}],
            "max_completion_tokens": 128,
            "temperature": 0,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_test_value",
                        "description": "Return a deterministic smoke test value.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string", "description": "test label"}
                            },
                            "required": ["label"],
                        },
                    },
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": "get_test_value"}},
        },
    )
    check_base_resp(text_tools)
    check_tool_call("text-tools", text_tools, strict=args.strict_tools)
    results["text_tools"] = text_tools

    # 4. Text-to-image
    image_text = request_json(
        "POST",
        "/v1/image_generation",
        {
            "model": "image-01",
            "prompt": "A simple red square icon centered on a white background",
            "aspect_ratio": "1:1",
            "n": 1,
        },
    )
    check_base_resp(image_text)
    require_ok("image-text-to-image", image_text, ("data",))
    generated_image_url = extract_image_url(image_text)
    results["image_text_to_image"] = image_text

    # 5. Image-to-image (optional)
    image_edit = None
    if args.include_image_edit:
        image_edit = request_json(
            "POST",
            "/v1/image_generation",
            {
                "model": "image-01",
                "prompt": "Turn this into a clean blue square icon while preserving the centered composition",
                "reference_image": generated_image_url,
                "aspect_ratio": "1:1",
                "n": 1,
            },
        )
        check_base_resp(image_edit)
        require_ok("image-to-image", image_edit, ("data",))
        results["image_to_image"] = image_edit

    # 6. Text-to-video (optional)
    video_result = None
    if args.include_video:
        if args.video_model in ("MiniMax-Hailuo-2.3", "MiniMax-Hailuo-02"):
            validate_video_duration(args.video_model, "1080P", args.video_duration)
        video_create = request_json(
            "POST",
            "/v1/video_generation",
            {
                "model": args.video_model,
                "prompt": "A simple cinematic shot of a red square gently floating on a white background",
                "duration": args.video_duration,
                "resolution": "1080P",
            },
        )
        check_base_resp(video_create)
        task_id = video_create.get("task_id")
        if not task_id:
            raise SystemExit(f"Video create missing task_id: {json.dumps(video_create)}")
        require_ok("video-create", video_create, ("task_id",))
        # Poll
        retrieved = poll_video(str(task_id), args.video_timeout, args.video_interval)
        urls, file_id, status = extract_video_info(retrieved)
        if status != "Success":
            raise SystemExit(f"Video did not complete successfully: {json.dumps(retrieved)}")
        if not urls:
            raise SystemExit(f"Video completed without URL: {json.dumps(retrieved)}")
        print("video: ok")
        video_result = {"create": video_create, "get": retrieved}
        results["video"] = video_result

    # 7. Music generation (optional)
    music_result = None
    if args.include_music:
        music = request_json(
            "POST",
            "/v1/music_generation",
            {
                "model": "music-2.6-free",
                "prompt": "轻快, 欢乐, 钢琴独奏, 适合阳光明媚的早晨",
                "is_instrumental": True,
            },
        )
        check_base_resp(music)
        require_ok("music", music, ("data",))
        print("music: ok")
        music_result = music
        results["music"] = music_result

    # 8. Speech synthesis (optional)
    speech_result = None
    if args.include_speech:
        speech = request_json(
            "POST",
            "/v1/t2a_v2",
            {
                "model": "speech-2.8-hd",
                "text": "你好，这是MiniMax语音合成测试。",
                "stream": False,
                "voice_setting": {"voice_id": "male-qn-qingse"},
            },
        )
        check_base_resp(speech)
        require_ok("speech", speech, ("data",))
        print("speech: ok")
        speech_result = speech
        results["speech"] = speech_result

    print_json(results)


def validate_size(value: str | None, name: str = "size") -> None:
    if value and not SIZE_RE.match(value):
        raise SystemExit(f"Invalid {name}: {value}. Expected WIDTHxHEIGHT, for example 1024x768.")


# ---- CLI ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call MiniMax generation APIs.")
    sub = parser.add_subparsers(dest="command", required=True)

    # text
    text = sub.add_parser("text", help="Create a chat completion.")
    text.add_argument("--prompt", required=True)
    text.add_argument("--system")
    text.add_argument("--model", default=DEFAULT_TEXT_MODEL)
    text.add_argument("--temperature", type=float, default=0.7)
    text.add_argument("--top-p", type=float)
    text.add_argument("--max-tokens", type=int, default=1024)
    text.add_argument("--stream", action="store_true")
    text.add_argument("--thinking", choices=["disabled", "enabled", "adaptive"])
    text.add_argument("--tools-json", help="JSON array for OpenAI-compatible tool definitions.")
    text.add_argument("--tool-choice-json", help="JSON object/string for OpenAI-compatible tool_choice.")
    text.add_argument("--raw", action="store_true", help="Print the raw provider response.")
    text.set_defaults(func=cmd_text)

    # image
    image = sub.add_parser("image", help="Generate or edit an image.")
    image.add_argument("--prompt", required=True)
    image.add_argument("--model", default=DEFAULT_IMAGE_MODEL)
    image.add_argument("--size", help="Output size like 1024x768 (width x height).")
    image.add_argument("--aspect-ratio", help="Aspect ratio like 16:9, 1:1, 4:3, etc.")
    image.add_argument("--image", help="Input image URL for image-to-image.")
    image.add_argument("--n", type=int, default=1, help="Number of images (1-9).")
    image.add_argument("--seed", type=int)
    image.add_argument("--response-format", default="url", choices=["url", "base64"])
    image.add_argument("--prompt-optimizer", action="store_true")
    image.add_argument("--no-translate", action="store_true", help="Do not translate non-English prompts.")
    image.add_argument("--download", action="store_true", help="Download generated image(s) to local disk.")
    image.add_argument("--output-dir", help="Directory to save downloaded images (default: current directory).")
    image.add_argument("--output-file", help="Filename for the downloaded image. If n>1, appends _0, _1, etc.")
    image.add_argument("--raw", action="store_true")
    image.set_defaults(func=cmd_image)

    # video
    video = sub.add_parser("video", help="Create a video generation task.")
    video.add_argument("--prompt", required=True)
    video.add_argument("--model", default=DEFAULT_VIDEO_MODEL)
    video.add_argument("--image", help="Input image URL for image-to-video.")
    video.add_argument("--duration", type=int, default=6, help="Video duration in seconds.")
    video.add_argument("--resolution", default="1080P", choices=["720P", "768P", "1080P"])
    video.add_argument("--prompt-optimizer", type=bool, default=True)
    video.add_argument("--no-translate", action="store_true")
    video.add_argument("--poll", action="store_true")
    video.add_argument("--timeout", type=int, default=900)
    video.add_argument("--interval", type=int, default=10)
    video.add_argument("--raw", action="store_true")
    video.set_defaults(func=cmd_video)

    # video-get
    video_get = sub.add_parser("video-get", help="Retrieve a video result by task_id.")
    video_get.add_argument("task_id", help="Task ID returned from video creation.")
    video_get.add_argument("--raw", action="store_true")
    video_get.set_defaults(func=cmd_video_get)

    # music
    music = sub.add_parser("music", help="Generate music from prompt and lyrics.")
    music.add_argument("--prompt", required=True, help="Music style description.")
    music.add_argument("--lyrics", help="Song lyrics with structure tags.")
    music.add_argument("--model", default=DEFAULT_MUSIC_MODEL)
    music.add_argument("--instrumental", action="store_true", help="Generate instrumental only.")
    music.add_argument("--lyrics-optimizer", action="store_true", help="Auto-generate lyrics from prompt.")
    music.add_argument("--output-format", default="url", choices=["url", "hex"])
    music.add_argument("--stream", action="store_true")
    music.add_argument("--sample-rate", type=int)
    music.add_argument("--bitrate", type=int)
    music.add_argument("--audio-format", choices=["mp3", "wav"])
    music.add_argument("--output-file", help="Save hex audio to file.")
    music.add_argument("--raw", action="store_true")
    music.set_defaults(func=cmd_music)

    # speech
    speech = sub.add_parser("speech", help="Text-to-speech synthesis.")
    speech.add_argument("--text", required=True)
    speech.add_argument("--model", default=DEFAULT_SPEECH_MODEL)
    speech.add_argument("--voice-id", default=DEFAULT_VOICE_ID)
    speech.add_argument("--speed", type=float, help="Speech speed (0.5-2.0).")
    speech.add_argument("--vol", type=float, help="Volume (0.1-10.0).")
    speech.add_argument("--pitch", type=int, help="Pitch adjustment (-12 to 12).")
    speech.add_argument("--emotion", help="Emotion tag (e.g., happy, sad, angry).")
    speech.add_argument("--sample-rate", type=int)
    speech.add_argument("--bitrate", type=int)
    speech.add_argument("--audio-format", choices=["mp3", "wav", "flac"])
    speech.add_argument("--channel", type=int, choices=[1, 2])
    speech.add_argument("--output-file", help="Save audio to file.")
    speech.add_argument("--raw", action="store_true")
    speech.set_defaults(func=cmd_speech)

    # smoke-test
    smoke = sub.add_parser("smoke-test", help="Run live API tests.")
    smoke.add_argument("--strict-tools", action="store_true")
    smoke.add_argument("--include-image-edit", action="store_true")
    smoke.add_argument("--include-video", action="store_true")
    smoke.add_argument("--include-music", action="store_true")
    smoke.add_argument("--include-speech", action="store_true")
    smoke.add_argument("--video-model", default="MiniMax-Hailuo-2.3")
    smoke.add_argument("--video-duration", type=int, default=6)
    smoke.add_argument("--video-timeout", type=int, default=900)
    smoke.add_argument("--video-interval", type=int, default=10)
    smoke.set_defaults(func=cmd_smoke_test)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
