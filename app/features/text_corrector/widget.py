#!/usr/bin/env python3
"""Ferramenta de correcao, reescrita e traducao de textos."""

import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QComboBox,
    QCheckBox,
    QFrame,
    QApplication,
    QSizePolicy,
)

try:
    from app.features.ai_assistant.widget import AIWorker, _load_settings
except Exception:
    try:
        from ai_assistant_widget import AIWorker
        from app.features.ai_assistant.widget import _load_settings
    except Exception:
        AIWorker = None
        _load_settings = None


from app.core.paths import BASE_DIR
from app.ui.app_theme import DARK_STYLE_PRO
from app.ui.components import PALETTE


OUTPUT_DIR = BASE_DIR / "IA_Saidas" / "corretor_textos"


COMMON_REPLACEMENTS = [
    (r"\bd e\b", "de"),
    (r"\bd o\b", "do"),
    (r"\bd a\b", "da"),
    (r"\bcorrijir\b", "corrigir"),
    (r"\bcorrije\b", "corrige"),
    (r"\bconsegui\b", "conseguir"),
    (r"\bvc\b", "você"),
    (r"\bvcs\b", "vocês"),
    (r"\btbm\b", "também"),
    (r"\btb\b", "também"),
    (r"\bpq\b", "por que"),
    (r"\bq\b", "que"),
    (r"\bn\b", "não"),
    (r"\bnao\b", "não"),
    (r"\bto\b", "estou"),
    (r"\btô\b", "estou"),
    (r"\bta\b", "está"),
    (r"\btá\b", "está"),
    (r"\bpra\b", "para"),
    (r"\bpro\b", "para o"),
    (r"\bpros\b", "para os"),
    (r"\baki\b", "aqui"),
    (r"\baq\b", "aqui"),
    (r"\bdps\b", "depois"),
    (r"\bblz\b", "beleza"),
    (r"\bmsg\b", "mensagem"),
    (r"\btd\b", "tudo"),
    (r"\bcade\b", "cadê"),
    (r"\bvoce\b", "você"),
    (r"\besta\b", "está"),
    (r"\bja\b", "já"),
    (r"\btambem\b", "também"),
    (r"\bso\b", "só"),
    (r"\bsera\b", "será"),
    (r"\bpossivel\b", "possível"),
    (r"\bportugues\b", "português"),
    (r"\bferramenta\b", "ferramenta"),
    (r"\bferramentras\b", "ferramentas"),
    (r"\bfunsao\b", "função"),
    (r"\bfuncao\b", "função"),
    (r"\bdesaine\b", "design"),
    (r"\bdesainer\b", "design"),
    (r"\binterfasse\b", "interface"),
    (r"\bpreciona\b", "pressiona"),
    (r"\baperta\b", "apertar"),
    (r"\babri\b", "abrir"),
    (r"\bve\b", "ver"),
    (r"\bcoloca\b", "colocar"),
    (r"\bassina\b", "assinar"),
    (r"\bprencher\b", "preencher"),
    (r"\bativaçao\b", "ativação"),
    (r"\bapaga\b", "apagar"),
    (r"\bocuta\b", "oculta"),
    (r"\bocultar\b", "ocultar"),
    (r"\bintale\b", "instale"),
    (r"\binstala\b", "instalar"),
    (r"\bprendrive\b", "pendrive"),
    (r"\bpendriver\b", "pendrive"),
    (r"\bresuldado\b", "resultado"),
    (r"\bresuldados\b", "resultados"),
    (r"\binportante\b", "importante"),
    (r"\biprementa\b", "implementar"),
    (r"\bimprementaçao\b", "implementação"),
    (r"\bimplementacao\b", "implementação"),
    (r"\bimplementaçao\b", "implementação"),
    (r"\bfringerprint\b", "fingerprint"),
    (r"\bconcerteza\b", "com certeza"),
    (r"\bderrepente\b", "de repente"),
    (r"\bporisso\b", "por isso"),
    (r"\bagente\b", "a gente"),
]


