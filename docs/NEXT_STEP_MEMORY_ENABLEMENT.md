# Próximo passo — habilitação real de memória no KakeleBot

Este guia é para sair do modo OCR-only e validar captura real por memória no `kakele.exe`.

## 1) Preencher offsets no perfil ativo

Arquivo: `profiles/<seu_perfil>.json`

```json
{
  "memory": {
    "enabled": true,
    "prefer_for_healing": true,
    "prefer_for_target": true,
    "prefer_for_cavebot": true,
    "process_name": "kakele.exe",
    "addresses": {
      "hp": "0x...",
      "max_hp": "0x...",
      "mp": "0x...",
      "max_mp": "0x...",
      "x": "0x...",
      "y": "0x...",
      "z": "0x...",
      "has_target": "0x...",
      "target_id": "0x..."
    }
  }
}
```

## 2) Rodar health-check de memória

Com o client do jogo aberto e logado:

```bash
kakelebot-memory-check
```

Saída esperada:
- `memory check: OK`
- valores de hp/mp/posição/target sendo impressos.

## 3) Validar no GUI

Inicie:

```bash
kakelebot-gui
```

No painel de diagnóstico, confirme que o campo de target mostra:
- `source=memory-*`
- `memory=memory-ok:kakele.exe`
- `pos=(x,y,z)` atualizando.

## 4) GO/NO-GO objetivo

GO:
- `kakelebot-memory-check` retorna OK por 3 execuções seguidas.
- heal e target executam sem depender de OCR em combate básico.
- cavebot move com recuperação de stuck quando posição não progride.

NO-GO:
- erro de leitura de memória recorrente.
- hp/mp incompatível com UI do jogo.
- posição/target estáticos ou claramente incorretos.
