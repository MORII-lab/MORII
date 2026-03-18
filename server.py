import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request


BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
ENV_FILE = BASE_DIR / ".env"
OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_PERSONA_NAME = "微光"
DEFAULT_PERSONA_TAGLINE = "像一个沉静、真诚、不评判人的深夜来信朋友。"
DEFAULT_CRISIS_SUPPORT_TEXT = "如果你有可能马上伤害自己、伤害他人，或已经无法保证安全，请立刻联系当地紧急服务，或马上去最近的医院/急诊。也请尽快联系一个你信任的人，让对方现在陪着你。"
CRISIS_PATTERNS = [
    r"自杀",
    r"轻生",
    r"想死",
    r"不想活",
    r"活着没意义",
    r"结束生命",
    r"去死",
    r"杀了自己",
    r"伤害自己",
    r"割腕",
    r"跳楼",
    r"吞药",
    r"服药自杀",
    r"上吊",
    r"自残",
    r"我会杀了他",
    r"我想杀人",
    r"伤害别人",
    r"同归于尽",
    r"suicide",
    r"kill myself",
    r"end my life",
    r"hurt myself",
    r"self harm",
    r"self-harm",
    r"kill him",
    r"kill her",
    r"kill them",
    r"hurt someone"
]

def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def extract_output_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"].strip()

    chunks = []
    for item in payload.get("output", []):
        if item.get("type") != "message" or item.get("role") != "assistant":
            continue

        for part in item.get("content", []):
            if part.get("type") in {"output_text", "text"} and part.get("text"):
                chunks.append(part["text"].strip())

    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


def get_persona_name() -> str:
    return os.getenv("MORII_PERSONA_NAME", DEFAULT_PERSONA_NAME).strip() or DEFAULT_PERSONA_NAME


def get_persona_tagline() -> str:
    return os.getenv("MORII_PERSONA_TAGLINE", DEFAULT_PERSONA_TAGLINE).strip() or DEFAULT_PERSONA_TAGLINE


def get_crisis_support_text() -> str:
    return os.getenv("CRISIS_SUPPORT_TEXT", DEFAULT_CRISIS_SUPPORT_TEXT).strip()


def build_system_prompt() -> str:
    persona_name = get_persona_name()
    persona_tagline = get_persona_tagline()

    return f"""
你是“微光对话”的陪伴型助手，名字叫“{persona_name}”。
你的人格设定：{persona_tagline}

你要始终维持这一种稳定人格：
1. 像一个愿意深夜安静回信的人，而不是客服、老师或说教者。
2. 温和，但不过度热情；真诚，但不夸张；稳定，但不冷淡。
3. 不用网络鸡汤，不堆砌空泛金句，不反复说同样的安慰模板。
4. 更像陪对方一起把情绪理顺，而不是急着给答案。

你的任务：
1. 先回应用户最核心的感受或处境，再给鼓励或轻微建议。
2. 尽量引用或贴近用户刚刚说的重点，让对方感到“被认真听见”。
3. 回复以中文为主，除非对方明确要求别的语言。
4. 优先短段落，整体像真实消息往来，不要写成长篇说理。
5. 末尾最多提出一个温和的问题，帮助对话继续。

你的语气规范：
1. 少用感叹号、口号式鼓励、过度煽情的表达。
2. 不要用“你一定可以”“一切都会好的”这类空泛安慰直接收尾。
3. 允许留白和克制，重点是陪伴感与可信度。
4. 即使给建议，也只给眼前很轻的一小步，不要一下子说很多条。

你的边界：
1. 不要声称自己是医生、治疗师或能提供专业诊断。
2. 不提供危险、自伤、伤害他人的操作性建议。
3. 如果用户出现明显的自伤、自杀、伤害他人、紧急危险信号：
   - 明确表达关切
   - 鼓励立即联系当地紧急服务、身边可信任的人或专业危机支持
   - 语气保持镇定、直接、温柔
4. 如果用户并非紧急危险，就保持陪伴风格，不要无端升级成危机话术。
""".strip()


def detect_crisis_signal(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False

    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in CRISIS_PATTERNS)


def build_crisis_reply() -> str:
    support_text = get_crisis_support_text()
    persona_name = get_persona_name()
    return (
        f"我是{persona_name}，我现在最在意的是你的安全。\n\n"
        "如果你有可能马上伤害自己、伤害别人，或者已经控制不住冲动，请不要一个人扛着，立刻联系当地紧急服务，"
        "或者马上去最近的医院/急诊。\n\n"
        "也请现在就联系一个你信任的人，直接告诉对方：我现在状态很危险，需要你立刻陪我。\n\n"
        f"{support_text}\n\n"
        "如果你愿意，只要回复我“已联系”或“还没”，我会尽量继续陪你把下一步说清楚。"
    )


