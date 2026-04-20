# Análise técnica — QoL (Heal/Target/Cavebot) e captura via memória

## 1) Objetivo do produto (contexto)

Esta análise consolida um plano técnico para o **software de auxílio** do Kakele focado em público casual, com três pilares:

1. **Heal** (vida/mana com regras configuráveis)
2. **Target/combat** (seleção de alvo, skills, prioridades e janelas de execução)
3. **Cavebot** (rotas para farm idle com segurança)

Além disso, considera a evolução desejada para **captura de estado do jogo via memória** (e posterior integração no client oficial), reduzindo dependência de OCR/imagem.

---

## 2) Estado atual do projeto (diagnóstico real do repositório)

O repositório hoje possui **duas camadas históricas**:

- Camada legada (`main.py`, `system/*`, `forms/*`) fortemente baseada em OCR/screenshot e threads manuais.
- Camada “next-generation” (`src/kakelebot/*`) com arquitetura mais modular (core/features/ui) e já com sinais de prontidão para evolução de runtime.

### 2.1 Heal

- Legado: leitura de barras por screenshot + OCR com limiares configuráveis na UI.
- Next-gen: decisão de heal separada em `HealingService.evaluate(...)`, recebendo leituras e thresholds.

**Leitura técnica:** a separação da decisão (domínio) já está boa no next-gen; o gargalo é a fonte dos dados (ainda visual/OCR), que oscila por ROI, fonte e contraste.

### 2.2 Target / combate

- Já existem parâmetros importantes de combate no perfil (`attack_enabled`, `secondary_attack_*`, `target_confirmation_cycles`, `target_stability_window`, etc.).
- O runtime atual faz validação de alvo por observações recentes e reduz falso-positivo com janela de estabilidade.

**Leitura técnica:** a base para “prioridade de alvo” existe parcialmente (controle de estabilidade), mas ainda falta um **Targeting Engine** explícito com lista de prioridades por tipo de monstro/risco/distância.

### 2.3 Cavebot

- Há suporte para waypoints com direção/repetição (`HuntWaypoint`) e execução cíclica (`HuntRuntime.next_action`).
- O healing runtime já pausa deslocamento durante alvo válido e retoma depois.

**Leitura técnica:** o mecanismo atual é suficiente para rota linear casual, mas para robustez de farm idle faltam módulos formais de anti-stuck, recuperação e telemetria.

### 2.4 Memória

- Existe um esqueleto de `MemoryService` + `PlayerState` no core.
- O código atual indica intenção de usar um adapter (`read_all_offsets`) para offsets reais.

**Leitura técnica:** excelente ponto de partida. O projeto já está arquiteturalmente próximo de trocar OCR por memória sem quebrar todas as features.

---

## 3) Gap analysis (o que falta para cumprir o objetivo completo)

### 3.1 Gap de dados

Hoje o motor depende de visão para partes críticas (vida/mana/target). Para confiabilidade de idle prolongado, precisa de:

- fonte de verdade primária via memória;
- fallback visual opcional (somente quando memória não estiver disponível);
- validação cruzada (memória x visão) durante rollout para reduzir regressões.

### 3.2 Gap de modelagem de Target

Faltam entidades de domínio para:

- prioridade por criatura (nome/id),
- regras condicionais (ex.: fugir de elite quando HP < X),
- regras de skill por contexto (single target vs pack),
- prioridade por risco e proximidade.

### 3.3 Gap operacional de Cavebot

Faltam estados explícitos de navegação:

- `IDLE`, `MOVING`, `ENGAGED`, `STUCK_RECOVERY`, `LOOTING`, `BANKING` (futuro);
- watchdog temporal (tempo máximo sem progresso);
- estratégia de recuperação por múltiplas tentativas.

### 3.4 Gap de observabilidade

Para um recurso “deixar caçando sozinho” em público casual, é essencial explicar “por que fez X”.
Faltam eventos estruturados para auditoria de decisão:

- snapshot de estado (HP/MP/posição/alvo),
- decisão tomada,
- ação emitida,
- resultado esperado vs observado.

---

## 4) Arquitetura recomendada (target architecture)

## 4.1 Princípio central

Introduzir um **GameStateProvider** com múltiplas fontes:

- `MemoryGameStateProvider` (primário)
- `VisionGameStateProvider` (fallback)
- `HybridGameStateProvider` (cross-check no rollout)

Todos os módulos (heal/target/cavebot) passam a consumir um `GameState` único.

### 4.2 Contrato de estado (mínimo)

```text
GameState
- tick_time
- player: hp, max_hp, mp, max_mp, level, exp
- position: x, y, z
- combat: has_target, target_id, target_name, target_hp_pct, targets_nearby[]
- context: is_in_combat, is_dead, is_channeling, bag_capacity, overweight
- telemetry: source(memory|vision|hybrid), confidence
```

### 4.3 Estratégia de integração por fases

**Fase 1 (Shadow Read):**
- leitura de memória sem dirigir ações;
- comparar com OCR e registrar desvio.

