import json
import os
import random
import re
from typing import Dict, Optional

from app.core.paths import BASE_DIR as PROJECT_BASE_DIR


class AddressExtractor:
    """Banco local de enderecos reserva usado quando a API de CEP falha."""

    DB_FILE = "enderecos_reserva.json"
    BASE_DIR = str(PROJECT_BASE_DIR)
    VALID_UFS = {
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG",
        "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
        "RS", "SC", "SE", "SP", "TO",
    }
    UF_NAMES = {
        "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapa",
        "BA": "Bahia", "CE": "Ceara", "DF": "Distrito Federal",
        "ES": "Espirito Santo", "GO": "Goias", "MA": "Maranhao",
        "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
        "MT": "Mato Grosso", "PA": "Para", "PB": "Paraiba",
        "PE": "Pernambuco", "PI": "Piaui", "PR": "Parana",
        "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RO": "Rondonia", "RR": "Roraima", "RS": "Rio Grande do Sul",
        "SC": "Santa Catarina", "SE": "Sergipe", "SP": "Sao Paulo",
        "TO": "Tocantins",
    }
    CEP_UF_RANGES = (
        ("SP", 1000000, 19999999),
        ("RJ", 20000000, 28999999),
        ("ES", 29000000, 29999999),
        ("MG", 30000000, 39999999),
        ("BA", 40000000, 48999999),
        ("SE", 49000000, 49999999),
        ("PE", 50000000, 56999999),
        ("AL", 57000000, 57999999),
        ("PB", 58000000, 58999999),
        ("RN", 59000000, 59999999),
        ("CE", 60000000, 63999999),
        ("PI", 64000000, 64999999),
        ("MA", 65000000, 65999999),
        ("PA", 66000000, 68899999),
        ("AP", 68900000, 68999999),
        ("AM", 69000000, 69299999),
        ("RR", 69300000, 69399999),
        ("AM", 69400000, 69899999),
        ("AC", 69900000, 69999999),
        ("DF", 70000000, 72799999),
        ("GO", 72800000, 72999999),
        ("DF", 73000000, 73699999),
        ("GO", 73700000, 76799999),
        ("TO", 77000000, 77999999),
        ("MT", 78000000, 78899999),
        ("RO", 78900000, 78999999),
        ("MS", 79000000, 79999999),
        ("PR", 80000000, 87999999),
        ("SC", 88000000, 89999999),
        ("RS", 90000000, 99999999),
    )

    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or os.path.join(self.BASE_DIR, self.DB_FILE)
        self.enderecos = self._carregar_banco()

    def _carregar_banco(self) -> list:
        if not os.path.exists(self.db_file):
            return []

        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
        except (json.JSONDecodeError, IOError, PermissionError) as exc:
            print(f"Aviso: erro ao carregar banco de enderecos: {exc}")
            return []

        if not isinstance(raw_items, list):
            return []

        normalized = []
        seen_ceps = set()
        changed = False
        for item in raw_items:
            clean = self._normalizar_endereco(item)
            cep = clean.get("cep", "")
            if not cep or cep in seen_ceps:
                changed = True
                continue
            seen_ceps.add(cep)
            normalized.append(clean)
            if clean != item:
                changed = True

        if changed:
            self.enderecos = normalized
            self._salvar_banco()

        return normalized

    def _salvar_banco(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.enderecos, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"Erro ao salvar banco de enderecos: {exc}")

    @classmethod
    def _clean_text(cls, value) -> str:
        text = str(value or "")
        text = text.replace("`", "").replace("*", "").strip()
        text = re.sub(r"\s+", " ", text)
        return text.strip(" -|;,.")

    @classmethod
    def _format_cep(cls, value) -> str:
        digits = re.sub(r"\D", "", str(value or ""))
        if len(digits) == 8:
            return f"{digits[:5]}-{digits[5:]}"
        return digits

    @classmethod
    def _infer_uf_from_cep(cls, cep: str) -> str:
        digits = re.sub(r"\D", "", str(cep or ""))
        if len(digits) != 8:
            return ""
        cep_number = int(digits)
        for uf, start, end in cls.CEP_UF_RANGES:
            if start <= cep_number <= end:
                return uf
        return ""

    @classmethod
    def _normalizar_uf(cls, uf: str, cep: str = "") -> str:
        uf = cls._clean_text(uf).upper()
        if uf in cls.VALID_UFS:
            return uf
        return cls._infer_uf_from_cep(cep)

    @classmethod
    def _normalizar_endereco(cls, item) -> Dict:
        item = item if isinstance(item, dict) else {}
        cep = cls._format_cep(item.get("cep", ""))
        uf = cls._normalizar_uf(item.get("uf") or item.get("estado"), cep)
        estado = cls.UF_NAMES.get(uf, cls._clean_text(item.get("estado", "")))
        return {
            "cep": cep,
            "logradouro": cls._clean_text(item.get("logradouro", "")),
            "bairro": cls._clean_text(item.get("bairro", "")),
            "cidade": cls._clean_text(item.get("cidade", "")),
            "estado": estado,
            "uf": uf,
            "numero": cls._clean_text(item.get("numero", "")),
        }

    def extrair_endereco(self, texto: str) -> Optional[Dict]:
        cep_match = re.search(r"\b(\d{5}-?\d{3})\b", texto or "")
        if not cep_match:
            return None

        cep = self._format_cep(cep_match.group(1))
        if any(e.get("cep") == cep for e in self.enderecos):
            return None

        endereco = {
            "cep": cep,
            "logradouro": "",
            "bairro": "",
            "cidade": "",
            "estado": "",
            "uf": "",
            "numero": "",
        }

        log_match = re.search(
            r"(?:Rua|R\.|Av|Avenida|Logradouro|Endereco|Endere..o|End)[:\s]+([^,\n]+)",
            texto,
            re.IGNORECASE,
        )
        if log_match:
            endereco["logradouro"] = log_match.group(1).strip()

        bairro_match = re.search(r"(?:Bairro)[:\s]+([^,\n]+)", texto, re.IGNORECASE)
        if bairro_match:
            endereco["bairro"] = bairro_match.group(1).strip()

        cidade_match = re.search(r"(?:Cidade|Municipio|Munic..pio)[:\s]+([^,\n/-]+)", texto, re.IGNORECASE)
        if cidade_match:
            endereco["cidade"] = cidade_match.group(1).strip()

        uf_match = re.search(r"(?:Estado|UF)[:\s]+([A-Z]{2})", texto, re.IGNORECASE)
        if uf_match:
            endereco["uf"] = uf_match.group(1).strip().upper()

        num_match = re.search(r"(?:Numero|N..mero|Num|NÂº|Nº)[:\s]+(\d+)", texto, re.IGNORECASE)
        if num_match:
            endereco["numero"] = num_match.group(1).strip()

        endereco = self._normalizar_endereco(endereco)
        if endereco["logradouro"] and endereco["cidade"]:
            self.enderecos.append(endereco)
            self._salvar_banco()
            return endereco

        return None

    def get_reserva(self, uf: str = None) -> Optional[Dict]:
        candidatos = [
            e for e in self.enderecos
            if e.get("cep") and e.get("logradouro") and e.get("cidade")
        ]

        uf = self._normalizar_uf(uf or "")
        if uf:
            filtrados = [e for e in candidatos if e.get("uf") == uf]
            candidatos = filtrados or candidatos

        if candidatos:
            return dict(random.choice(candidatos))
        return None

    def stats(self) -> Dict:
        total = len(self.enderecos)
        valid_uf = sum(1 for e in self.enderecos if e.get("uf") in self.VALID_UFS)
        usable = sum(
            1 for e in self.enderecos
            if e.get("cep") and e.get("logradouro") and e.get("cidade")
        )
        return {"total": total, "valid_uf": valid_uf, "usable": usable}
