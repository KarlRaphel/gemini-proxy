
# Gemini Proxy

🌎 **Gemini Proxy** 是一个轻量级的流式 HTTP 代理，专为与 [Google Gemini](https://ai.google.dev/) 等 AI 服务对接设计。它支持将请求通过本地或指定的中间代理(socks5/http)转发，安全灵活，部署简单。适合需要科学上网或企业安全隔离场景。

❓ **Gemini Proxy 与 [One API](https://github.com/songquanpeng/one-api) 等代理有何区别？** One API 等服务虽然同样可以设置网络代理，但是为了统一管理，通常会将Gemini等其他AI服务转换为OpenAI兼容形式，缺失了一些功能。此外，Token用量记录等功能也增加了一些复杂性。

🔥 **实现方式：**
<div align="center">
  <img src="./docs/framework.svg" alt="实现架构" width="300">
</div>

---

## 特性亮点

- 🚀 **流式转发**：支持大模型流式响应，极低延迟，体验丝滑。
- 🛡️ **代理支持**：可配置 socks5 或 http 中间代理，轻松绕过网络限制。
- 🏠 **自定义目标**：不仅限于 Gemini API，任意指定目标服务。
- 🐳 **Docker 一键部署**：开箱即用，适合服务器/本地快速部署。
- 📜 **详细日志**：内置日志，方便排查问题和监控流量。

---

## 快速开始

### 1. 拉取或构建镜像

你可以直接使用 Dockerfile 构建镜像：

```bash
docker build -t gemini-proxy .
```

### 2. 配置并启动（推荐 Docker Compose）

在你的 `docker-compose.yml` 文件中：

```yaml
services:
  gemini-proxy:
    container_name: gemini-proxy
    image: gemini-proxy
    restart: always
    network_mode: bridge
    ports:
      - 8080:8080
    environment:
      # 必需: 配置你的代理（http 或 socks5，按需选择）
      - PROXY_URL=http://192.168.0.123:7890
      # 可选: 指定要代理的目标API
      # - TARGET_URL=https://generativelanguage.googleapis.com
```

**启动服务：**
```bash
docker compose up -d
```

### 3. 直接运行（开发调试）

如果你需要本地调试，也可以直接运行：

```bash
pip install -r requirements.txt
python main.py
```

---

## 使用说明

项目运行后，所有请求都会经过你的代理被转发到 `TARGET_URL`（默认为 Gemini API），并支持流式响应。你可以像这样使用：

```bash
curl "http://localhost:8080/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'
```

## OpenAI 兼容性

Gemini 官方提供 [OpenAI 兼容的 API](https://ai.google.dev/gemini-api/docs/openai)，你可以像这样使用：

```bash
curl "http://localhost:8080/v1beta/openai/chat/completions" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer GEMINI_API_KEY" \
-d '{
    "model": "gemini-2.0-flash",
    "messages": [
        {"role": "user", "content": "Explain to me how AI works"}
    ]
    }'
```

**Tips:**
- 支持 GET/POST/PUT/DELETE/PATCH 等常见 HTTP 方法。
- 响应为流式（chunked），适合大模型长文本输出。
- 所有请求头（如 Authorization）和请求体会被完整转发。

---

## 环境变量说明

| 变量名      | 作用                                             | 示例                         |
| ----------- | ----------------------------------------------- | --------------------------- |
| PROXY_URL   | 中间代理地址，支持 http 或 socks5 格式           | http://1.2.3.4:7890         |
| TARGET_URL  | 目标 API 地址，默认 Google Gemini API            | https://generativelanguage.googleapis.com |

---

## 进阶用法

### 1. 仅作为本地端口转发（无中间代理）

如部署在海外 VPS，可不设置 `PROXY_URL`，直接作为本地转发：

```yaml
environment:
  # - PROXY_URL=    # 留空即可
```

### 2. 支持 socks5 代理

```yaml
environment:
  - PROXY_URL=socks5://127.0.0.1:1080
```

### 3. 转发到自定义 API

```yaml
environment:
  - TARGET_URL=https://your.custom.api.com
```

---

## 常见问题

1. **代理连接失败怎么办？**
   - 确认 `PROXY_URL` 填写正确，且代理服务器可达。

2. **API 报 401/403？**
   - 检查 Authorization 头部是否正确转发，API key 有效。

3. **流式响应不完整/卡住？**
   - 检查网络连通性，必要时增大超时时间。

---

## 技术原理

- 使用 Flask 实现 HTTP 反向代理。
- 利用 `requests` 的 `stream=True`，实现 chunked 流式转发，极大提升大模型响应体验。
- 自动剥离/透传大部分 HTTP 头，兼容性强。

---

## 生产部署建议

- 推荐使用 Gunicorn 等 WSGI 服务器生产部署：
  ```bash
  gunicorn -w 4 -b 0.0.0.0:42082 app:app --timeout 120
  ```
- 结合 Docker Compose，支持热更新、自动重启。

---

## 贡献

欢迎提 issue 和 PR！如需定制化功能，请联系作者。

---

## License

MIT

---

**让你的 Gemini API 接入更简单、更流畅、更安全！**

---