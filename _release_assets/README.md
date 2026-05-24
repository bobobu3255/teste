# Release assets

Pacotes prontos para download/distribuição do Telegram Collector Pro.

## Disponíveis

### `TelegramCollectorPro_v12.0_DESIGN_REWORK_20260524.zip`
- **Versão:** v12.0 — Design Rework (Cyberpunk Edition)
- **Tamanho:** ~830 KB
- **Conteúdo:** projeto completo com a reformulação visual aplicada
- **Não inclui:** `_temp/`, `archive/dev_backups/`, `__pycache__/`, `.git/`

#### Como baixar
- **Link direto (raw):** [TelegramCollectorPro_v12.0_DESIGN_REWORK_20260524.zip](https://github.com/bobobu3255/teste/raw/design/professional-cover/_release_assets/TelegramCollectorPro_v12.0_DESIGN_REWORK_20260524.zip)
- Ou navegue até este arquivo no GitHub e clique em **Download**.

#### Como usar
```bash
unzip TelegramCollectorPro_v12.0_DESIGN_REWORK_20260524.zip
cd tcp_release
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### O que mudou no design
- `app/ui/components.py` — 21 novos símbolos (tokens + helpers)
- `app/ui/app_theme.py` — botões com gradient, foco brilhante, 13 novos seletores
- `app/ui/app_motion.py` (NOVO) — glow real, sombras, fade-in
- `app/ui/splash.py` (NOVO) — splash screen cyberpunk com logo animado
- `app/ui/app_bootstrap.py` — paleta Qt + fonte sincronizadas com design system

Veja `CHANGELOG.md` na raiz do pacote para detalhes completos.
