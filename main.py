import os
from flask import Flask, request, Response # 导入 Response 类
import requests
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

TARGET_URL = os.getenv('TARGET_URL', 'https://generativelanguage.googleapis.com')
PROXY_URL = os.getenv('PROXY_URL')

proxies = None
if PROXY_URL:
    PROXY_URL = PROXY_URL.strip('\'"') # 清理可能存在的引号
    try:
        parsed_proxy = urlparse(PROXY_URL)
        if not parsed_proxy.scheme or not parsed_proxy.netloc:
            raise ValueError("Invalid proxy URL format after cleaning.")
        proxies = {'http': PROXY_URL, 'https': PROXY_URL}
        logging.info(f"Using proxy: {proxies}")
    except ValueError as e:
        logging.error(f"Invalid PROXY_URL ('{PROXY_URL}'): {e}. Not using intermediate proxy.")
        PROXY_URL = None
else:
    logging.info("Not using intermediate proxy.")

try:
    TARGET_HOST = urlparse(TARGET_URL).netloc
    if not TARGET_HOST:
        raise ValueError("Invalid TARGET_URL, cannot extract host.")
    logging.info(f"Target Host configured: {TARGET_HOST}")
except Exception as e:
    logging.error(f"FATAL: Error parsing TARGET_URL ('{TARGET_URL}'): {e}")
    TARGET_HOST = None
# --- 配置部分结束 ---

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_handler(path):
    if not TARGET_HOST:
        return "Internal Server Error: Proxy target not configured correctly.", 500

    target = f"{TARGET_URL.rstrip('/')}/{path.lstrip('/')}"
    query = request.query_string.decode()
    if query:
        target += f'?{query}'

    logging.info(f"Incoming request: {request.method} {request.full_path}")
    logging.info(f"Forwarding to target URL: {target}")
    if proxies:
        logging.info(f"via proxy: {PROXY_URL}")

    headers_to_forward = {k: v for k, v in request.headers}
    headers_to_forward['Host'] = TARGET_HOST
    headers_to_forward.pop('Connection', None)
    headers_to_forward.pop('Transfer-Encoding', None)

    logging.info(f"Forwarding Headers: {headers_to_forward}")

    try:
        # ================== 关键修改点 1: stream=True ==================
        resp = requests.request(
            method=request.method,
            url=target,
            headers=headers_to_forward,
            # 对于请求体，如果需要流式上传大文件，需用 request.stream
            # 对于普通 API 调用，request.get_data() 通常可以
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            proxies=proxies,
            timeout=60, # 流式请求可能需要更长的超时时间
            verify=True,
            stream=True  # <--- 告诉 requests 不要立即下载响应体
        )

        logging.info(f"Received response status: {resp.status_code}, streaming enabled.")

        def generate_stream():
            """一个生成器，逐块读取并 yield 响应内容"""
            try:
                # iter_content 会按块读取数据
                # chunk_size 可以调整，None 让 requests 决定
                for chunk in resp.iter_content(chunk_size=8192):
                    # 如果 chunk 非空，则 yield 它
                    if chunk:
                        # logging.debug(f"Yielding chunk: {len(chunk)} bytes") # 取消注释以调试
                        yield chunk
            except Exception as e:
                logging.error(f"Error while streaming chunks: {e}")
            finally:
                # 确保原始响应连接被关闭
                resp.close()
                logging.info("Original response connection closed.")

        # 准备需要透传的响应头
        response_headers = {}
        for k, v in resp.headers.items():
            # 过滤掉不应由代理控制或可能引起问题的头
            if k.lower() not in [
                'content-encoding',    # requests 的 iter_content 默认会解压
                'transfer-encoding', # 由 Flask/Werkzeug 处理流式传输
                'connection',
                'content-length',    # 流式响应长度通常未知
                # 'keep-alive',        # 连接管理由服务器和代理处理
            ]:
                response_headers[k] = v

        # 使用 Response 对象包装生成器，并传递状态码和头部
        # Flask 会自动处理生成器，实现流式响应 (Transfer-Encoding: chunked)
        return Response(generate_stream(), status=resp.status_code, headers=response_headers)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during request forwarding: {e}")
        status_code = 502
        if isinstance(e, requests.exceptions.Timeout):
            status_code = 504
        return f"Proxy Error: {str(e)}", status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