def normalize_messages(messages):
    normalized = []
    for item in messages[-12:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue

        normalized.append({
            "role": role,
            "content": content
        })

    return normalized


def normalize_memory(items):
    normalized = []
    for item in items[:8]:
        if isinstance(item, str):
            text = item.strip()
            if text:
                normalized.append(text)
            continue

        if not isinstance(item, dict):
            continue

        label = str(item.get("label", "")).strip()
        text = str(item.get("text", "")).strip()
        if not text:
            continue

        if label:
            normalized.append(f"{label}：{text}")
        else:
            normalized.append(text)

    return normalized


def build_memory_prompt(memory_items) -> str:
    if not memory_items:
        return ""

    lines = ["下面这些是这段对话里已经形成的记忆点，只在合适时自然使用："]
    lines.extend(f"- {item}" for item in memory_items)
    lines.append("不要生硬复述所有记忆；只挑和当前这句最相关的内容，让用户感到你记得、你在持续听。")
    return "\n".join(lines)


class MoriiHandler(BaseHTTPRequestHandler):
    server_version = "MoriiHTTP/1.0"

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: bytes, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html)

    def _send_no_content(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._send_no_content()

    def do_GET(self):
        if self.path in {"/", "/index.html"}:
            self._send_html(INDEX_FILE.read_bytes())
            return

        if self.path == "/api/health":
            model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
            has_key = bool(os.getenv("OPENAI_API_KEY"))
            self._send_json({
                "ok": True,
                "ai_configured": has_key,
                "mode": "ai" if has_key else "demo",
                "model": model,
                "crisis_support_text": get_crisis_support_text(),
                "persona_name": get_persona_name(),
                "persona_tagline": get_persona_tagline()
            })
            return

        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            payload = json.loads(raw_body.decode("utf-8"))
            messages = normalize_messages(payload.get("messages", []))
            memory_items = normalize_memory(payload.get("memory", []))

            if not messages:
                self._send_json({"error": "No valid messages were provided."}, HTTPStatus.BAD_REQUEST)
                return

            latest_user_message = next(
                (item["content"] for item in reversed(messages) if item["role"] == "user"),
                ""
            )
            if detect_crisis_signal(latest_user_message):
                self._send_json({
                    "reply": build_crisis_reply(),
                    "mode": "crisis",
                    "support": get_crisis_support_text()
                })
                return

            if not os.getenv("OPENAI_API_KEY"):
                self._send_json(
                    {"error": "OPENAI_API_KEY is not configured on the server."},
                    HTTPStatus.SERVICE_UNAVAILABLE
                )
                return

            response_text = self._call_openai(messages, memory_items)
            self._send_json({"reply": response_text, "mode": "ai"})
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            self._send_json(
                {"error": "OpenAI request failed.", "detail": detail},
                HTTPStatus.BAD_GATEWAY
            )
        except error.URLError as exc:
            self._send_json(
                {"error": "Unable to reach OpenAI.", "detail": str(exc.reason)},
                HTTPStatus.BAD_GATEWAY
            )
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON request body."}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json(
                {"error": "Unexpected server error.", "detail": str(exc)},
                HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def log_message(self, fmt, *args):
        return

    def _call_openai(self, messages, memory_items) -> str:
        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        memory_prompt = build_memory_prompt(memory_items)

        prompt_inputs = [
            {"role": "developer", "content": build_system_prompt()}
        ]
        if memory_prompt:
            prompt_inputs.append({"role": "developer", "content": memory_prompt})

        request_body = {
            "model": model,
            "input": [
                *prompt_inputs,
                *messages
            ],
            "max_output_tokens": 360
        }

        if os.getenv("OPENAI_USER_ID"):
            request_body["safety_identifier"] = os.getenv("OPENAI_USER_ID")

        raw_request = json.dumps(request_body).encode("utf-8")
        api_request = request.Request(
            OPENAI_URL,
            data=raw_request,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with request.urlopen(api_request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))

        text = extract_output_text(payload)
        if not text:
            raise RuntimeError("OpenAI returned no assistant text.")

        return text


def main() -> None:
    load_env_file(ENV_FILE)
    port = int(os.getenv("PORT", "3000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), MoriiHandler)
    print(f"Morii server is running at http://localhost:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
