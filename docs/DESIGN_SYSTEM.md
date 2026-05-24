<div align="center">
  <img src="assets/banner.svg" alt="Telegram Collector Pro" width="100%"/>
</div>

# Design System — Cyberpunk Neon

> A linguagem visual oficial do Telegram Collector Pro v12. Tudo que aparece em tela deve consumir os tokens definidos aqui.

---

## 1. Princípios

1. **Console profissional, não jogo.** O visual é "tech sério com personalidade", não arcade.
2. **Hierarquia por luz, não por peso.** Glow + acento cyan guiam o olho; negritos são reservados a títulos.
3. **Densidade controlada.** Espaçamentos generosos em painéis externos, compactos em listas/dados.
4. **Movimento sutil.** Animações curtas (120–180ms) e apenas em interações que pedem feedback.
5. **Acessibilidade primeiro.** Contraste mínimo AA em todo texto sobre superfícies.

## 2. Paleta

<div align="center">
  <img src="assets/palette.svg" alt="Paleta Cyberpunk Neon" width="92%"/>
</div>

### Tokens base

| Token | Hex | Aplicação |
|---|---|---|
| `bg.deep` | `#0a0e1a` | Fundo da janela, canvases |
| `bg.surface` | `#111827` | Cards, painéis, headers |
| `bg.elevated` | `#0f172a` | Pills, inputs, popovers |
| `border.subtle` | `rgba(34,211,238,0.18)` | Bordas internas |
| `border.accent` | `rgba(34,211,238,0.55)` | Bordas de elementos focados/ativos |

### Acentos

| Token | Hex | Aplicação |
|---|---|---|
| `accent` | `#06b6d4` | Botões primários, brand |
| `accent.light` | `#22d3ee` | Hover, highlights, glow |
| `accent.deep` | `#0e7490` | Estados pressionados |

### Texto

| Token | Hex | Aplicação |
|---|---|---|
| `text.primary` | `#f1f5f9` | Títulos, conteúdo |
| `text.secondary` | `#cbd5e1` | Texto auxiliar |
| `text.muted` | `#94a3b8` | Labels, hints |
| `text.disabled` | `#475569` | Estados inativos |

### Semânticos

| Token | Hex | Aplicação |
|---|---|---|
| `success` | `#10b981` | Confirmações, status saudável |
| `warning` | `#f59e0b` | Avisos não bloqueantes |
| `danger` | `#f43f5e` | Erros, ações destrutivas |
| `info` | `#22d3ee` | Mensagens informativas |

## 3. Tipografia

| Uso | Família | Peso | Tamanho |
|---|---|---|---|
| Display / título de tela | Segoe UI / Inter | 800 | 28–32 px |
| Heading de painel | Segoe UI / Inter | 700 | 18–22 px |
| Corpo | Segoe UI / Inter | 400 | 13–14 px |
| Labels / hints | Segoe UI / Inter | 500 | 11–12 px |
| Mono (logs, código, badges) | JetBrains Mono / Consolas | 500–700 | 11–12 px |

Regras:
- **Letter-spacing** de `+1px` em badges e eyebrows.
- **Letter-spacing** de `-0.5px` em títulos grandes (efeito condensado).
- Nunca usar mais de **2 famílias** em uma mesma tela.

## 4. Espaçamento e raio

Sistema base de **4px**: `4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 56`.

| Token | Valor | Uso |
|---|---|---|
| `radius.sm` | 6 px | Inputs, tags |
| `radius.md` | 10 px | Cards |
| `radius.lg` | 14 px | Painéis grandes, modais |
| `radius.pill` | 999 px | Badges, pills |

## 5. Elevação & glow

Em vez de sombras pesadas, usamos **glow cyan** sutil:

```css
/* Glow leve (botões em hover, ícones ativos) */
filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.45));

/* Glow forte (estado focado) */
filter: drop-shadow(0 0 12px rgba(34, 211, 238, 0.65));
```

Sombras tradicionais ficam reservadas a modais:
```css
box-shadow: 0 18px 48px rgba(0, 0, 0, 0.55);
```

## 6. Componentes-chave

### Botão primário
```qss
QPushButton[variant="primary"] {
  background: #06b6d4;
  color: #0a0e1a;
  border: 1px solid #22d3ee;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 700;
}
QPushButton[variant="primary"]:hover { background: #22d3ee; }
QPushButton[variant="primary"]:pressed { background: #0e7490; }
```

### Botão secundário (ghost)
```qss
QPushButton[variant="ghost"] {
  background: transparent;
  color: #22d3ee;
  border: 1px solid rgba(34, 211, 238, 0.55);
  border-radius: 8px;
  padding: 8px 16px;
}
QPushButton[variant="ghost"]:hover {
  background: rgba(34, 211, 238, 0.10);
}
```

### Input
```qss
QLineEdit {
  background: #0f172a;
  color: #f1f5f9;
  border: 1px solid rgba(34, 211, 238, 0.25);
  border-radius: 6px;
  padding: 6px 10px;
  selection-background-color: #06b6d4;
}
QLineEdit:focus { border-color: #22d3ee; }
```

### Card / painel
```qss
QFrame[role="card"] {
  background: #111827;
  border: 1px solid rgba(34, 211, 238, 0.18);
  border-radius: 14px;
}
```

### Badge / pill
```qss
QLabel[role="pill"] {
  background: #0f172a;
  color: #e2e8f0;
  border: 1px solid rgba(34, 211, 238, 0.7);
  border-radius: 999px;
  padding: 2px 10px;
  font-family: 'JetBrains Mono';
  font-size: 11px;
  letter-spacing: 1px;
}
```

## 7. Iconografia

- Linha fina (1.5–2 px), cantos levemente arredondados.
- Cor padrão: `text.muted`. Em hover/ativo: `accent.light` com glow.
- Tamanhos canônicos: **16 / 20 / 24 px**.

## 8. Estados

| Estado | Indicação visual |
|---|---|
| **Default** | Cor base, sem glow |
| **Hover** | Borda → `accent.light`, glow leve, transição 150ms |
| **Focus** | Borda 2 px `accent.light` + glow forte |
| **Pressed** | Background → `accent.deep`, sem glow |
| **Disabled** | Opacidade 50%, sem interação |
| **Error** | Borda `danger`, mensagem em `danger` 12px |

## 9. Conteúdo & tom

- Português direto, voz ativa, frases curtas.
- Labels em **MAIÚSCULAS** somente para eyebrows e badges.
- Erros: descrever **o que aconteceu** + **o que fazer**.
- Nunca usar gírias internas em mensagens visíveis ao usuário.

## 10. Checklist de revisão visual

Antes de aprovar uma tela nova, confirme:

- [ ] Usa apenas tokens do tema (zero hex hard-coded).
- [ ] Hierarquia tipográfica respeita a tabela da seção 3.
- [ ] Espaçamento múltiplo de 4 px.
- [ ] Estados de hover/focus/disabled implementados.
- [ ] Contraste de texto ≥ 4.5:1 sobre o fundo usado.
- [ ] Animações ≤ 200ms e somente em interação.
- [ ] Ícones consistentes (mesmo conjunto, mesma espessura).

---

<div align="right">
  <sub>Design System · v12.0 preview · Cyberpunk Neon</sub>
</div>
