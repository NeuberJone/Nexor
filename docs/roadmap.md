# Nexor — Roadmap

## 1. Propósito do roadmap

Este roadmap organiza a evolução do Nexor de forma coerente com sua definição atual:

* plataforma operacional de produção têxtil
* foco local-first
* rastreabilidade real
* fechamento de rolos como núcleo operacional
* crescimento por camadas
* evolução futura para planejamento, estoque, analytics e arquitetura híbrida

A lógica do roadmap não é adicionar recursos de forma aleatória, mas construir o sistema por maturidade.

---

## 2. Direção estratégica

O Nexor deve crescer em etapas que respeitem a dependência entre os domínios.

### Regra central

Primeiro, consolidar o **núcleo operacional**.
Depois, expandir para **cadastros**, **consulta**, **planejamento**, **estoque**, **analytics** e **serviços híbridos**.

### O que isso evita

* UI bonita sobre base instável
* estoque sem dados operacionais confiáveis
* planejamento desconectado da produção real
* sincronização online antes da maturidade local
* acúmulo de módulos sem espinha dorsal de domínio

---

## 3. Macro fases do produto

### Fase 1 — Base operacional confiável

Objetivo:
Construir a fundação técnica e conceitual do Nexor.

### Fase 2 — Fechamento de rolos

Objetivo:
Transformar logs e jobs em registros operacionais consolidados.

### Fase 3 — Cadastros estruturados

Objetivo:
Dar suporte estável à rastreabilidade e padronização.

### Fase 4 — Consulta e auditoria

Objetivo:
Permitir busca, revisão e reexportação de registros.

### Fase 5 — Planejamento de produção

Objetivo:
Organizar a fila antes da execução com base nos dados reais.

### Fase 6 — Estoque

Objetivo:
Conectar disponibilidade de tecido ao sistema operacional.

### Fase 7 — Analytics

Objetivo:
Transformar produção em métricas e apoio à decisão.

### Fase 8 — Evolução híbrida

Objetivo:
Expandir o Nexor para sincronização, backup e operação distribuída sem perder a confiabilidade local.

---

## 4. Fase 1 — Base operacional confiável

### Objetivo principal

Estabilizar o modelo de produção e garantir que logs, jobs, métricas e regras centrais estejam corretos e consistentes.

### Entregas principais

* ingestão de logs
* parsing e normalização
* modelo consistente de job
* persistência local sólida
* alinhamento entre banco, models, mapper e repositórios
* métricas corrigidas
* classificação e status operacionais
* unificação das regras de suspeita

### Resultado esperado

O Nexor deixa de ser apenas um experimento técnico e passa a ter um núcleo confiável para crescer.

### Critério de saída da fase

* logs válidos viram jobs corretamente
* métricas principais estão coerentes
* status e classificações seguem regra única
* persistência funciona sem inconsistência estrutural

---

## 5. Fase 2 — Fechamento de rolos

### Objetivo principal

Criar o fluxo central do produto: transformar eventos operacionais em rolos fechados, auditáveis e exportáveis.

### Entregas principais

* leitura automática da pasta configurada de logs
* inbox operacional com lista de logs/jobs elegíveis
* estados visíveis dos itens
* seleção dos jobs do rolo atual
* resumo consolidado do rolo em montagem
* fechamento estruturado do rolo
* persistência do rolo e vínculos
* exportação em PDF
* exportação em JPG mirror

### Resultado esperado

O Nexor passa a representar um ciclo operacional real de produção.

### Critério de saída da fase

* é possível montar e fechar um rolo completo no sistema
* jobs ficam corretamente vinculados ao rolo
* exportações são geradas com base em dados persistidos
* o fluxo pode ser repetido com segurança

---

## 6. Fase 3 — Cadastros estruturados

### Objetivo principal

Adicionar base de referência confiável para enriquecer a operação.

### Entregas principais

* cadastro de operadores
* cadastro de máquinas
* cadastro de tecidos
* aliases e normalização de nomes de tecido
* parâmetros auxiliares operacionais
* configuração inicial mais clara

### Resultado esperado

A rastreabilidade melhora e o sistema reduz dependência de texto solto ou convenções implícitas.

### Critério de saída da fase

* operadores, máquinas e tecidos podem ser mantidos no sistema
* a operação usa essas referências de forma consistente
* aliases reduzem problemas de nomenclatura

---

## 7. Fase 4 — Consulta e auditoria

### Objetivo principal

Dar visibilidade histórica e capacidade de revisão aos registros já consolidados.

### Entregas principais

* tela de consulta de rolos registrados
* filtros por data, tecido, máquina, operador e status
* visualização de detalhes do rolo
* reconstrução dos jobs vinculados
* reexportação de PDF e JPG mirror
* revisão de inconsistências e suspeitas
* base para trilha de auditoria futura

### Resultado esperado

O Nexor deixa de ser apenas um ponto de entrada e passa a ser também uma base de consulta confiável.

### Critério de saída da fase

* é possível encontrar rapidamente um rolo registrado
* o detalhe mostra a composição do registro
* relatórios podem ser recuperados sem retrabalho manual

---

## 8. Fase 5 — Planejamento de produção

### Objetivo principal

