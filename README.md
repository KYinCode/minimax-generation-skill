# minimax-generation

**MiniMax 开放平台 API Skill**，支持文本、图像、视频、音乐和语音五大模态的生成能力。

---

## 特性

- **文本生成**: 基于 `MiniMax-M3`，支持 1M 上下文、多模态输入、thinking 和工具调用
- **图像生成**: 基于 `image-01`，支持文生图、图生图、多种宽高比和自定义尺寸
- **视频生成**: 基于 `MiniMax-Hailuo-2.3`，支持 6s/10s 时长、多种分辨率、运镜指令
- **音乐生成**: 基于 `music-2.6`，支持文本生成音乐和参考音频翻唱
- **语音合成**: 基于 `speech-2.8-hd`，支持多音色、语速、音量、情感控制
- **统一 CLI**: 一个脚本覆盖所有模态，无需第三方依赖

---

## 项目结构

```
minimax-generation/
├── SKILL.md                  # Skill 主文档（触发条件 + 使用指南）
├── agents/
│   └── openai.yaml           # Agent 界面配置
├── references/
│   └── api.md                # MiniMax API 完整参考文档
└── scripts/
    └── minimax_api.py        # 统一的 Python CLI 工具
```

---

## 快速开始

### 环境变量

```bash
export MINIMAX_API_KEY="your-api-key-here"
```

### 文本生成

```bash
python scripts/minimax_api.py text \
  --prompt "写一段产品 Slogan" \
  --model MiniMax-M3 \
  --temperature 0.7
```

### 图像生成

```bash
python scripts/minimax_api.py image \
  --prompt "A luminous floating city above misty canyon at sunrise" \
  --aspect-ratio 16:9 \
  --n 1
```

### 视频生成（带轮询）

```bash
python scripts/minimax_api.py video \
  --prompt "A cinematic shot of a cat walking on the beach at sunset" \
  --model MiniMax-Hailuo-2.3 \
  --duration 6 \
  --resolution 1080P \
  --poll
```

### 音乐生成

```bash
python scripts/minimax_api.py music \
  --prompt "轻快, 欢乐, 钢琴独奏, 阳光明媚的早晨" \
  --instrumental \
  --output-format url
```

### 语音合成

```bash
python scripts/minimax_api.py speech \
  --text "你好，这是 MiniMax 语音合成测试" \
  --voice-id male-qn-qingse \
  --output-file output.mp3
```

### 冒烟测试

```bash
# 基础测试（文本 + 流式 + 工具 + 图像）
python scripts/minimax_api.py smoke-test

# 全量测试（+ 视频 + 音乐 + 语音）
python scripts/minimax_api.py smoke-test \
  --include-video --include-music --include-speech
```

---

## CLI 命令速查

| 命令 | 说明 | 关键参数 |
|------|------|----------|
| `text` | 文本对话/补全 | `--prompt`, `--model`, `--stream`, `--thinking` |
| `image` | 文生图 / 图生图 | `--prompt`, `--aspect-ratio`, `--image`(参考图) |
| `video` | 视频生成（异步） | `--prompt`, `--image`, `--duration`, `--poll` |
| `video-get` | 查询视频任务 | `task_id` |
| `music` | 音乐生成 | `--prompt`, `--lyrics`, `--instrumental` |
| `speech` | 语音合成(T2A) | `--text`, `--voice-id`, `--output-file` |
| `smoke-test` | 全链路测试 | `--include-video/music/speech` |

---

## API 端点映射

| 模态 | 端点 | 方法 |
|------|------|------|
| 文本 | `/v1/chat/completions` | POST |
| 图像 | `/v1/image_generation` | POST |
| 视频创建 | `/v1/video_generation` | POST |
| 视频查询 | `/v1/query/video_generation` | GET |
| 音乐 | `/v1/music_generation` | POST |
| 语音 | `/v1/t2a_v2` | POST |

---

## 模型列表

### 文本
- `MiniMax-M3`（推荐）: 1M 上下文，多模态，thinking，工具调用
- `MiniMax-M2.7` / `M2.5` / `M2.1` / `M2` 及其 highspeed 版本

### 图像
- `image-01`: 文生图、图生图、自定义尺寸
- `image-01-live`: 额外支持画风预设

### 视频
- `MiniMax-Hailuo-2.3`（推荐）: 6s/10s，768P/1080P，运镜指令
- `MiniMax-Hailuo-02`: 同上
- `T2V-01-Director` / `T2V-01`: 基础视频生成

### 音乐
- `music-2.6` / `music-2.6-free`: 文本生成音乐
- `music-cover` / `music-cover-free`: 参考音频翻唱

### 语音
- `speech-2.8-hd` / `speech-2.8-turbo`（推荐）
- `speech-2.6-hd` / `speech-2.6-turbo`
- `speech-02-hd` / `speech-02-turbo`
- `speech-01-hd` / `speech-01-turbo`

---

## 响应格式

所有响应遵循 MiniMax 的统一格式：

```json
{
  "data": { ... },
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

- `status_code = 0`: 成功
- `status_code != 0`: 错误，详见 `references/api.md` 错误码表

---

## 依赖

- Python 3.8+
- 仅使用标准库：`urllib`, `json`, `argparse`, `os`, `sys`, `time`
- **无需第三方依赖**

---

## License

同原项目许可证