PHRASE_REPLACEMENTS = [
    (r"\berro d e portugues\b", "erro de português"),
    (r"\berros d e portugues\b", "erros de português"),
    (r"\berros d eportugues\b", "erros de português"),
    (r"\berros deportugues\b", "erros de português"),
    (r"\bevitar erros d e portugues\b", "evitar erros de português"),
    (r"\bevitar erros d eportugues\b", "evitar erros de português"),
    (r"\beu queria sabe\b", "eu queria saber"),
    (r"\bqueria sabe\b", "queria saber"),
    (r"\bquero sabe\b", "quero saber"),
    (r"\boff line\b", "offline"),
    (r"\bon line\b", "online"),
    (r"\bquero que de pra\b", "quero que dê para"),
    (r"\bda esse erro\b", "dá esse erro"),
    (r"\bda pra melhora\b", "dá para melhorar"),
    (r"\bda pra melhorar\b", "dá para melhorar"),
    (r"\bda para melhora\b", "dá para melhorar"),
    (r"\bda para melhorar\b", "dá para melhorar"),
    (r"\bpara melhora\b", "para melhorar"),
    (r"\bvoce consegue\b", "você consegue"),
    (r"\bvc consegue\b", "você consegue"),
    (r"\bconsegue corrige\b", "consegue corrigir"),
    (r"\bconsegue me ajuda\b", "consegue me ajudar"),
    (r"\bcorrige esse texto\b", "corrigir esse texto"),
    (r"\bpor que (está|esta|tem|vai|foi|é|sou|era)\b", r"porque \1"),
    (r"\bmais eu\b", "mas eu"),
    (r"\bmais agora\b", "mas agora"),
    (r"\bmais nao\b", "mas não"),
    (r"\bmais não\b", "mas não"),
    (r"\bme ajuda\b", "me ajude"),
    (r"\bquero pode\b", "quero poder"),
    (r"\bso falta assina\b", "só falta assinar"),
    (r"\bsó falta assina\b", "só falta assinar"),
    (r"\bso falta cria\b", "só falta criar"),
    (r"\bsó falta cria\b", "só falta criar"),
    (r"\bso falta coloca\b", "só falta colocar"),
    (r"\bsó falta coloca\b", "só falta colocar"),
    (r"\bmuito bem só falta\b", "muito bem, só falta"),
    (r"\bmuito bem, só falta\b", "muito bem, só falta"),
    (r"\bda pra\b", "dá para"),
    (r"\bdar pra\b", "dar para"),
    (r"\bd e\b", "de"),
]


SYNONYMS = {
    "melhorar": ["aprimorar", "aperfeiçoar", "otimizar", "refinar"],
    "corrigir": ["ajustar", "revisar", "consertar", "retificar"],
    "bonito": ["elegante", "agradável", "bem acabado", "polido"],
    "simples": ["fácil", "direto", "objetivo", "descomplicado"],
    "rápido": ["ágil", "veloz", "imediato", "instantâneo"],
    "erro": ["falha", "problema", "inconsistência", "defeito"],
    "texto": ["frase", "mensagem", "conteúdo", "redação"],
    "ferramenta": ["recurso", "utilitário", "módulo", "função"],
    "interface": ["tela", "visual", "painel", "layout"],
}


def _fix_mojibake(text):
    if not any(mark in text for mark in ("Ã", "Â", "�")):
        return text
    try:
        fixed = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
        if fixed.count("Ã") < text.count("Ã"):
            return fixed
    except Exception:
        pass
    return text


def _capitalize_sentences(text):
    def repl(match):
        prefix, letter = match.group(1), match.group(2)
        return prefix + letter.upper()

    text = re.sub(r"(^|[.!?]\s+)([a-záàâãéêíóôõúç])", repl, text)
    return text


def _finish_sentence(text):
    if text and "\n" not in text and not re.search(r"[.!?…]$", text):
        return text + "."
    return text