**Fase 2 (Soft Switch):**
- heal guiado por memória, target/hunt ainda híbrido;
- fallback automático para OCR se leitura inválida.

**Fase 3 (Memory-first):**
- todas as decisões por memória;
- OCR restrito a diagnóstico/observabilidade.

**Fase 4 (Client-integrated):**
- quando integrar no client, substituir leitura externa por API/bridge interna, mantendo o mesmo contrato `GameStateProvider`.

---

## 5) Especificação funcional por pilar

## 5.1 Heal (vida e mana)

### Regras recomendadas

- limiar por porcentagem (já existe no perfil) + histerese para evitar spam;
- cooldown por skill;
- prioridade: vida > mana quando ambos disparam no mesmo ciclo;
- bloqueio de cast em estados inválidos (stun/silence/canalizando, quando disponível em memória).

### Indicadores de qualidade

- tempo médio para reação a queda de HP;
- taxa de overheal;
- taxa de falha de cast por cooldown incorreto.

## 5.2 Target / combate

### Modelo recomendado

1. **Target Selector**: escolhe alvo por score (`risco`, `distância`, `prioridade configurada`, `hp restante`).
2. **Combat Planner**: decide skill/hotkey por contexto.
3. **Action Dispatcher**: emite tecla com rate limiting.

### Regras essenciais

- whitelist/blacklist de criaturas;
- prioridade por lista ordenada;
- skill de abertura, skill de execução e skill defensiva;
- fallback para “space attack” quando não houver skill válida.

## 5.3 Cavebot

### Modelo recomendado

- rota composta por waypoints com metadados:
  - `direction/repeats` (compatível atual),
  - opcionalmente `wait_ms`, `must_have_target=false`, `safe_radius`, `action_on_arrival`.

### Robustez mínima

- detector de “sem progresso” (posição não muda por N ciclos);
- recuperação escalonada:
  1) repetir movimento,
  2) passo lateral,
  3) mini-retrocesso,
  4) pausa e alerta.

---

## 6) Segurança técnica e produto

- Adotar **feature flags** por módulo (`memory_heal_enabled`, `memory_target_enabled`, `memory_hunt_enabled`).
- Guardrails de sessão:
  - limite de ações/minuto,
  - pausa automática em inconsistência de estado,
  - “stop all” por hotkey global.
- Logs estruturados (JSONL) para suporte e tuning de perfil.

---

## 7) Plano de implementação sugerido (incremental)

## Sprint A — Base de memória confiável

- Implementar adapter real para `MemoryService`.
- Validar offsets por versão/build do client.
- Criar `MemoryHealthCheck` (assinatura de processo, leitura mínima válida, latência).

## Sprint B — Heal memory-first

- Migrar decisão de heal para `GameStateProvider` híbrido.
- Manter OCR como fallback transparente.
- Criar painel simples de “fonte atual do dado” (memory/vision).

## Sprint C — Targeting Engine

- Introduzir configuração de prioridades (UI + profile JSON).
- Implementar score de alvo.
- Integrar planner de skills com cooldown/condição.

## Sprint D — Cavebot resiliente

- Adicionar detector de stuck por posição em memória.
- Implementar recuperação em camadas.
- Expor métricas de rota (loops, stuck_count, recoveries).

## Sprint E — Hardening e rollout

- Testes de soak (4h/8h/12h).
- Comparativo de eficácia (OCR vs memória).
- Deploy gradual por feature flag.

---

## 8) Matriz de riscos e mitigação

1. **Offsets quebram a cada update do jogo**
   - Mitigação: versionar tabela de offsets por build e health-check de inicialização.

2. **Leitura inconsistente/intermitente**
   - Mitigação: validação por janela temporal + fallback visual automático.

3. **Ações erradas em estado ambíguo**
   - Mitigação: confidence gating (não agir com confiança baixa).

4. **Travamento de rota (stuck)**
   - Mitigação: watchdog de progresso + recovery.

5. **Complexidade de suporte para usuários casuais**
   - Mitigação: presets prontos por classe/nível + explicações no painel de decisão.

---

## 9) KPIs para aceitar a evolução

- **Heal**: > 99% de ciclos com leitura válida de HP/MP (memória) em sessão estável.
- **Target**: redução de troca indevida de alvo em pelo menos 60% vs baseline OCR.
- **Cavebot**: taxa de stuck não recuperado < 1 por hora.
- **Experiência casual**: sessão de 4h sem intervenção manual em cenário de farm padrão.

---

## 10) Conclusão executiva

O projeto já contém fundamentos técnicos importantes para esse roadmap:

- modularidade no next-gen,
- runtime de heal/hunt já separados,
- configuração persistente por perfil,
- esqueleto de serviço de memória.

Com um **GameStateProvider memory-first**, um **Targeting Engine de prioridades** e um **Cavebot com recuperação de stuck**, o software consegue cumprir a proposta de valor casual (jogar no tempo livre e automatizar tarefas repetitivas no tempo ocupado) com qualidade operacional significativamente maior.
