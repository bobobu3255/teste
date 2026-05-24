"""
Assistente de IA local para Ollama e llama.cpp.
Interface em estilo chat, sem travar a UI.
"""
import html
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import date, datetime
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMenu, QMessageBox, QPushButton, QTextEdit,
    QVBoxLayout, QWidget, QInputDialog,
)

from cloud_service import CloudService, load_cloud_settings, save_cloud_settings
from app.core.paths import BASE_DIR, CONFIG_DIR
from app.features.ai_assistant.styles import (
    ai_widget_qss, chat_body_open, chat_output_qss, frame_qss, image_style,
    label_qss as ai_label_qss, menu_qss, message_style, pill_qss, prompt_input_qss,
)
AI_SETTINGS_FILE = CONFIG_DIR / "ai_settings.json"
AI_CHATS_DIR = CONFIG_DIR / "ai_chats"
AI_MEMORY_FILE = CONFIG_DIR / "ai_memory.txt"
OPENCODE_ZEN_URL = "https://opencode.ai/zen"
OPENCODE_ZEN_MODEL = "minimax-m2.5-free"
OPENCODE_RUN_MODEL = "opencode/minimax-m2.5-free"
OPENCODE_ZEN_API_KEY = "opencode-api-key"
TEXT_EXTENSIONS = {
    ".txt", ".md", ".html", ".htm", ".css", ".js", ".json", ".csv", ".xml",
    ".py", ".bat", ".ps1", ".log", ".ini", ".toml", ".yaml", ".yml",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


CURRENT_DATE = date.today().strftime("%d/%m/%Y")

DEFAULT_SYSTEM_PROMPT = (
    "Voce e um assistente local dentro de um app PyQt chamado Telegram Collector Pro. "
    f"Data atual do sistema: {CURRENT_DATE}. "
    "Responda em portugues do Brasil, direto e pratico. Nao faca saudacoes longas repetidas. "
    "Nao mencione data, presidente, memoria ou fatos do sistema a menos que o usuario pergunte. "
    "Ajude a corrigir erros, "
    "organizar dados, explicar logs e sugerir proximas acoes seguras. "
    "Voce e uma IA local/offline: se perguntarem algo que pode ter mudado recentemente, "
    "avise que pode precisar de verificacao na internet. "
    "Se o usuario pedir para criar site, html, css, js, python, json ou arquivos, entregue blocos de codigo "
    "com cercas markdown e linguagem, por exemplo ```html, ```css e ```js. "
    "Nao diga que criou arquivo fisico; o aplicativo salva os arquivos quando houver blocos de codigo. "
    "Nao invente acesso a arquivos que nao foram enviados no prompt."
)

AI_CHAT_PRESETS = {
    "Geral": (
        "Modo Geral: responda de forma direta, prática e curta. "
        "Se faltar contexto, diga o que precisa ser testado."
    ),
    "Código": (
        "Modo Código: aja como assistente de programação. Priorize passos seguros, "
        "explique erros por causa provável e entregue código organizado quando pedido."
    ),
    "Português": (
        "Modo Português: corrija frases mantendo o sentido do usuário. "
        "Quando útil, entregue uma versão natural, uma formal e uma curta."
    ),
    "Logs": (
        "Modo Logs: leia mensagens de erro, encontre causa provável, risco e próximo teste. "
        "Evite enrolação e destaque a primeira coisa a corrigir."
    ),
    "Arquivos": (
        "Modo Arquivos: quando o usuário pedir site, texto, código ou documento, "
        "entregue blocos de código completos com linguagem para o app criar arquivos."
    ),
}


class LocalAIError(Exception):
    pass


def _downloads_dir():
    path = Path.home() / "Downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_output_dir(folder_name):
    for base in (_downloads_dir(), BASE_DIR / "IA_Saidas"):
        try:
            path = base / folder_name
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception:
            continue
    path = BASE_DIR / "IA_Saidas"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_output_file(filename):
    for base in (_downloads_dir(), BASE_DIR / "IA_Saidas"):
        try:
            base.mkdir(parents=True, exist_ok=True)
            path = base / filename
            path.write_text("", encoding="utf-8")
            return path
        except Exception:
            continue
    path = BASE_DIR / "IA_Saidas" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(name, fallback="arquivo"):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name).strip().strip(".")
    return cleaned or fallback


def _model_supports_images(model):
    low = (model or "").lower()
    return any(key in low for key in ("vision", "llava", "bakllava", "moondream", "minicpm-v", "qwen2.5vl", "qwen-vl"))