def _basic_cleanup(text):
    text = _fix_mojibake(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _apply_common_rules(text):
    text = _basic_cleanup(text)
    for pattern, replacement in COMMON_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    for pattern, replacement in PHRASE_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\bso\b", "só", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    text = _capitalize_sentences(text)
    return _finish_sentence(text)


def _formalize(text):
    text = _apply_common_rules(text)
    replacements = [
        (r"\ba gente\b", "nós"),
        (r"\bbeleza\b", "certo"),
        (r"\bdá para\b", "é possível"),
        (r"\bquero\b", "gostaria de"),
        (r"\bpreciso\b", "necessito"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return _capitalize_sentences(text)


def _make_short(text):
    text = _apply_common_rules(text)
    text = re.sub(r"\bpor favor\b,?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\beu gostaria de\b", "quero", text, flags=re.IGNORECASE)
    text = re.sub(r"\bé possível\b", "dá para", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _make_friendly(text):
    text = _apply_common_rules(text)
    if text and not re.search(r"[.!?]$", text):
        text += "."
    return text


def _punctuation_only(text):
    text = _basic_cleanup(text)
    text = _capitalize_sentences(text)
    return text


def _mode_key(mode):
    cleaned = _fix_mojibake(mode or "").lower()
    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _language_code(locale):
    key = _mode_key(locale)
    if "pt" in key and "br" not in key:
        return "pt-PT"
    return "pt-BR"


def _apply_languagetool(text, language="pt-BR"):
    """Usa LanguageTool local se estiver rodando em localhost:8081."""
    if not text.strip():
        return text, False, ""
    payload = urllib.parse.urlencode({
        "text": text,
        "language": language,
        "enabledOnly": "false",
    }).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:8081/v2/check",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2.2) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return text, False, str(exc)

    corrected = text
    applied = 0
    for match in sorted(data.get("matches", []), key=lambda item: item.get("offset", 0), reverse=True):
        replacements = match.get("replacements") or []
        if not replacements:
            continue
        replacement = replacements[0].get("value", "")
        if not replacement:
            continue
        offset = int(match.get("offset", 0))
        length = int(match.get("length", 0))
        if offset < 0 or length <= 0 or offset + length > len(corrected):
            continue
        corrected = corrected[:offset] + replacement + corrected[offset + length:]
        applied += 1
    return corrected, applied > 0, ""


def _json_get(url, timeout=1.5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return {}


def _best_ollama_model(ollama_url):
    data = _json_get(ollama_url.rstrip("/") + "/api/tags")
    names = [item.get("name", "") for item in data.get("models", []) if item.get("name")]
    if not names:
        return ""
    priority = ("qwen3", "qwen2.5", "qwen", "llama3.2", "llama", "gemma", "mistral")
    for token in priority:
        for name in names:
            if token in name.lower():
                return name
    return names[0]


def _text_ai_backend(settings):
    provider = settings.get("provider", "Ollama")
    model = settings.get("model", "")
    if provider == "OpenCode Zen":
        ollama_url = settings.get("ollama_url", "http://127.0.0.1:11434")
        return "Ollama", ollama_url, _best_ollama_model(ollama_url) or "qwen3:1.7b"
    if provider == "Ollama":
        ollama_url = settings.get("ollama_url", "http://127.0.0.1:11434")
        if not model or any(token in model.lower() for token in ("minimax", "claude", "gpt", "opencode")):
            model = _best_ollama_model(ollama_url) or "qwen2.5:1.5b"
        return "Ollama", ollama_url, model
    if provider == "llama.cpp":
        return provider, settings.get("llamacpp_url", "http://127.0.0.1:8080"), model
    return provider, settings.get("openai_url", "http://127.0.0.1:1234"), model


def _synonym_report(text):
    words = set(re.findall(r"[A-Za-zÀ-ÿ]+", text.lower()))
    lines = []
    for word, options in SYNONYMS.items():
        if word in words:
            lines.append(f"{word}: " + ", ".join(options))
    if not lines:
        return "Não encontrei palavras comuns do dicionário interno. Tente um texto maior ou use a correção com IA."
    return "Sugestões de sinônimos:\n\n" + "\n".join(lines)


def local_transform(text, mode):
    if not text.strip():
        return ""
    key = _mode_key(mode)
    if key == "correcao rapida":
        return _apply_common_rules(text)
    if key == "portugues formal":
        return _formalize(text)
    if key == "mensagem natural":
        return _make_friendly(text)
    if key == "curto e direto":
        return _make_short(text)
    if key == "pontuacao":
        return _punctuation_only(text)
    if key == "sinonimos":
        return _synonym_report(text)
    return _apply_common_rules(text)


class TextCorrectorWidget(QWidget):
    """Editor inspirado em corretores online, com modo local e IA opcional."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self.setStyleSheet(self._style())
        self._build()
        self._update_stats()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("Hero")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(16, 14, 16, 14)
        header_lay.setSpacing(12)

        title_box = QVBoxLayout()
        title = QLabel("Português Pro")
        title.setObjectName("Title")
        subtitle = QLabel("Correção rápida, reescrita com IA local, sinônimos e tradução em uma tela limpa.")
        subtitle.setObjectName("Subtle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_lay.addLayout(title_box, 1)

        self.status = QLabel("Local pronto")
        self.status.setObjectName("Status")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setMinimumWidth(110)
        header_lay.addWidget(self.status)
        root.addWidget(header)

        controls = QFrame()
        controls.setObjectName("Panel")
        controls_lay = QGridLayout(controls)
        controls_lay.setContentsMargins(12, 12, 12, 12)
        controls_lay.setHorizontalSpacing(10)
        controls_lay.setVerticalSpacing(8)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Correção rápida",
            "Português formal",
            "Mensagem natural",
            "Curto e direto",
            "Pontuação",
            "Sinônimos",
            "Traduzir para inglês",
            "Traduzir para português",
        ])
        self.locale_combo = QComboBox()
        self.locale_combo.addItems(["Português BR", "Português PT", "Português neutro"])
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["Normal", "Educado", "Profissional", "Amigável", "Mensagem curta"])

        self.keep_meaning = QCheckBox("Manter sentido")
        self.keep_meaning.setChecked(True)
        self.keep_emojis = QCheckBox("Manter emojis")
        self.keep_emojis.setChecked(True)

        mode_label = QLabel("Modo")
        mode_label.setObjectName("FieldLabel")
        locale_label = QLabel("Português")
        locale_label.setObjectName("FieldLabel")
        tone_label = QLabel("Tom")
        tone_label.setObjectName("FieldLabel")
        controls_lay.addWidget(mode_label, 0, 0)
        controls_lay.addWidget(self.mode_combo, 0, 1)
        controls_lay.addWidget(locale_label, 0, 2)
        controls_lay.addWidget(self.locale_combo, 0, 3)
        controls_lay.addWidget(tone_label, 1, 0)
        controls_lay.addWidget(self.tone_combo, 1, 1)
        controls_lay.addWidget(self.keep_meaning, 1, 2)
        controls_lay.addWidget(self.keep_emojis, 1, 3)
        controls_lay.setColumnStretch(1, 1)
        controls_lay.setColumnStretch(3, 1)
        root.addWidget(controls)

        editors = QHBoxLayout()
        editors.setSpacing(12)

        left = self._editor_card("Texto original")
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("Cole ou digite seu texto aqui...")
        self.input_text.textChanged.connect(self._update_stats)
        left.layout().addWidget(self.input_text, 1)
        self.input_stats = QLabel("0 palavras • 0 caracteres")
        self.input_stats.setObjectName("Subtle")
        left.layout().addWidget(self.input_stats)

        right = self._editor_card("Texto corrigido")
        self.output_text = QPlainTextEdit()
        self.output_text.setPlaceholderText("O resultado aparece aqui.")
        self.output_text.textChanged.connect(self._update_stats)
        right.layout().addWidget(self.output_text, 1)
        self.output_stats = QLabel("0 palavras • 0 caracteres")
        self.output_stats.setObjectName("Subtle")
        right.layout().addWidget(self.output_stats)

        editors.addWidget(left, 1)
        editors.addWidget(right, 1)
        root.addLayout(editors, 1)

        action_bar = QFrame()
        action_bar.setObjectName("Panel")
        actions = QHBoxLayout(action_bar)
        actions.setContentsMargins(12, 10, 12, 10)
        actions.setSpacing(8)

        self.local_btn = QPushButton("✓ Corrigir rápido")
        self.local_btn.setObjectName("Primary")
        self.local_btn.clicked.connect(self.correct_local)
        self.ai_btn = QPushButton("🤖 Melhorar com IA")
        self.ai_btn.clicked.connect(self.correct_with_ai)
        self.copy_btn = QPushButton("⎘ Copiar")
        self.copy_btn.clicked.connect(self.copy_output)
        self.swap_btn = QPushButton("↔ Usar resultado")
        self.swap_btn.clicked.connect(self.use_output_as_input)
        self.save_btn = QPushButton("💾 Salvar TXT")
        self.save_btn.clicked.connect(self.save_output)
        self.clear_btn = QPushButton("🗑 Limpar")
        self.clear_btn.clicked.connect(self.clear_all)

        for button in (self.local_btn, self.ai_btn, self.copy_btn, self.swap_btn, self.save_btn, self.clear_btn):
            button.setMinimumHeight(38)
            actions.addWidget(button)
        root.addWidget(action_bar)

        self.notice = QLabel(
            "Dica: o modo rápido funciona offline. Se LanguageTool local ou Ollama estiverem abertos, eu uso automaticamente quando fizer sentido."
        )
        self.notice.setObjectName("Hint")
        self.notice.setWordWrap(True)
        root.addWidget(self.notice)

    def _editor_card(self, title):
        card = QFrame()
        card.setObjectName("Panel")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        lay.addWidget(label)
        return card

    def _prompt_for_ai(self, text):
        mode = self.mode_combo.currentText()
        locale = self.locale_combo.currentText()
        tone = self.tone_combo.currentText()
        meaning = "sem mudar o sentido principal" if self.keep_meaning.isChecked() else "pode melhorar a estrutura se necessario"
        emojis = "mantendo emojis quando existirem" if self.keep_emojis.isChecked() else "removendo emojis se atrapalharem"

        if mode == "Traduzir para inglês":
            task = "Traduza o texto para ingles natural e claro."
        elif mode == "Traduzir para português":
            task = f"Traduza o texto para {locale}, com tom {tone}."
        elif mode == "Sinônimos":
            task = "Liste sinonimos uteis para as palavras principais e depois entregue uma versao reescrita."
        else:
            task = f"Corrija e reescreva em {locale}, com tom {tone}, {meaning}, {emojis}."

        return (
            f"{task}\n"
            "Responda somente com o texto final ou com a lista pedida. "
            "Nao explique o processo.\n\n"
            f"Texto:\n{text}"
        )

    def correct_local(self):
        text = self.input_text.toPlainText()
        mode = self.mode_combo.currentText()
        if not text.strip():
            self._notice("Cole ou digite um texto primeiro.", "#fbbf24")
            self._set_status("Aguardando texto", "#fbbf24")
            return
        if _mode_key(mode).startswith("traduzir"):
            self._notice("Tradução precisa de IA. Vou tentar usar a IA local automaticamente.", "#38bdf8")
            self.correct_with_ai()
            return
        result = local_transform(text, mode)
        if _mode_key(mode) not in {"sinonimos"}:
            lt_result, used_lt, lt_error = _apply_languagetool(result, _language_code(self.locale_combo.currentText()))
            if used_lt:
                result = _capitalize_sentences(_basic_cleanup(lt_result))
                self._notice("Corrigi com regras locais e LanguageTool local.", "#10b981")
            elif lt_error:
                self._notice("Correção rápida offline aplicada. LanguageTool local não está aberto, então ignorei essa etapa.", "#8aa4bd")
        self.output_text.setPlainText(result)
        if result.strip() == _basic_cleanup(text).strip() and text.strip():
            self._set_status("Pouca mudança", "#fbbf24")
        else:
            self._set_status("Corrigido", "#10b981")

    def correct_with_ai(self):
        if AIWorker is None or _load_settings is None:
            self._apply_ai_fallback("IA Local não está disponível neste projeto.")
            return
        text = self.input_text.toPlainText().strip()
        if not text:
            self._notice("Cole ou digite um texto primeiro.", "#fbbf24")
            self._set_status("Aguardando texto", "#fbbf24")
            return
        settings = _load_settings()
        provider, url, model = _text_ai_backend(settings)

        self.ai_btn.setEnabled(False)
        self.local_btn.setEnabled(False)
        self._set_status("IA revisando", "#38bdf8")
        self._notice(f"Usando {provider} {model or ''} para revisar o texto.", "#38bdf8")
        self._worker = AIWorker(
            provider,
            url,
            model,
            self._prompt_for_ai(text),
            mode="generate",
            api_key=settings.get("api_key", ""),
            ollama_path=settings.get("ollama_path", ""),
        )
        self._worker.finished.connect(self._ai_done)
        self._worker.start()

    def _ai_done(self, ok, message, mode):
        self.ai_btn.setEnabled(True)
        self.local_btn.setEnabled(True)
        if ok:
            self.output_text.setPlainText(message.strip())
            self._set_status("IA concluiu", "#10b981")
            self._notice("Texto revisado pela IA local.", "#10b981")
        else:
            self._apply_ai_fallback(message)
        self._worker = None

    def _apply_ai_fallback(self, message):
        mode = self.mode_combo.currentText()
        if _mode_key(mode).startswith("traduzir"):
            fallback = self.input_text.toPlainText().strip()
            if fallback:
                self.output_text.setPlainText(fallback)
        else:
            fallback = local_transform(self.input_text.toPlainText(), mode)
            if fallback:
                self.output_text.setPlainText(fallback)
        self._set_status("IA offline", "#f43f5e")
        self._notice(
            "Não consegui usar a IA agora. Apliquei o melhor modo local possível. "
            f"Detalhes: {message}",
            "#f43f5e",
        )

    def copy_output(self):
        text = self.output_text.toPlainText()
        if not text.strip():
            return
        QApplication.clipboard().setText(text)
        self._set_status("Copiado", "#10b981")

    def use_output_as_input(self):
        text = self.output_text.toPlainText()
        if text.strip():
            self.input_text.setPlainText(text)
            self.output_text.clear()
            self._set_status("Resultado virou original", "#38bdf8")

    def save_output(self):
        text = self.output_text.toPlainText().strip()
        if not text:
            self._notice("Não há resultado para salvar.", "#fbbf24")
            return
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"texto_corrigido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = OUTPUT_DIR / filename
        path.write_text(text, encoding="utf-8")
        self._set_status("Salvo", "#10b981")
        self._notice(f"Arquivo salvo em: {path}", "#10b981")

    def clear_all(self):
        self.input_text.clear()
        self.output_text.clear()
        self._set_status("Limpo", "#94a3b8")

    def _update_stats(self):
        in_text = self.input_text.toPlainText() if hasattr(self, "input_text") else ""
        out_text = self.output_text.toPlainText() if hasattr(self, "output_text") else ""
        self.input_stats.setText(f"{self._word_count(in_text)} palavras • {len(in_text)} caracteres")
        self.output_stats.setText(f"{self._word_count(out_text)} palavras • {len(out_text)} caracteres")

    def _word_count(self, text):
        return len(re.findall(r"\S+", text))

    def _set_status(self, text, color):
        self.status.setText(text)
        self.status.setStyleSheet(
            f"background: rgba(15,23,42,0.92); color: {color}; "
            f"border: 1px solid {color}; border-radius: 16px; padding: 8px 12px; font-weight: 800;"
        )

    def _notice(self, text, color="#9ddff0"):
        if not hasattr(self, "notice"):
            return
        self.notice.setText(text)
        self.notice.setStyleSheet(
            f"background: rgba(34,211,238,0.08); border: 1px solid rgba(34,211,238,0.22); "
            f"border-radius: 10px; color: {color}; padding: 9px 12px;"
        )
        QTimer.singleShot(6500, self._reset_notice)

    def _reset_notice(self):
        if not hasattr(self, "notice"):
            return
        self.notice.setText(
            "Dica: o modo rápido funciona offline. Se LanguageTool local ou Ollama estiverem abertos, eu uso automaticamente quando fizer sentido."
        )
        self.notice.setStyleSheet(
            "background: rgba(34,211,238,0.08); border: 1px solid rgba(34,211,238,0.20); "
            "border-radius: 10px; color: #9ddff0; padding: 9px 12px;"
        )

    def _style(self):
        return DARK_STYLE_PRO + f"""
            QFrame#Hero {{
                background: {PALETTE.card};
                border: 1px solid {PALETTE.border};
                border-radius: 10px;
            }}
            QFrame#Panel {{
                background: {PALETTE.card};
                border: 1px solid {PALETTE.border};
                border-radius: 10px;
            }}
            QLabel#Title {{
                color: {PALETTE.text};
                font-size: 22px;
                font-weight: 900;
            }}
            QLabel#SectionTitle {{
                color: {PALETTE.primary};
                font-weight: 900;
                font-size: 13px;
            }}
            QLabel#Subtle {{
                color: {PALETTE.muted};
            }}
            QLabel#FieldLabel {{
                color: #93c5fd;
                font-weight: 800;
                padding-left: 2px;
            }}
            QLabel#Hint {{
                background: rgba(34,211,238,0.08);
                border: 1px solid rgba(34,211,238,0.20);
                border-radius: 8px;
                color: #9ddff0;
                padding: 9px 12px;
            }}
            QPlainTextEdit {{
                background: {PALETTE.panel};
                border: 1px solid {PALETTE.border};
                border-radius: 8px;
                padding: 12px;
                color: {PALETTE.text};
                selection-background-color: #0891b2;
                font-size: 14px;
            }}
            QPlainTextEdit:focus {{
                border-color: {PALETTE.border_strong};
            }}
            QCheckBox {{
                color: #cbd5e1;
                spacing: 8px;
            }}
            QPushButton#Primary {{
                background: {PALETTE.success};
                border: none;
                color: #ffffff;
            }}
            QPushButton#Primary:hover {{
                background: #34d399;
            }}
        """