Levar o Nexor da operação reativa para preparação estruturada da execução.

### Entregas principais

* fila de produção
* agrupamento por tecido
* ordenação operacional
* controle de capacidade por rolo
* definição de gaps
* estimativa de tempo
* preparação de blocos ou lotes de produção
* aproveitamento futuro com base em lógica mais inteligente

### Resultado esperado

O sistema passa a apoiar decisões antes da produção, e não apenas depois dela.

### Critério de saída da fase

* é possível montar uma fila coerente com base em tecido e capacidade
* o sistema gera estimativas úteis para a operação
* planejamento e operação passam a conversar entre si

---

## 9. Fase 6 — Estoque

### Objetivo principal

Adicionar controle simples e útil de materiais, conectado ao contexto produtivo.

### Entregas principais

* cadastro de rolos de tecido
* cadastro de pedaços
* disponibilidade por tecido
* atualização de consumo após confirmação
* vínculo progressivo com planejamento
* preparação para melhor aproveitamento de material

### Resultado esperado

O Nexor passa a considerar não apenas o que foi produzido, mas também com o que é possível produzir.

### Critério de saída da fase

* saldo de materiais pode ser visualizado por tecido
* operação e planejamento conseguem consultar disponibilidade
* o sistema consegue refletir consumo confirmado

---

## 10. Fase 7 — Analytics

### Objetivo principal

Transformar o histórico operacional em informação gerencial e aprendizado do processo.

### Entregas principais

* produtividade por máquina
* duração média por metro
* comparação entre períodos
* padrões de consumo
* indicadores de eficiência
* alertas ou sinais de anomalia
* apoio futuro à melhoria contínua

### Resultado esperado

O Nexor passa a gerar inteligência operacional, e não apenas armazenamento de registros.

### Critério de saída da fase

* métricas principais são confiáveis e legíveis
* o sistema permite comparação histórica útil
* dados começam a apoiar decisões e ajustes de processo

---

## 11. Fase 8 — Evolução híbrida

### Objetivo principal

Expandir o produto para cenários mais amplos sem romper a confiabilidade local.

### Entregas principais

* monitoramento contínuo por agente local
* sincronização opcional
* backup remoto
* centralização de métricas
* consolidação entre estações ou máquinas
* base para atualizações e serviços distribuídos

### Resultado esperado

O Nexor mantém sua base local-first, mas passa a oferecer recursos de integração e continuidade operacional em escala maior.

### Critério de saída da fase

* o sistema continua funcional offline
* recursos híbridos são opcionais e controlados
* a expansão online não compromete o fluxo principal

---

## 12. Prioridade de implementação prática

### Prioridade imediata

Focar no que sustenta o produto:

* núcleo operacional
* regras de classificação
* fechamento de rolo
* persistência confiável

### Prioridade seguinte

Adicionar o que melhora a estrutura e a consulta:

* cadastros
* busca histórica
* reexportação

### Prioridade posterior

Expandir para camadas superiores:

* planejamento
* estoque
* analytics
* híbrido

### Regra de priorização

Nenhuma camada superior deve crescer em cima de uma base operacional inconsistente.

---

## 13. Dependências entre fases

O roadmap deve respeitar dependências claras.

### Dependências principais

* **Fase 2 depende da Fase 1**
* **Fase 3 depende da Fase 1 e fortalece a Fase 2**
* **Fase 4 depende da Fase 2**
* **Fase 5 depende da estabilidade de operação e cadastros**
* **Fase 6 depende de dados de tecidos e integração com planejamento/operação**
* **Fase 7 depende de histórico consistente**
* **Fase 8 depende de uma base local madura**

### Leitura importante

Planejamento, estoque e híbrido não devem ser tratados como “próximos recursos visuais”, mas como camadas que exigem fundação sólida.

---

## 14. Critérios de maturidade do produto

O roadmap não deve ser medido apenas por quantidade de features, mas por maturidade real.

### Sinais de maturidade

* dados consistentes
* fluxo reproduzível
* baixa fricção operacional
* rastreabilidade confiável
* exportações coerentes
* consulta histórica útil
* base estável para crescer

### Sinais de risco

* muitos recursos sem integração real
* UI avançando mais rápido que o modelo
* duplicação de lógica de negócio
* métricas contraditórias
* campos e cadastros criados sem papel claro no domínio

---

## 15. Roadmap resumido em visão executiva

### Fase 1

Base operacional confiável

### Fase 2

Fechamento de rolos

### Fase 3

Cadastros estruturados

### Fase 4

Consulta e auditoria

### Fase 5

Planejamento de produção

### Fase 6

Estoque

### Fase 7

Analytics

### Fase 8

Evolução híbrida local-first

---

## 16. Direção final do roadmap

O Nexor deve evoluir com disciplina de produto.

A construção começa no núcleo operacional, consolida o ciclo de vida do rolo, melhora rastreabilidade com cadastros e consulta, e só então avança com segurança para planejamento, estoque, analytics e expansão híbrida.

### Síntese

**O roadmap do Nexor deve seguir a ordem: operar bem, registrar bem, consultar bem, planejar melhor, controlar recursos e só então expandir o sistema além do posto local.**