def _load_settings():
    defaults = {
        "provider": "Ollama",
        "ollama_url": "http://127.0.0.1:11434",
        "llamacpp_url": "http://127.0.0.1:8080",
        "openai_url": "http://127.0.0.1:1234",
        "opencode_zen_url": OPENCODE_ZEN_URL,
        "api_key": "",
        "ollama_path": "",
        "claude_path": "",
        "opencode_path": "",
        "model": "qwen2.5:1.5b",
        "chat_preset": "Geral",
    }
    try:
        if AI_SETTINGS_FILE.exists():
            with open(AI_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                defaults.update(data)
    except Exception:
        pass
    return defaults


def _save_settings(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(AI_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_memory():
    try:
        return AI_MEMORY_FILE.read_text(encoding="utf-8")
    except Exception:
        return ""


def _save_memory(text):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    AI_MEMORY_FILE.write_text(text.strip(), encoding="utf-8")


def _parse_http_error(exc):
    body = ""
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    if body:
        try:
            data = json.loads(body)
            return data.get("error") or data.get("message") or body
        except Exception:
            return body
    return str(exc)


def _json_request(url, payload=None, timeout=60, retries=0, api_key="", extra_headers=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            message = _parse_http_error(exc)
            if exc.code == 503 and attempt < retries:
                time.sleep(4)
                continue
            raise LocalAIError(f"HTTP {exc.code}: {message}")
        except urllib.error.URLError as exc:
            raise LocalAIError(f"Servidor local nao respondeu: {exc.reason or exc}")

    return {}


def _friendly_error(message):
    text = str(message)
    low = text.lower()
    if "permission requested" in low or "external_directory" in low:
        return (
            "O OpenCode tentou agir como agente de arquivos em vez de responder no chat. "
            "Reenvie a pergunta ou use o modo Ollama/Lite para conversa normal."
        )
    if "opencode executou" in low and "nao retornou texto" in low:
        return (
            "O OpenCode abriu, mas nao devolveu uma resposta de chat. "
            "Para conversa normal, use Ollama com qwen2.5:1.5b ou llama3.2:3b. "
            "Deixe Zen/OpenCode para tarefas de codigo e agente."
        )
    if "connection refused" in low or "actively refused" in low or "nao respondeu" in low:
        return (
            "O Ollama parece fechado. Clique em 'Iniciar Ollama' ou abra o Ollama no Windows, "
            "depois teste a conexao."
        )
    if "model" in low and ("not found" in low or "not installed" in low or "pull" in low):
        return "Esse modelo nao esta instalado. Clique em 'Baixar modelo' ou escolha um modelo listado."
    if "503" in low:
        if "memory" in low or "memoria" in low or "system memory" in low:
            return "O modelo ficou pesado para a maquina. Tente um modelo menor, como gemma3:1b ou qwen2.5:1.5b."
        return "O Ollama devolveu 503. Pode ser modelo carregando, ocupado ou pesado demais. Aguarde um pouco ou teste modelo menor."
    if "404" in low:
        return "Endpoint/modelo nao encontrado. Confira a URL, o motor selecionado e o nome do modelo."
    if "401" in low or "403" in low:
        return "A chave/API recusou a conexao. No preset do video, tente aplicar OpenCode Zen novamente."
    if "internal server error" in low and "opencode" in low:
        return "O OpenCode Zen respondeu erro interno. Aguarde e tente de novo, ou use o Claude Code configurado pelo botao do preset."
    return text


def _find_ollama_exe(saved_path=""):
    candidates = []
    if saved_path:
        candidates.append(saved_path)
    found = shutil.which("ollama")
    if found:
        candidates.append(found)
    local = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if local:
        candidates.append(str(Path(local) / "Programs" / "Ollama" / "ollama.exe"))
    if program_files:
        candidates.append(str(Path(program_files) / "Ollama" / "ollama.exe"))
    if program_files_x86:
        candidates.append(str(Path(program_files_x86) / "Ollama" / "ollama.exe"))
    for path in candidates:
        if path and Path(path).exists():
            return str(Path(path))
    return ""


def _find_cli_command(name, saved_path=""):
    candidates = []
    if saved_path:
        candidates.append(saved_path)
    found = shutil.which(name) or shutil.which(f"{name}.cmd") or shutil.which(f"{name}.exe")
    if found:
        candidates.append(found)
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(str(Path(appdata) / "npm" / f"{name}.cmd"))
        candidates.append(str(Path(appdata) / "npm" / name))
    for path in candidates:
        if not path:
            continue
        try:
            if Path(path).exists():
                return str(Path(path))
        except OSError:
            return str(path)
    return ""


def _strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text or "")




def _fix_mojibake(text):
    """Corrige respostas que chegam com UTF-8 interpretado como Windows-1252."""
    text = str(text or "")
    markers = ("Ã", "Â", "â", "ðŸ", "�")
    if not text or not any(marker in text for marker in markers):
        return text
    try:
        fixed = text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        score = lambda value: sum(value.count(marker) for marker in markers)
        if fixed.strip() and score(fixed) < score(text):
            return fixed
    except Exception:
        pass
    return text


def _opencode_chat_dir():
    local = os.environ.get("LOCALAPPDATA")
    if local:
        path = Path(local) / "Temp" / "opencode" / "telegram_collector_chat"
    else:
        path = CONFIG_DIR / "opencode_chat"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parse_opencode_json_output(text):
    chunks = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        part = event.get("part") if isinstance(event, dict) else None
        if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
            chunks.append(part["text"])
        elif event.get("type") == "text" and event.get("text"):
            chunks.append(event["text"])
    return "".join(chunks).strip()


class LocalAIClient:
    def __init__(self, provider, base_url, model, api_key=""):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.api_key = api_key.strip()

    def _url(self, path):
        if self.base_url.endswith("/v1") and path.startswith("/v1/"):
            return self.base_url + path[3:]
        return self.base_url + path

    def list_models(self):
        if self.provider == "OpenCode Zen":
            return [OPENCODE_ZEN_MODEL]
        if self.provider == "Ollama":
            data = _json_request(f"{self.base_url}/api/tags", timeout=10)
            return [item.get("name", "") for item in data.get("models", []) if item.get("name")]
        data = _json_request(self._url("/v1/models"), timeout=10, api_key=self.api_key)
        return [item.get("id", "") for item in data.get("data", []) if item.get("id")]

    def pull_model(self):
        if self.provider != "Ollama":
            raise LocalAIError("Download automatico esta disponivel apenas para Ollama.")
        if not self.model:
            raise LocalAIError("Informe o nome do modelo antes de baixar.")
        payload = {"name": self.model, "stream": False}
        data = _json_request(f"{self.base_url}/api/pull", payload, timeout=3600)
        return data.get("status") or f"Modelo {self.model} baixado ou atualizado."

    def generate(self, prompt, images=None):
        if not self.model:
            raise LocalAIError("Informe um modelo para conversar.")

        if self.provider == "Ollama":
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": DEFAULT_SYSTEM_PROMPT,
                "stream": False,
                "keep_alive": "10m",
                "options": {"temperature": 0.2},
            }
            if images:
                payload["images"] = images
            data = _json_request(f"{self.base_url}/api/generate", payload, timeout=180, retries=2)
            return data.get("response", "").strip()

        if images:
            raise LocalAIError("Imagens anexadas funcionam apenas com Ollama e modelo visual.")

        if self.provider == "OpenCode Zen":
            payload = {
                "model": self.model or OPENCODE_ZEN_MODEL,
                "max_tokens": 2048,
                "system": DEFAULT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            data = _json_request(
                self._url("/v1/messages"),
                payload,
                timeout=180,
                retries=1,
                extra_headers={
                    "x-api-key": self.api_key or OPENCODE_ZEN_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
            )
            chunks = []
            for item in data.get("content", []):
                if item.get("type") == "text" and item.get("text"):
                    chunks.append(item["text"])
            if chunks:
                return "\n".join(chunks).strip()
            return data.get("message") or data.get("completion") or ""

        payload = {
            "model": self.model or "local-model",
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "stream": False,
        }
        data = _json_request(self._url("/v1/chat/completions"), payload, timeout=180, retries=1, api_key=self.api_key)
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return ""


class AIWorker(QThread):
    finished = pyqtSignal(bool, str, str)

    def __init__(self, provider, base_url, model, prompt, mode="generate", api_key="", ollama_path="", images=None, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.base_url = base_url
        self.model = model
        self.prompt = prompt
        self.mode = mode
        self.api_key = api_key
        self.ollama_path = ollama_path
        self.images = images or []

    def _generate_with_opencode_zen(self):
        opencode_cmd = _find_cli_command("opencode")
        if not opencode_cmd:
            raise LocalAIError(
                "OpenCode nao encontrado. Instale com: npm install -g opencode-ai@latest"
            )

        env = os.environ.copy()
        env.update({
            "ANTHROPIC_BASE_URL": self.base_url.rstrip("/") or OPENCODE_ZEN_URL,
            "ANTHROPIC_MODEL": self.model or OPENCODE_ZEN_MODEL,
            "ANTHROPIC_API_KEY": self.api_key or OPENCODE_ZEN_API_KEY,
            "ENABLE_TOOL_SEARCH": "true",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "LANG": "pt_BR.UTF-8",
            "LC_ALL": "pt_BR.UTF-8",
        })
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        model = (self.model or OPENCODE_ZEN_MODEL).strip()
        run_model = model if "/" in model else f"opencode/{model}"
        work_dir = _opencode_chat_dir()
        chat_prompt = self._opencode_chat_prompt()
        cmd = [
            opencode_cmd,
            "run",
            "--pure",
            "-m",
            run_model,
            "--format",
            "json",
            chat_prompt,
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
            creationflags=flags,
        )
        output = _fix_mojibake(_strip_ansi(proc.stdout)).strip()
        error = _fix_mojibake(_strip_ansi(proc.stderr)).strip()
        if proc.returncode != 0:
            raise LocalAIError(error or output or f"OpenCode saiu com codigo {proc.returncode}")
        parsed = _parse_opencode_json_output(output)
        if parsed:
            return parsed

        combined = "\n".join(part for part in (output, error) if part).strip()
        clean_lines = [
            line.rstrip()
            for line in combined.splitlines()
            if line.strip()
            and not line.lstrip().startswith("> build")
            and not line.lstrip().startswith("{\"type\":")
            and "permission requested:" not in line.lower()
            and "auto-rejecting" not in line.lower()
        ]
        if clean_lines:
            return "\n".join(clean_lines).strip()

        fallback = self._generate_with_opencode_plain(opencode_cmd, run_model, env, flags, work_dir)
        if fallback:
            return fallback
        raise LocalAIError("OpenCode executou, mas nao retornou texto. Tente reenviar ou trocar o modelo Zen.")

    def _opencode_chat_prompt(self):
        marker = "Contexto completo do ultimo pedido:"
        current_request = self.prompt.split(marker, 1)[1].strip() if marker in self.prompt else self.prompt.strip()
        prompt = (
            "Responda diretamente a pergunta ou pedido do usuario em portugues do Brasil. "
            "Nao responda apenas que esta pronto. "
            "Nao tente usar ferramentas, pastas ou permissoes. "
            "Se o usuario pedir arquivo/codigo, responda com blocos markdown.\n\n"
            f"Pergunta do usuario:\n{current_request}\n\nResposta:"
        )
        return re.sub(r"\s+", " ", prompt).strip()

    def _generate_with_opencode_plain(self, opencode_cmd, run_model, env, flags, work_dir):
        cmd = [opencode_cmd, "run", "--pure", "-m", run_model, self._opencode_chat_prompt()]
        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
            creationflags=flags,
        )
        combined = _fix_mojibake(_strip_ansi((proc.stdout or "") + "\n" + (proc.stderr or ""))).strip()
        if proc.returncode != 0:
            return ""
        lines = [
            line.rstrip()
            for line in combined.splitlines()
            if line.strip()
            and not line.lstrip().startswith("> build")
            and "permission requested:" not in line.lower()
            and "auto-rejecting" not in line.lower()
        ]
        return "\n".join(lines).strip()

    def run(self):
        try:
            if self.mode == "start":
                ollama_exe = _find_ollama_exe(self.ollama_path)
                if not ollama_exe:
                    raise LocalAIError(
                        "Ollama nao encontrado no PC. Instale pelo botao 'Instalar Ollama' "
                        "ou selecione o caminho do ollama.exe."
                    )
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen([ollama_exe, "serve"], creationflags=flags)
                time.sleep(2)
                self.finished.emit(True, "Ollama iniciado. Clique em Conectar para listar modelos.", self.mode)
                return

            if self.provider == "OpenCode Zen" and self.mode == "generate":
                direct_error = ""
                try:
                    client = LocalAIClient(self.provider, self.base_url, self.model, self.api_key)
                    answer = _fix_mojibake(client.generate(self.prompt)).strip()
                    if answer:
                        self.finished.emit(True, answer, self.mode)
                        return
                except Exception as exc:
                    direct_error = str(exc)

                try:
                    answer = self._generate_with_opencode_zen()
                    self.finished.emit(True, answer, self.mode)
                    return
                except Exception as exc:
                    if direct_error:
                        raise LocalAIError(
                            f"OpenCode Zen via API falhou: {direct_error}\n"
                            f"OpenCode CLI falhou: {exc}"
                        )
                    raise

            client = LocalAIClient(self.provider, self.base_url, self.model, self.api_key)
            if self.mode == "models":
                models = client.list_models()
                self.finished.emit(True, "\n".join(models) if models else "Nenhum modelo encontrado.", self.mode)
            elif self.mode == "pull":
                result = client.pull_model()
                self.finished.emit(True, result, self.mode)
            else:
                answer = client.generate(self.prompt, self.images)
                self.finished.emit(True, answer or "A IA respondeu vazio.", self.mode)
        except Exception as exc:
            self.finished.emit(False, str(exc), self.mode)


class CloudTaskWorker(QThread):
    finished = pyqtSignal(str, bool, object, str)

    def __init__(self, task, settings, parent=None):
        super().__init__(parent)
        self.task = task
        self.settings = settings

    def run(self):
        try:
            service = CloudService(self.settings)
            if self.task == "diagnose":
                self.finished.emit(self.task, True, service.diagnose(), "")
                return
            if self.task == "sync":
                payload = {
                    "models": service.get_ai_models(),
                    "prompts": service.get_prompts(),
                }
                self.finished.emit(self.task, True, payload, "")
                return
            raise RuntimeError("Tarefa de nuvem desconhecida.")
        except Exception as exc:
            self.finished.emit(self.task, False, None, str(exc))


class ImageGenerationWorker(QThread):
    finished = pyqtSignal(bool, str, str)

    def __init__(self, prompt, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self):
        try:
            url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
            payload = {
                "prompt": self.prompt,
                "steps": 6,
                "width": 512,
                "height": 512,
                "cfg_scale": 1.5,
                "sampler_name": "Euler a",
            }
            data = _json_request(url, payload, timeout=240)
            images = data.get("images") or []
            if not images:
                raise LocalAIError("Servidor respondeu sem imagem.")
            raw = base64.b64decode(images[0].split(",", 1)[-1])
            out_dir = _safe_output_dir("ia_imagens")
            path = out_dir / f"imagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path.write_bytes(raw)
            self.finished.emit(True, str(path), "")
        except Exception as exc:
            self.finished.emit(False, "", str(exc))


class ChatInput(QTextEdit):
    submitted = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            event.accept()
            self.submitted.emit()
            return
        super().keyPressEvent(event)


class AIAssistantWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = _load_settings()
        self._worker = None
        self._cloud_worker = None
        self._image_worker = None
        self.messages = []
        self.pending_attachments = []
        self.pending_images = []
        self.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._auto_create_files_after_response = False
        self._build()
        self._refresh_chat_list()
        self._append_message(
            "assistant",
            "Pronto. Escreva sua mensagem ou use o botao + para anexar arquivos, criar arquivos e gerar imagens.",
            render=False,
        )
        self._render_chat()

    def _build(self):
        self._build_minimal_ui()
        return

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("IA Local")
        title.setStyleSheet("color:#f8fafc;font-size:22px;font-weight:900;background:transparent;border:none;")
        subtitle = QLabel("Chat local com Ollama. Recomendado: Qwen 2.5 leve ou Llama 3.2 3B.")
        subtitle.setStyleSheet("color:#94a3b8;font-size:12px;background:transparent;border:none;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.status_label = QLabel("Offline")
        self.status_label.setStyleSheet(pill_qss("#f59e0b"))
        header.addWidget(self.status_label)
        root.addLayout(header)

        settings_frame = QFrame()
        settings_frame.setStyleSheet(
            "QFrame{background:#0b1626;border:1px solid rgba(34,211,238,0.18);border-radius:14px;}"
        )
        settings_lay = QVBoxLayout(settings_frame)
        settings_lay.setContentsMargins(12, 10, 12, 10)
        settings_lay.setSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(self._small_label("Motor"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Ollama", "llama.cpp", "OpenAI Compatível"])
        self.provider_combo.setCurrentText(self.settings.get("provider", "Ollama"))
        self.provider_combo.currentTextChanged.connect(self._provider_changed)
        row1.addWidget(self.provider_combo)
        row1.addWidget(self._small_label("Modelo"))
        self.model_input = QLineEdit(self.settings.get("model", "qwen2.5:1.5b"))
        self.model_input.setPlaceholderText("qwen2.5:1.5b")
        row1.addWidget(self.model_input, 1)
        row1.addWidget(self._small_label("Preset"))
        self.model_preset = QComboBox()
        self.model_preset.addItems([
            "qwen2.5:1.5b",
            "qwen2.5:3b",
            "qwen2.5:7b",
            "qwen2.5:14b",
            "llama3.2:3b",
            "qwen3:8b",
            "qwen3:14b",
            "llava:7b",
            "llama3.2-vision:11b",
            "qwen3:1.7b",
            "qwen3:4b",
        ])
        self.model_preset.setToolTip("Escolha um modelo e clique em Baixar modelo se ele ainda nao existir.")
        self.model_preset.currentTextChanged.connect(self.model_input.setText)
        row1.addWidget(self.model_preset)
        connect_btn = QPushButton("Conectar")
        connect_btn.clicked.connect(self.test_connection)
        row1.addWidget(connect_btn)
        root_start_btn = QPushButton("Iniciar Ollama")
        root_start_btn.clicked.connect(self.start_ollama)
        row1.addWidget(root_start_btn)
        install_btn = QPushButton("Instalar Ollama")
        install_btn.clicked.connect(lambda: webbrowser.open("https://ollama.com/download/windows"))
        row1.addWidget(install_btn)
        settings_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self._small_label("URL"))
        self.url_input = QLineEdit(self._current_url())
        row2.addWidget(self.url_input, 1)
        pull_btn = QPushButton("Baixar modelo")
        pull_btn.clicked.connect(self.pull_model)
        row2.addWidget(pull_btn)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.save_settings)
        row2.addWidget(save_btn)
        settings_lay.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(self._small_label("Chave API"))
        self.api_key_input = QLineEdit(self.settings.get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Opcional para servidor OpenAI-compatible")
        row3.addWidget(self.api_key_input, 1)
        row3.addWidget(self._small_label("Ollama.exe"))
        self.ollama_path_input = QLineEdit(self.settings.get("ollama_path", ""))
        self.ollama_path_input.setPlaceholderText("Opcional")
        row3.addWidget(self.ollama_path_input, 1)
        find_btn = QPushButton("Localizar")
        find_btn.clicked.connect(self.find_ollama_path)
        row3.addWidget(find_btn)
        settings_lay.addLayout(row3)

        hint = QLabel("Dica: para pendrive/PC simples, comece por qwen2.5:1.5b. Depois teste llama3.2:3b se a maquina aguentar.")
        hint.setStyleSheet("color:#7dd3fc;font-size:11px;background:rgba(34,211,238,0.06);border-radius:8px;padding:7px 9px;")
        settings_lay.addWidget(hint)
        root.addWidget(settings_frame)

        self.model_list = QListWidget()
        self.model_list.setMaximumHeight(72)
        self.model_list.setToolTip("Modelos encontrados no servidor local")
        self.model_list.itemDoubleClicked.connect(lambda item: self.model_input.setText(item.text()))
        root.addWidget(self.model_list)

        chat_row = QHBoxLayout()
        chat_row.addWidget(self._small_label("Chats"))
        self.chat_combo = QComboBox()
        self.chat_combo.setToolTip("Conversas salvas localmente no projeto")
        chat_row.addWidget(self.chat_combo, 1)
        new_chat_btn = QPushButton("Novo chat")
        new_chat_btn.clicked.connect(self.new_chat)
        chat_row.addWidget(new_chat_btn)
        save_chat_btn = QPushButton("Salvar chat")
        save_chat_btn.clicked.connect(self.save_current_chat)
        chat_row.addWidget(save_chat_btn)
        open_chat_btn = QPushButton("Abrir chat")
        open_chat_btn.clicked.connect(self.open_selected_chat)
        chat_row.addWidget(open_chat_btn)
        memory_btn = QPushButton("Memoria")
        memory_btn.clicked.connect(self.edit_memory)
        chat_row.addWidget(memory_btn)
        root.addLayout(chat_row)

        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        self.chat_output.setStyleSheet(
            "QTextEdit{background:#05070d;border:1px solid rgba(34,211,238,0.14);"
            "border-radius:16px;color:#e5e7eb;padding:12px;font-size:13px;}"
            "QScrollBar:vertical{background:#07111f;width:10px;border-radius:5px;}"
            "QScrollBar::handle:vertical{background:#164e63;border-radius:5px;}"
        )
        root.addWidget(self.chat_output, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet(
            "QFrame{background:#0b1626;border:1px solid rgba(34,211,238,0.22);border-radius:16px;}"
        )
        input_lay = QVBoxLayout(input_frame)
        input_lay.setContentsMargins(10, 8, 10, 8)
        self.prompt_input = ChatInput()
        self.prompt_input.setPlaceholderText("Mensagem para a IA local... Enter envia, Shift+Enter pula linha")
        self.prompt_input.setMinimumHeight(74)
        self.prompt_input.setMaximumHeight(110)
        self.prompt_input.submitted.connect(self.ask_ai)
        self.prompt_input.setStyleSheet(
            "QTextEdit{background:#08111f;border:1px solid rgba(148,163,184,0.10);"
            "border-radius:12px;color:#f8fafc;padding:9px;font-size:13px;}"
            "QTextEdit:focus{border-color:rgba(34,211,238,0.45);}"
        )
        input_lay.addWidget(self.prompt_input)

        actions = QHBoxLayout()
        logs_btn = QPushButton("Analisar logs")
        logs_btn.clicked.connect(self.analyze_logs)
        actions.addWidget(logs_btn)
        attach_btn = QPushButton("Anexar")
        attach_btn.clicked.connect(self.attach_files)
        actions.addWidget(attach_btn)
        save_response_btn = QPushButton("Salvar resposta")
        save_response_btn.clicked.connect(self.save_last_response)
        actions.addWidget(save_response_btn)
        create_files_btn = QPushButton("Criar arquivos")
        create_files_btn.clicked.connect(self.create_files_from_last_response)
        actions.addWidget(create_files_btn)
        image_btn = QPushButton("Gerar imagem")
        image_btn.clicked.connect(self.generate_image_from_prompt)
        actions.addWidget(image_btn)
        clear_btn = QPushButton("Limpar chat")
        clear_btn.clicked.connect(self.clear_chat)
        actions.addWidget(clear_btn)
        self.attachments_label = QLabel("0 anexos")
        self.attachments_label.setStyleSheet(ai_label_qss("attachments"))
        actions.addWidget(self.attachments_label)
        actions.addStretch()
        self.ask_btn = QPushButton("Enviar  â†µ")
        self.ask_btn.setFixedWidth(150)
        self.ask_btn.clicked.connect(self.ask_ai)
        actions.addWidget(self.ask_btn)
        input_lay.addLayout(actions)
        root.addWidget(input_frame)

        self._provider_changed(self.provider_combo.currentText())

    def _build_minimal_ui(self):
        self.setStyleSheet(ai_widget_qss())
        self._build_hidden_controls()

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 16, 22, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("IA Local")
        title.setStyleSheet(ai_label_qss("title"))
        subtitle = QLabel("Conversa local")
        subtitle.setStyleSheet(ai_label_qss("subtitle"))
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.preset_switch = QComboBox()
        self.preset_switch.addItems(list(AI_CHAT_PRESETS.keys()))
        self.preset_switch.setCurrentText(self.settings.get("chat_preset", "Geral"))
        self.preset_switch.setFixedWidth(132)
        self.preset_switch.setToolTip("Muda o jeito da IA responder sem trocar o modelo.")
        self.preset_switch.currentTextChanged.connect(self._chat_preset_changed)
        header.addWidget(self.preset_switch)

        self.model_switch = QComboBox()
        self.model_switch.addItems(["Lite", "Pro", "Max", "Vision", "Zen"])
        self.model_switch.setFixedWidth(138)
        self.model_switch.setToolTip("Troca rapida de modelo. Zen usa o preset OpenCode Zen do video.")
        self.model_switch.currentTextChanged.connect(self._model_mode_changed)
        header.addWidget(self.model_switch)

        self.chat_menu_btn = QPushButton("Chats")
        self.chat_menu_btn.setFixedWidth(72)
        self.chat_menu_btn.setToolTip("Abrir, salvar ou apagar conversas salvas")
        self.chat_menu_btn.clicked.connect(self._open_chat_menu)
        header.addWidget(self.chat_menu_btn)

        new_chat_btn = QPushButton("+ Chat")
        new_chat_btn.setFixedWidth(74)
        new_chat_btn.clicked.connect(self.new_chat)
        header.addWidget(new_chat_btn)

        self.settings_btn = QPushButton("Config")
        self.settings_btn.setFixedWidth(82)
        self.settings_btn.setToolTip("Abrir configuracoes tecnicas da IA")
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        header.addWidget(self.settings_btn)

        self.status_label = QLabel("Offline")
        self.status_label.setStyleSheet(self._pill_qss("#f59e0b"))
        header.addWidget(self.status_label)
        root.addLayout(header)

        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        self.chat_output.setFrameShape(QFrame.NoFrame)
        self.chat_output.setStyleSheet(chat_output_qss(minimal=True))
        root.addWidget(self.chat_output, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet(frame_qss("input"))
        input_lay = QVBoxLayout(input_frame)
        input_lay.setContentsMargins(12, 10, 12, 10)
        input_lay.setSpacing(7)

        self.prompt_input = ChatInput()
        self.prompt_input.setPlaceholderText("Mensagem para a IA local... Enter envia, Shift+Enter pula linha")
        self.prompt_input.setMinimumHeight(74)
        self.prompt_input.setMaximumHeight(120)
        self.prompt_input.submitted.connect(self.ask_ai)
        self.prompt_input.setStyleSheet(prompt_input_qss(minimal=True))
        input_lay.addWidget(self.prompt_input)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.tools_btn = QPushButton("+")
        self.tools_btn.setFixedSize(34, 30)
        self.tools_btn.setToolTip("Acoes: anexar, criar arquivos, imagem, logs e limpar")
        self.tools_btn.clicked.connect(self._open_tools_menu)
        footer.addWidget(self.tools_btn)

        self.attachments_label = QLabel("")
        self.attachments_label.setStyleSheet("color:#94a3b8;font-size:11px;background:transparent;border:none;")
        footer.addWidget(self.attachments_label)
        footer.addStretch()

        self.ask_btn = QPushButton("Enviar")
        self.ask_btn.setFixedWidth(112)
        self.ask_btn.clicked.connect(self.ask_ai)
        footer.addWidget(self.ask_btn)
        input_lay.addLayout(footer)
        root.addWidget(input_frame)

        self._provider_changed(self.provider_combo.currentText())
        self._sync_model_mode()

    def _build_hidden_controls(self):
        self.provider_combo = QComboBox(self)
        self.provider_combo.addItems(["Ollama", "llama.cpp", "OpenAI Compatível", "OpenCode Zen"])
        self.provider_combo.setCurrentText(self.settings.get("provider", "Ollama"))
        self.provider_combo.currentTextChanged.connect(self._provider_changed)

        self.model_input = QLineEdit(self.settings.get("model", "qwen2.5:1.5b"), self)
        self.model_input.setPlaceholderText("qwen2.5:1.5b")

        self.model_preset = QComboBox(self)
        self.model_preset.addItems([
            "qwen2.5:1.5b",
            "qwen2.5:3b",
            "qwen2.5:7b",
            "qwen2.5:14b",
            "llama3.2:3b",
            "qwen3:8b",
            "qwen3:14b",
            "llava:7b",
            "llama3.2-vision:11b",
            "qwen3:1.7b",
            "qwen3:4b",
            OPENCODE_ZEN_MODEL,
        ])
        self.model_preset.currentTextChanged.connect(self.model_input.setText)

        self.url_input = QLineEdit(self._current_url(), self)
        self.api_key_input = QLineEdit(self.settings.get("api_key", ""), self)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.ollama_path_input = QLineEdit(self.settings.get("ollama_path", ""), self)

        self.model_list = QListWidget(self)
        self.model_list.itemDoubleClicked.connect(lambda item: self.model_input.setText(item.text()))

        self.chat_combo = QComboBox(self)
        self.chat_combo.setToolTip("Conversas salvas localmente no projeto")

        for widget in (
            self.provider_combo,
            self.model_input,
            self.model_preset,
            self.url_input,
            self.api_key_input,
            self.ollama_path_input,
            self.model_list,
            self.chat_combo,
        ):
            widget.setVisible(False)

    def _small_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(ai_label_qss("small"))
        return label

    def _pill_qss(self, color):
        return pill_qss(color)

    def _chat_preset_changed(self, preset):
        data = _load_settings()
        data["chat_preset"] = preset if preset in AI_CHAT_PRESETS else "Geral"
        _save_settings(data)
        self.settings = data
        self._set_status(f"Modo {data['chat_preset']}", "#38bdf8")

    def _model_mode_changed(self, mode):
        mapping = {
            "Lite": "qwen2.5:1.5b",
            "Pro": "llama3.2:3b",
            "Max": "qwen3:8b",
            "Vision": "llava:7b",
            "Zen": OPENCODE_ZEN_MODEL,
        }
        if mode == "Zen":
            self.apply_opencode_zen_preset(show_message=False)
            self._set_status("OpenCode Zen", "#38bdf8")
            return
        if self.provider_combo.currentText() == "OpenCode Zen":
            self.provider_combo.setCurrentText("Ollama")
        model = mapping.get(mode)
        if model:
            self.model_input.setText(model)
            self.save_settings()
            self._set_status(f"Modelo {mode}", "#38bdf8")

    def _sync_model_mode(self):
        if not hasattr(self, "model_switch"):
            return
        model = (self.model_input.text() or "").lower()
        if self.provider_combo.currentText() == "OpenCode Zen" or "minimax-m2.5" in model:
            mode = "Zen"
        elif "llava" in model or "vision" in model or "vl" in model:
            mode = "Vision"
        elif "qwen3" in model or "14b" in model or "32b" in model:
            mode = "Max"
        elif "llama3.2" in model or "3b" in model or "7b" in model:
            mode = "Pro"
        else:
            mode = "Lite"
        self.model_switch.blockSignals(True)
        self.model_switch.setCurrentText(mode)
        self.model_switch.blockSignals(False)

    def _open_chat_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(menu_qss())
        menu.addAction("Abrir chat salvo", self.open_chat_picker)
        menu.addAction("Salvar chat atual", self.save_current_chat)
        menu.addAction("Apagar chat salvo", self.delete_chat_picker)
        menu.addSeparator()
        menu.addAction("Novo chat", self.new_chat)
        menu.exec_(self.chat_menu_btn.mapToGlobal(self.chat_menu_btn.rect().bottomLeft()))

    def _open_tools_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(menu_qss())
        menu.addAction("Anexar arquivo/imagem", self.attach_files)
        menu.addAction("Criar arquivos da ultima resposta", lambda: self.create_files_from_last_response(True))
        menu.addAction("Salvar ultima resposta", self.save_last_response)
        menu.addAction("Gerar imagem pelo prompt", self.generate_image_from_prompt)
        menu.addSeparator()
        menu.addAction("Usar OpenCode Zen do video", self.apply_opencode_zen_preset)
        menu.addAction("Configurar Claude Code gratis", self.configure_claude_code_zen)
        menu.addAction("Abrir Claude Code", self.open_claude_code)
        menu.addAction("Abrir OpenCode", self.open_opencode)
        menu.addSeparator()
        menu.addAction("Diagnosticar bobobu/cPanel", self.cloud_diagnostics)
        menu.addAction("Sincronizar catalogo IA do site", self.sync_cloud_catalog)
        menu.addSeparator()
        menu.addAction("Novo chat", self.new_chat)
        menu.addAction("Abrir chat salvo", self.open_chat_picker)
        menu.addAction("Apagar chat salvo", self.delete_chat_picker)
        menu.addAction("Salvar chat atual", self.save_current_chat)
        menu.addAction("Memoria da IA", self.edit_memory)
        menu.addSeparator()
        menu.addAction("Analisar logs", self.analyze_logs)
        menu.addAction("Limpar chat", self.clear_chat)
        menu.exec_(self.tools_btn.mapToGlobal(self.tools_btn.rect().bottomLeft()))

    def apply_opencode_zen_preset(self, show_message=True):
        """Aplica o preset mostrado no video: OpenCode Zen + Minimax M2.5."""
        self.provider_combo.setCurrentText("OpenCode Zen")
        self.url_input.setText(OPENCODE_ZEN_URL)
        self.model_input.setText(OPENCODE_ZEN_MODEL)
        if not self.api_key_input.text().strip():
            self.api_key_input.setText(OPENCODE_ZEN_API_KEY)
        self.save_settings()
        self._sync_model_mode()
        if show_message:
            self._append_message(
                "system",
                "Preset OpenCode Zen aplicado.\n"
                f"URL: {OPENCODE_ZEN_URL}\n"
                f"Modelo: {OPENCODE_ZEN_MODEL}\n\n"
                "Isso e o caminho do video para usar uma alternativa ao Claude Code/Ollama.",
                render=True,
            )

    def _ensure_cloud_defaults(self):
        settings = load_cloud_settings()
        if not settings.get("base_url"):
            settings["base_url"] = "https://bobobu.com.br/v11"
        save_cloud_settings(settings)
        return settings

    def cloud_diagnostics(self):
        settings = self._ensure_cloud_defaults()
        self._run_cloud_worker("diagnose", settings, "Consultando bobobu/cPanel...")

    def _render_cloud_diagnostics(self, result):
        lines = [
            "Diagnostico bobobu/cPanel",
            "",
            f"URL: {result.get('base_url')}",
            f"Ativo no app: {'sim' if result.get('enabled') else 'nao'}",
            f"version.json: {'OK' if result.get('version_ok') else 'falhou'}",
            f"ai_models.json: {'OK' if result.get('models_ok') else 'falhou'}",
            f"prompts.json: {'OK' if result.get('prompts_ok') else 'falhou'}",
        ]
        errors = result.get("errors") or []
        if errors:
            lines.append("")
            lines.append("Erros:")
            lines.extend(f"- {item}" for item in errors)
        self._append_message("system", "\n".join(lines), render=True)

    def sync_cloud_catalog(self):
        settings = self._ensure_cloud_defaults()
        self._run_cloud_worker("sync", settings, "Sincronizando catalogo do site...")

    def _run_cloud_worker(self, task, settings, message):
        if self._cloud_worker and self._cloud_worker.isRunning():
            self._append_message("system", "Ja existe uma consulta do site em andamento.", render=True)
            return
        self._append_message("system", message, render=True)
        self._cloud_worker = CloudTaskWorker(task, settings, self)
        self._cloud_worker.finished.connect(self._cloud_worker_done)
        self._cloud_worker.start()

    def _cloud_worker_done(self, task, ok, payload, error):
        if not ok:
            self._append_message(
                "system",
                "Nao consegui falar com o site agora.\n\n"
                f"Detalhes: {error}\n\n"
                "A interface continuou funcionando; tente novamente quando a conexao estiver ok.",
                render=True,
            )
            return
        if task == "diagnose":
            self._render_cloud_diagnostics(payload or {})
            return
        if task != "sync":
            return

        data = payload or {}
        models = data.get("models") or []
        prompts = data.get("prompts") or {}
        self.model_list.clear()
        for item in models:
            name = item.get("name")
            if name:
                label = item.get("label") or item.get("provider") or ""
                offline = "offline" if item.get("offline") else "online"
                self.model_list.addItem(f"{name}  [{label} / {offline}]")

        prompt_version = prompts.get("version", "sem versao") if isinstance(prompts, dict) else "sem versao"
        self._append_message(
            "system",
            "Catalogo IA sincronizado do seu dominio.\n\n"
            f"Modelos encontrados: {len(models)}\n"
            f"Prompts: {prompt_version}\n\n"
            "Isso nao troca seu modelo sozinho; serve como guia online para instalar/escolher modelos.",
            render=True,
        )

    def configure_claude_code_zen(self):
        """Cria/atualiza ~/.claude/settings.json com o preset do video."""
        config_dir = Path.home() / ".claude"
        config_dir.mkdir(parents=True, exist_ok=True)
        settings_path = config_dir / "settings.json"
        data = {}
        if settings_path.exists():
            try:
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                backup = settings_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                try:
                    settings_path.replace(backup)
                except Exception:
                    pass
                data = {}

        env = data.get("env")
        if not isinstance(env, dict):
            env = {}
        api_key = (
            self.api_key_input.text().strip()
            or self.settings.get("api_key", "").strip()
            or OPENCODE_ZEN_API_KEY
        )
        env.update({
            "ANTHROPIC_BASE_URL": OPENCODE_ZEN_URL,
            "ANTHROPIC_MODEL": OPENCODE_ZEN_MODEL,
            "ANTHROPIC_API_KEY": api_key,
            "ENABLE_TOOL_SEARCH": "true",
        })
        data["env"] = env
        settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._append_message(
            "system",
            "Claude Code configurado com OpenCode Zen.\n\n"
            f"Arquivo:\n{settings_path}\n\n"
            "Agora voce pode abrir o Claude Code pelo menu + > Abrir Claude Code.",
            render=True,
        )
        self._set_status("Claude configurado", "#10b981")

    def _open_cli_in_terminal(self, command_name, saved_key):
        settings = _load_settings()
        cmd = _find_cli_command(command_name, settings.get(saved_key, ""))
        if not cmd:
            QMessageBox.warning(
                self,
                "IA Local",
                f"Nao encontrei {command_name}. Instale ou reinicie o terminal para atualizar o PATH.",
            )
            return
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        if sys.platform == "win32":
            subprocess.Popen(["cmd.exe", "/k", cmd], cwd=str(BASE_DIR), creationflags=flags)
        else:
            subprocess.Popen([cmd], cwd=str(BASE_DIR))
        self._set_status(f"{command_name} aberto", "#38bdf8")

    def open_claude_code(self):
        self._open_cli_in_terminal("claude", "claude_path")

    def open_opencode(self):
        self._open_cli_in_terminal("opencode", "opencode_path")

    def open_chat_picker(self):
        self._refresh_chat_list()
        if self.chat_combo.count() <= 0:
            QMessageBox.information(self, "IA Local", "Ainda nao ha chats salvos.")
            return
        titles = [self.chat_combo.itemText(i) for i in range(self.chat_combo.count())]
        title, ok = QInputDialog.getItem(self, "Abrir chat", "Escolha uma conversa:", titles, 0, False)
        if not ok or not title:
            return
        index = titles.index(title)
        self.chat_combo.setCurrentIndex(index)
        self.open_selected_chat()

    def delete_chat_picker(self):
        self._refresh_chat_list()
        if self.chat_combo.count() <= 0:
            QMessageBox.information(self, "IA Local", "Ainda nao ha chats salvos para apagar.")
            return
        titles = [self.chat_combo.itemText(i) for i in range(self.chat_combo.count())]
        title, ok = QInputDialog.getItem(self, "Apagar chat", "Escolha a conversa para apagar:", titles, 0, False)
        if not ok or not title:
            return
        index = titles.index(title)
        chat_id = self.chat_combo.itemData(index)
        if not chat_id:
            return
        answer = QMessageBox.question(
            self,
            "Apagar chat",
            f"Apagar a conversa salva?\n\n{title}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        path = AI_CHATS_DIR / f"{chat_id}.json"
        try:
            if path.exists():
                path.unlink()
            if chat_id == self.current_chat_id:
                self.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.messages = []
                self._append_message("assistant", "Chat apagado. Comecei uma conversa nova.", render=False)
                self._render_chat()
            self._refresh_chat_list()
            self._set_status("Chat apagado", "#10b981")
        except Exception as exc:
            QMessageBox.warning(self, "IA Local", f"Nao consegui apagar esse chat:\n{exc}")

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuracoes da IA")
        dialog.setMinimumWidth(720)
        dialog.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel("Configuracoes da IA Local")
        title.setStyleSheet(ai_label_qss("dialog_title"))
        desc = QLabel("Use esta tela quando precisar trocar motor, URL, modelo, instalar Ollama ou baixar modelos.")
        desc.setStyleSheet(ai_label_qss("dialog_desc"))
        layout.addWidget(title)
        layout.addWidget(desc)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        provider = QComboBox()
        provider.addItems(["Ollama", "llama.cpp", "OpenAI Compatível", "OpenCode Zen"])
        provider.setCurrentText(self.provider_combo.currentText())
        form.addRow("Motor:", provider)

        preset = QComboBox()
        preset.addItems([self.model_preset.itemText(i) for i in range(self.model_preset.count())])
        preset.setCurrentText(self.model_input.text())
        form.addRow("Preset:", preset)

        model = QLineEdit(self.model_input.text())
        form.addRow("Modelo:", model)
        preset.currentTextChanged.connect(model.setText)

        url = QLineEdit(self.url_input.text())
        form.addRow("URL:", url)

        api_key = QLineEdit(self.api_key_input.text())
        api_key.setEchoMode(QLineEdit.Password)
        api_key.setPlaceholderText("Opcional para servidor OpenAI-compatible")
        form.addRow("Chave API:", api_key)

        ollama_path = QLineEdit(self.ollama_path_input.text())
        ollama_path.setPlaceholderText("Opcional: caminho do ollama.exe")
        form.addRow("Ollama.exe:", ollama_path)
        layout.addLayout(form)

        models_label = QLabel("Modelos encontrados")
        models_label.setStyleSheet(ai_label_qss("dialog_section"))
        layout.addWidget(models_label)
        local_models = QListWidget()
        local_models.setMaximumHeight(110)
        for i in range(self.model_list.count()):
            local_models.addItem(self.model_list.item(i).text())
        local_models.itemDoubleClicked.connect(lambda item: model.setText(item.text()))
        layout.addWidget(local_models)

        def apply_local_settings():
            self.provider_combo.setCurrentText(provider.currentText())
            self.model_input.setText(model.text().strip())
            self.url_input.setText(url.text().strip())
            self.api_key_input.setText(api_key.text().strip())
            self.ollama_path_input.setText(ollama_path.text().strip())
            self.save_settings()
            self._sync_model_mode()

        def fill_opencode_zen_fields():
            provider.setCurrentText("OpenCode Zen")
            preset.setCurrentText(OPENCODE_ZEN_MODEL)
            model.setText(OPENCODE_ZEN_MODEL)
            url.setText(OPENCODE_ZEN_URL)
            api_key.setText(OPENCODE_ZEN_API_KEY)

        def list_models_from_dialog():
            apply_local_settings()
            self.test_connection()

        def pull_from_dialog():
            apply_local_settings()
            self.pull_model()

        def start_from_dialog():
            apply_local_settings()
            self.start_ollama()

        def locate_ollama_from_dialog():
            found = _find_ollama_exe(ollama_path.text().strip())
            if found:
                ollama_path.setText(found)
                return
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Selecionar ollama.exe", str(Path.home()), "Ollama (ollama.exe)")
            if file_path:
                ollama_path.setText(file_path)

        actions = QHBoxLayout()
        zen_btn = QPushButton("Preset OpenCode Zen")
        zen_btn.clicked.connect(fill_opencode_zen_fields)
        actions.addWidget(zen_btn)
        connect_btn = QPushButton("Conectar/listar")
        connect_btn.clicked.connect(list_models_from_dialog)
        actions.addWidget(connect_btn)
        start_btn = QPushButton("Iniciar Ollama")
        start_btn.clicked.connect(start_from_dialog)
        actions.addWidget(start_btn)
        pull_btn = QPushButton("Baixar modelo")
        pull_btn.clicked.connect(pull_from_dialog)
        actions.addWidget(pull_btn)
        locate_btn = QPushButton("Localizar")
        locate_btn.clicked.connect(locate_ollama_from_dialog)
        actions.addWidget(locate_btn)
        layout.addLayout(actions)

        chat_actions = QHBoxLayout()
        claude_setup_btn = QPushButton("Configurar Claude Code")
        claude_setup_btn.clicked.connect(lambda: (apply_local_settings(), self.configure_claude_code_zen()))
        chat_actions.addWidget(claude_setup_btn)
        open_claude_btn = QPushButton("Abrir Claude")
        open_claude_btn.clicked.connect(self.open_claude_code)
        chat_actions.addWidget(open_claude_btn)
        open_opencode_btn = QPushButton("Abrir OpenCode")
        open_opencode_btn.clicked.connect(self.open_opencode)
        chat_actions.addWidget(open_opencode_btn)
        memory_btn = QPushButton("Memoria")
        memory_btn.clicked.connect(self.edit_memory)
        chat_actions.addWidget(memory_btn)
        open_chat_btn = QPushButton("Abrir chat")
        open_chat_btn.clicked.connect(self.open_chat_picker)
        chat_actions.addWidget(open_chat_btn)
        delete_chat_btn = QPushButton("Apagar chat")
        delete_chat_btn.clicked.connect(self.delete_chat_picker)
        chat_actions.addWidget(delete_chat_btn)
        save_chat_btn = QPushButton("Salvar chat")
        save_chat_btn.clicked.connect(self.save_current_chat)
        chat_actions.addWidget(save_chat_btn)
        layout.addLayout(chat_actions)

        footer = QHBoxLayout()
        footer.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        footer.addWidget(cancel_btn)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(lambda: (apply_local_settings(), dialog.accept()))
        footer.addWidget(save_btn)
        layout.addLayout(footer)

        provider.currentTextChanged.connect(
            lambda value: url.setText(
                self.settings.get("llamacpp_url", "http://127.0.0.1:8080")
                if value == "llama.cpp"
                else self.settings.get("opencode_zen_url", OPENCODE_ZEN_URL)
                if value == "OpenCode Zen"
                else self.settings.get("openai_url", "http://127.0.0.1:1234")
                if value != "Ollama"
                else self.settings.get("ollama_url", "http://127.0.0.1:11434")
            )
        )
        dialog.exec_()

    def _current_url(self):
        provider = self.settings.get("provider", "Ollama")
        if provider == "llama.cpp":
            return self.settings.get("llamacpp_url", "http://127.0.0.1:8080")
        if provider == "OpenCode Zen":
            return self.settings.get("opencode_zen_url", OPENCODE_ZEN_URL)
        if provider != "Ollama":
            return self.settings.get("openai_url", "http://127.0.0.1:1234")
        return self.settings.get("ollama_url", "http://127.0.0.1:11434")

    def _provider_changed(self, provider):
        if provider == "Ollama":
            self.url_input.setText(self.settings.get("ollama_url", "http://127.0.0.1:11434"))
            self.model_input.setPlaceholderText("Ex: llama3.2:3b, gemma3:1b, qwen2.5:1.5b")
        elif provider == "llama.cpp":
            self.url_input.setText(self.settings.get("llamacpp_url", "http://127.0.0.1:8080"))
            self.model_input.setPlaceholderText("Modelo ou alias do llama-server")
        elif provider == "OpenCode Zen":
            self.url_input.setText(self.settings.get("opencode_zen_url", OPENCODE_ZEN_URL))
            self.model_input.setText(self.model_input.text().strip() or OPENCODE_ZEN_MODEL)
            self.model_input.setPlaceholderText(OPENCODE_ZEN_MODEL)
            if not self.api_key_input.text().strip():
                self.api_key_input.setText(OPENCODE_ZEN_API_KEY)
        else:
            self.url_input.setText(self.settings.get("openai_url", "http://127.0.0.1:1234"))
            self.model_input.setPlaceholderText("Ex: local-model, qwen2.5, gemma")

    def _provider_data(self):
        return (
            self.provider_combo.currentText(),
            self.url_input.text().strip(),
            self.model_input.text().strip(),
        )

    def save_settings(self):
        provider, url, model = self._provider_data()
        data = _load_settings()
        data["provider"] = provider
        data["model"] = model
        data["api_key"] = self.api_key_input.text().strip()
        data["ollama_path"] = self.ollama_path_input.text().strip()
        if hasattr(self, "preset_switch"):
            data["chat_preset"] = self.preset_switch.currentText()
        if provider == "Ollama":
            data["ollama_url"] = url
        elif provider == "llama.cpp":
            data["llamacpp_url"] = url
        elif provider == "OpenCode Zen":
            data["opencode_zen_url"] = url or OPENCODE_ZEN_URL
        else:
            data["openai_url"] = url
        _save_settings(data)
        self.settings = data
        self._set_status("Salvo", "#10b981")

    def test_connection(self):
        provider, url, model = self._provider_data()
        self.save_settings()
        self._run_worker(provider, url, model, "", "models")

    def start_ollama(self):
        self.save_settings()
        self._run_worker("Ollama", self.url_input.text().strip(), self.model_input.text().strip(), "", "start")

    def find_ollama_path(self):
        found = _find_ollama_exe(self.ollama_path_input.text().strip())
        if found:
            self.ollama_path_input.setText(found)
            self.save_settings()
            self._append_message("assistant", f"Ollama encontrado em:\n{found}", render=True)
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar ollama.exe", str(Path.home()), "Ollama (ollama.exe)")
        if file_path:
            self.ollama_path_input.setText(file_path)
            self.save_settings()

    def pull_model(self):
        provider, url, model = self._provider_data()
        if provider != "Ollama":
            QMessageBox.warning(self, "IA Local", "Baixar modelo pelo app funciona apenas com Ollama.")
            return
        if not model:
            QMessageBox.warning(self, "IA Local", "Digite o nome do modelo antes.")
            return
        self.save_settings()
        self._append_message("system", f"Baixando/atualizando modelo {model}. Isso pode demorar.", render=True)
        self._run_worker(provider, url, model, "", "pull")

    def ask_ai(self):
        user_text = self.prompt_input.toPlainText().strip()
        if not user_text:
            QMessageBox.warning(self, "IA Local", "Digite uma mensagem primeiro.")
            return
        provider, url, model = self._provider_data()
        self.save_settings()
        self._auto_create_files_after_response = self._looks_like_file_request(user_text)

        if self._looks_like_image_request(user_text):
            self.generate_image_from_prompt(user_text)
            self.prompt_input.clear()
            return

        images = []
        attachment_context = self._attachment_context()
        if attachment_context:
            user_text = f"{user_text}\n\n{attachment_context}"

        if self.pending_images:
            if provider == "Ollama" and _model_supports_images(model):
                images = [item["base64"] for item in self.pending_images]
                user_text += "\n\n[IMAGENS ANEXADAS]\n" + ", ".join(item["name"] for item in self.pending_images)
            else:
                names = ", ".join(item["name"] for item in self.pending_images)
                user_text += (
                    "\n\n[IMAGENS ANEXADAS]\n"
                    f"{names}\n"
                    "Observacao: o modelo atual parece ser apenas texto. Para analisar imagem de verdade, "
                    "use um modelo visual no Ollama, como llama3.2-vision ou llava."
                )

        visible_text = self.prompt_input.toPlainText().strip()
        if self.pending_attachments or self.pending_images:
            visible_text += f"\n\n[{len(self.pending_attachments) + len(self.pending_images)} anexo(s) enviados para contexto]"
        self._append_message("user", visible_text, render=True)
        self.prompt_input.clear()
        prompt = self._conversation_prompt() + "\n\nContexto completo do ultimo pedido:\n" + user_text
        self._clear_pending_attachments(update_only=True)
        self._run_worker(provider, url, model, prompt, "generate", images=images)

    def analyze_logs(self):
        log_file = CONFIG_DIR / "browser_logs.jsonl"
        if not log_file.exists():
            self._append_message("assistant", "Ainda nao encontrei logs do navegador para analisar.", render=True)
            return
        lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()[-80:]
        self.prompt_input.setText(
            "Analise estes logs do projeto. Diga a causa provavel dos erros, "
            "o que corrigir primeiro e quais passos testar:\n\n" + "\n".join(lines)
        )
        self.ask_ai()

    def attach_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Anexar arquivos para a IA",
            str(Path.home()),
            "Arquivos suportados (*.txt *.md *.html *.htm *.css *.js *.json *.csv *.xml *.py *.log *.pdf *.png *.jpg *.jpeg *.webp *.bmp);;Todos os arquivos (*)",
        )
        if not paths:
            return

        added = []
        errors = []
        for raw_path in paths:
            path = Path(raw_path)
            try:
                item = self._prepare_attachment(path)
                if item["kind"] == "image":
                    self.pending_images.append(item)
                else:
                    self.pending_attachments.append(item)
                added.append(path.name)
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

        self._update_attachments_label()
        if added:
            self._append_message("system", "Anexado: " + ", ".join(added), render=True)
        if errors:
            QMessageBox.warning(self, "IA Local", "Alguns arquivos nao foram anexados:\n\n" + "\n".join(errors[:8]))

    def _prepare_attachment(self, path):
        suffix = path.suffix.lower()
        if not path.exists():
            raise ValueError("arquivo nao encontrado")

        if suffix in IMAGE_EXTENSIONS:
            raw = path.read_bytes()
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("imagem maior que 8 MB")
            return {
                "kind": "image",
                "name": path.name,
                "path": str(path),
                "base64": base64.b64encode(raw).decode("ascii"),
            }

        if suffix == ".pdf":
            text = self._extract_pdf_text(path)
            return {"kind": "pdf", "name": path.name, "path": str(path), "content": text[:60000]}

        if suffix in TEXT_EXTENSIONS or path.stat().st_size < 2 * 1024 * 1024:
            text = path.read_text(encoding="utf-8", errors="replace")
            return {"kind": "text", "name": path.name, "path": str(path), "content": text[:60000]}

        raise ValueError("tipo de arquivo nao suportado")

    def _extract_pdf_text(self, path):
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise ValueError("leitor de PDF nao disponivel") from exc

        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages[:20], start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"--- Pagina {i} ---\n{text.strip()}")
        return "\n\n".join(pages) or "[PDF sem texto extraivel. Pode ser imagem/scan.]"

    def _attachment_context(self):
        if not self.pending_attachments:
            return ""
        chunks = ["[ARQUIVOS ANEXADOS PARA ANALISE]"]
        for item in self.pending_attachments:
            chunks.append(
                f"\nArquivo: {item['name']}\nTipo: {item['kind']}\nCaminho: {item['path']}\nConteudo:\n{item['content']}"
            )
        return "\n".join(chunks)

    def _clear_pending_attachments(self, update_only=False):
        self.pending_attachments = []
        self.pending_images = []
        self._update_attachments_label()
        if not update_only:
            self._append_message("system", "Anexos limpos.", render=True)

    def _update_attachments_label(self):
        total = len(self.pending_attachments) + len(self.pending_images)
        if total:
            self.attachments_label.setText(f"{total} anexo{'s' if total != 1 else ''} pronto{'s' if total != 1 else ''}")
        else:
            self.attachments_label.setText("")

    def save_last_response(self):
        content = self._last_assistant_content()
        if not content:
            QMessageBox.information(self, "IA Local", "Ainda nao ha resposta da IA para salvar.")
            return
        filename = f"ia_resposta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path = _safe_output_file(filename)
        path.write_text(content, encoding="utf-8")
        QMessageBox.information(self, "IA Local", f"Resposta salva em:\n{path}")

    def create_files_from_last_response(self, show_dialog=True):
        content = self._last_assistant_content()
        if not content:
            if show_dialog:
                QMessageBox.information(self, "IA Local", "Ainda nao ha resposta da IA para criar arquivos.")
            return

        blocks = self._extract_code_blocks(content)
        if not blocks:
            blocks = self._extract_loose_files(content)
        if not blocks:
            if show_dialog:
                self.save_last_response()
            return

        out_dir = _safe_output_dir(f"ia_arquivos_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        used = set()
        saved = []
        for idx, (lang, code) in enumerate(blocks, start=1):
            name = self._suggest_code_filename(lang, idx)
            while name.lower() in used:
                stem = Path(name).stem
                suffix = Path(name).suffix
                name = f"{stem}_{idx}{suffix}"
            used.add(name.lower())
            path = out_dir / name
            path.write_text(code.strip() + "\n", encoding="utf-8")
            saved.append(path.name)

        msg = f"Arquivos criados em:\n{out_dir}\n\n" + "\n".join(saved)
        self._append_message("system", msg, render=True)
        if show_dialog:
            QMessageBox.information(self, "IA Local", msg)

    def _last_assistant_content(self):
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return ""

    def _extract_code_blocks(self, content):
        pattern = re.compile(r"```([a-zA-Z0-9_.+-]*)\s*\n(.*?)```", re.DOTALL)
        return [(m.group(1).strip().lower(), m.group(2)) for m in pattern.finditer(content) if m.group(2).strip()]

    def _extract_loose_files(self, content):
        blocks = []
        html_match = re.search(r"(?is)(<!doctype html.*?</html>|<html.*?</html>)", content)
        if html_match:
            blocks.append(("html", html_match.group(1)))

        css_match = re.search(r"(?is)(?:/\*\s*style\.css\s*\*/|style\.css\s*:)\s*(.*?)(?=\n\s*(?:script\.js|index\.html|<!doctype|<html)|\Z)", content)
        if css_match:
            blocks.append(("css", css_match.group(1).strip()))

        js_match = re.search(r"(?is)(?://\s*script\.js|script\.js\s*:)\s*(.*?)(?=\n\s*(?:style\.css|index\.html|<!doctype|<html)|\Z)", content)
        if js_match:
            blocks.append(("js", js_match.group(1).strip()))
        return blocks

    def _suggest_code_filename(self, lang, idx):
        mapping = {
            "html": "index.html",
            "htm": "index.html",
            "css": "style.css",
            "javascript": "script.js",
            "js": "script.js",
            "json": "data.json",
            "python": "script.py",
            "py": "script.py",
            "markdown": "README.md",
            "md": "README.md",
        }
        return mapping.get(lang, f"arquivo_{idx}.txt")

    def clear_chat(self):
        self.messages = []
        self._clear_pending_attachments(update_only=True)
        self._append_message("assistant", "Chat limpo. Como posso ajudar no projeto?", render=True)

    def _looks_like_file_request(self, text):
        low = text.lower()
        file_words = ("arquivo", "html", "site", "pagina", "página", "css", "javascript", "script", "json", "python")
        action_words = ("cria", "crie", "gerar", "gere", "monta", "monte", "fazer", "faça", "salva", "salvar")
        return any(w in low for w in file_words) and any(w in low for w in action_words)

    def _looks_like_image_request(self, text):
        low = text.lower()
        return any(w in low for w in ("gerar imagem", "gera imagem", "criar imagem", "crie uma imagem", "/imagem"))

    def generate_image_from_prompt(self, prompt_text=None):
        prompt = (prompt_text or self.prompt_input.toPlainText()).strip()
        if not prompt:
            QMessageBox.warning(self, "IA Local", "Digite o prompt da imagem primeiro.")
            return
        prompt = re.sub(r"^/imagem\s*", "", prompt, flags=re.I).strip()
        if self._image_worker and self._image_worker.isRunning():
            QMessageBox.information(self, "IA Local", "Ja existe uma imagem sendo gerada.")
            return
        self._append_message("user", f"/imagem {prompt}", render=True)
        self.prompt_input.clear()
        self._set_status("Gerando imagem...", "#22d3ee")
        self._append_message("system", "Gerando imagem local em segundo plano...", render=True)
        self._image_worker = ImageGenerationWorker(prompt, self)
        self._image_worker.finished.connect(self._on_image_generation_finished)
        self._image_worker.start()

    def _on_image_generation_finished(self, ok, path, error):
        self._image_worker = None
        if ok:
            self._append_message("system", f"Imagem criada em:\n{path}", render=True)
            self._set_status("Imagem criada", "#10b981")
            return
        self._append_message(
            "assistant",
            "Ainda nao consegui gerar imagem porque o servidor Stable Diffusion local nao esta rodando.\n\n"
            "Quando instalar/abrir o Stable Diffusion WebUI com API em http://127.0.0.1:7860, "
            "esse botao salva a imagem direto em Downloads\\ia_imagens.\n\n"
            f"Detalhes: {error}",
            render=True,
        )
        self._set_status("Imagem indisponivel", "#f59e0b")

    def _conversation_prompt(self):
        recent = self.messages[-8:]
        lines = []
        preset_name = self.settings.get("chat_preset", "Geral")
        if hasattr(self, "preset_switch"):
            preset_name = self.preset_switch.currentText()
        preset_text = AI_CHAT_PRESETS.get(preset_name, AI_CHAT_PRESETS["Geral"])
        lines.append(f"Modo de resposta ativo: {preset_name}\n{preset_text}")
        memory = _load_memory().strip()
        if memory:
            lines.append("Memoria fixa da IA sobre o usuario/projeto:\n" + memory)
        for msg in recent:
            role = "Usuario" if msg["role"] == "user" else "Assistente"
            if msg["role"] == "system":
                role = "Sistema"
            lines.append(f"{role}: {msg['content']}")
        return "\n\n".join(lines)

    def new_chat(self):
        if self.messages:
            self.save_current_chat(show_message=False)
        self.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self._clear_pending_attachments(update_only=True)
        self._append_message("assistant", "Novo chat iniciado. O que vamos fazer agora?", render=True)
        self._refresh_chat_list()

    def save_current_chat(self, show_message=True):
        AI_CHATS_DIR.mkdir(parents=True, exist_ok=True)
        title = self._chat_title()
        data = {
            "id": self.current_chat_id,
            "title": title,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "messages": self.messages,
        }
        path = AI_CHATS_DIR / f"{self.current_chat_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._refresh_chat_list()
        if show_message:
            self._set_status("Chat salvo", "#10b981")

    def open_selected_chat(self):
        chat_id = self.chat_combo.currentData()
        if not chat_id:
            QMessageBox.information(self, "IA Local", "Nenhum chat salvo selecionado.")
            return
        path = AI_CHATS_DIR / f"{chat_id}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            QMessageBox.warning(self, "IA Local", f"Nao consegui abrir esse chat:\n{exc}")
            return
        self.current_chat_id = data.get("id") or chat_id
        self.messages = data.get("messages") or []
        self._clear_pending_attachments(update_only=True)
        self._render_chat()
        self._set_status("Chat aberto", "#10b981")

    def edit_memory(self):
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Memoria da IA",
            "O que a IA deve lembrar em todos os chats?",
            _load_memory(),
        )
        if ok:
            _save_memory(text)
            self._append_message("system", "Memoria local atualizada.", render=True)

    def _chat_title(self):
        for msg in self.messages:
            if msg.get("role") == "user" and msg.get("content"):
                first = msg["content"].splitlines()[0][:45]
                return _safe_filename(first, "Chat")
        return "Chat " + self.current_chat_id

    def _refresh_chat_list(self):
        if not hasattr(self, "chat_combo"):
            return
        current = self.current_chat_id
        self.chat_combo.blockSignals(True)
        self.chat_combo.clear()
        if AI_CHATS_DIR.exists():
            chats = []
            for path in AI_CHATS_DIR.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    chats.append((data.get("updated_at", ""), data.get("title", path.stem), data.get("id", path.stem)))
                except Exception:
                    chats.append(("", path.stem, path.stem))
            for _, title, chat_id in sorted(chats, reverse=True):
                self.chat_combo.addItem(title, chat_id)
        index = self.chat_combo.findData(current)
        if index >= 0:
            self.chat_combo.setCurrentIndex(index)
        self.chat_combo.blockSignals(False)

    def _run_worker(self, provider, url, model, prompt, mode, images=None):
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "IA Local", "A IA ainda esta processando.")
            return
        self.ask_btn.setEnabled(False)
        self._set_status("Processando", "#f59e0b")
        self._worker = AIWorker(
            provider,
            url,
            model,
            prompt,
            mode,
            api_key=self.api_key_input.text().strip(),
            ollama_path=self.ollama_path_input.text().strip(),
            images=images or [],
            parent=self,
        )
        self._worker.finished.connect(self._worker_done)
        self._worker.start()

    def _worker_done(self, ok, message, mode):
        self.ask_btn.setEnabled(True)
        if ok:
            self._set_status("Online", "#10b981")
            if mode == "models":
                self.model_list.clear()
                for line in message.splitlines():
                    if line.strip() and "Nenhum modelo" not in line:
                        self.model_list.addItem(line.strip())
                self._append_message(
                    "assistant",
                    "Conexao ok. Modelos listados acima. Clique duas vezes em um modelo para usar.",
                    render=True,
                )
            elif mode == "pull":
                self._append_message("assistant", f"Modelo pronto: {message}", render=True)
                self.test_connection()
            elif mode == "start":
                self._append_message("assistant", message, render=True)
            else:
                self._append_message("assistant", message, render=True)
                if self._auto_create_files_after_response:
                    self._auto_create_files_after_response = False
                    self.create_files_from_last_response(show_dialog=False)
                self.save_current_chat(show_message=False)
        else:
            self._auto_create_files_after_response = False
            friendly = _friendly_error(message)
            self._set_status("Offline/erro", "#f43f5e")
            self._append_message(
                "assistant",
                f"Nao consegui usar a IA local.\n\n{friendly}\n\nDetalhes tecnicos: {message}",
                render=True,
            )

    def _append_message(self, role, content, render=True):
        content = _fix_mojibake(content)
        self.messages.append({"role": role, "content": content})
        if render:
            self._render_chat()

    def _content_html(self, text):
        parts = []
        text = _fix_mojibake(text)
        for line in str(text).splitlines() or [""]:
            stripped = line.strip().strip('"')
            try:
                path = Path(stripped)
                if path.exists() and path.suffix.lower() in IMAGE_EXTENSIONS:
                    parts.append(
                        "<div style='margin:8px 0;'>"
                        f"<img src='{path.as_uri()}' style='{image_style()}'>"
                        "</div>"
                    )
                    continue
            except Exception:
                pass
            parts.append(html.escape(line))
        return "<br>".join(parts)

    def _render_chat(self):
        html_parts = [
            chat_body_open()
        ]
        for msg in self.messages:
            role = msg["role"]
            content = self._content_html(msg["content"])
            align, bg, border, label, width = message_style(role)
            html_parts.append(
                f"<div align='{align}' style='margin:14px 0;'>"
                f"<div style='display:inline-block;max-width:{width};background:{bg};"
                f"border:1px solid {border};border-radius:18px;padding:13px 15px;text-align:left;'>"
                f"<div style='font-size:11px;color:#94a3b8;font-weight:800;margin-bottom:6px;'>{label}</div>"
                f"<div style='font-size:14px;line-height:1.62;color:#f8fafc;'>{content}</div>"
                f"</div></div>"
            )
        html_parts.append("</div></body></html>")
        self.chat_output.setHtml("".join(html_parts))
        self.chat_output.moveCursor(self.chat_output.textCursor().End)

    def _set_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(self._pill_qss(color))

