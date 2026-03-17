# Nexor

**Nexor** é uma plataforma operacional para produção têxtil, projetada para transformar eventos reais de produção em informação estruturada, auditável e útil para a rotina diária.

O projeto nasce com foco em **rastreamento operacional**, **fechamento de rolos**, **consulta histórica**, **planejamento de produção**, **cadastros estruturados**, **estoque** e **evolução para uma arquitetura híbrida local-first**.

---

## Visão do projeto

O Nexor não é um hub genérico de utilitários.
Ele foi concebido como uma plataforma de operação e inteligência de produção, atuando entre o planejamento e a execução.

Sua proposta é sair da lógica de ferramentas isoladas e consolidar um fluxo mais maduro, onde logs, jobs, rolos, máquinas, operadores, tecidos e planejamento passam a fazer parte de um mesmo sistema.

### Definição resumida

**Nexor = núcleo operacional de produção + cadastros estruturados + consulta auditável + planejamento + estoque + evolução híbrida local-first.**

---

## O que o Nexor é

* Uma base operacional para acompanhar a produção real
* Um sistema centrado em logs, jobs e rolos
* Uma plataforma com foco em rastreabilidade
* Uma estrutura preparada para crescer com planejamento, estoque e analytics
* Um produto pensado para uso local, intuitivo e instalável

## O que o Nexor não é

* Não é uma cópia do Jocasta
* Não é a absorção completa do ecossistema PX
* Não é apenas um leitor de logs
* Não é apenas uma tela bonita sobre dados soltos
* Não é um sistema dependente de internet para funcionar

---

## Referências de origem

O Nexor aproveita referências funcionais específicas do ecossistema PX, mas mantém identidade própria.

### Referências diretas

* **PXPrintLogs**
* **PXSearchOrders**
* **PXPrintCalc**

### Como essas referências entram no projeto

#### PXPrintLogs

Inspira:

* leitura operacional dos logs
* fluxo prático de produção
* exportações em PDF
* exportações em JPG mirror
* visão voltada ao uso real no ambiente produtivo

#### PXSearchOrders

Inspira:

* tela de consulta
* busca por registros já salvos
* conferência histórica
* recuperação e revisão de dados operacionais

#### PXPrintCalc

Inspira parcialmente:

* cálculos auxiliares
* lógica de metragem
* estimativas futuras para planejamento de produção

### Importante

O restante dos módulos PX/Jocasta **não entra automaticamente no Nexor**.
O projeto deve crescer com base no seu próprio domínio, não por acúmulo de módulos externos.

---

## Problema que o Nexor resolve

Em muitas rotinas produtivas, a informação existe, mas está fragmentada:

* logs ficam soltos em pastas
* o fechamento operacional depende de processos manuais
* a conferência de rolos não está centralizada
* histórico e reexportação exigem retrabalho
* planejamento e estoque ficam desconectados da execução

O Nexor busca resolver isso transformando a produção em um fluxo contínuo e estruturado.

---

## Objetivos do projeto

* Ler logs de produção de forma automática a partir de uma origem configurada
* Estruturar e consolidar jobs e rolos com rastreabilidade
* Permitir fechamento operacional de rolos com revisão e exportação
* Facilitar busca, auditoria e reexportação de registros
* Preparar base para planejamento de produção por tecido e capacidade
* Integrar futuramente estoque, analytics e sincronização híbrida

---

## Princípios do produto

### Operação primeiro

O Nexor deve priorizar o fluxo real da produção antes de buscar sofisticação visual ou excesso de recursos.

### Modelo antes da interface

A UI deve nascer do domínio e do fluxo do usuário, não de improviso visual.

### Local-first

A operação principal deve funcionar localmente, mesmo sem internet.

### Semi online por camadas

Recursos online entram como expansão futura, não como dependência do núcleo.

### Simplicidade operacional

Cada tela deve ter propósito claro, linguagem direta e poucos passos para concluir a ação principal.

### Produto instalável de verdade

O objetivo não é apenas empacotar scripts, mas entregar uma experiência de produto consistente.

---

## Escopo funcional

O Nexor deve ser organizado por domínios funcionais.

### 1. Operação

Fluxo diário da produção.

Inclui:

* leitura automática da pasta de logs
* listagem de logs encontrados
* status de processamento
* seleção dos logs que compõem um rolo
* revisão do rolo em montagem
* fechamento do rolo
* exportações em PDF e JPG mirror

### 2. Cadastros

Entidades de apoio do sistema.

Inclui:

* operadores
* máquinas / maquinário
* tecidos
* aliases de tecido
* configurações auxiliares

### 3. Consulta e auditoria

Histórico e rastreabilidade.

Inclui:

* busca de rolos registrados
* filtros por data, máquina, tecido, operador e status
* abertura dos detalhes do rolo
* visualização dos logs vinculados
* reexportação de relatórios
* revisão de inconsistências e suspeitas

### 4. Planejamento de produção

Organização da fila antes da execução.

Inclui:

* agrupamento por tecido
* controle de capacidade de rolos
* definição de gaps
* estimativa de tempo
* preparação de fila de impressão

### 5. Estoque

Controle simples de materiais.

Inclui:

* cadastro de rolos de tecido
* cadastro de pedaços
* disponibilidade por tecido
* atualização de consumo após confirmação

### 6. Analytics

Métricas e visão de desempenho.

Inclui:

* produtividade por máquina
* duração média por metro
* eficiência operacional
* histórico e padrões de produção

### 7. Configurações e evolução híbrida

Base para funcionamento local e expansão futura.

Inclui:

* pasta de origem dos logs
* pasta de exportação
* parâmetros operacionais
* sincronização futura
* backup futuro
* atualizações futuras

---

## Entidades centrais

O Nexor deve ser pensado em torno de entidades claras e persistentes.

### Entidades principais

* **Log**
* **Job**
* **Rolo**
* **Máquina**
* **Operador**
* **Tecido**
* **Item de estoque**
* **Plano de produção**

### Relação conceitual inicial

* O **log** é a entrada operacional bruta
* O **job** é o registro normalizado do evento de produção
* O **rolo** é a consolidação operacional de um conjunto de jobs/logs
* Máquina, operador e tecido enriquecem a rastreabilidade
* Estoque e planejamento se conectam ao núcleo após a base operacional estar estável

### Regra central

O Nexor deve ser modelado em torno do **ciclo de vida do rolo**, mas sem reduzir o sistema apenas a isso.

---

## Fluxo principal esperado

O fluxo principal da operação deve seguir uma lógica simples e objetiva:

1. O sistema lê automaticamente os logs a partir de uma origem configurada
2. Os logs encontrados são listados com status visíveis
3. O operador seleciona os logs que fazem parte do rolo atual
4. O sistema apresenta um resumo consolidado
5. O rolo é revisado, fechado e registrado
6. Os relatórios são exportados em PDF e JPG mirror
7. O rolo pode ser consultado, auditado e reexportado depois

---

## Direção de UI/UX

A interface do Nexor deve ser planejada para ser intuitiva, rápida e confiável.

### Princípios de UI

* uma ação principal por tela
* nomes claros e operacionais
* poucos cliques para tarefas frequentes
* status visíveis
* erros explicados em linguagem simples
* confirmações para ações sensíveis
* padrão visual consistente

### Regra prática

Se o operador abrir o sistema e não souber por onde começar em poucos segundos, a home está errada.

---

## Estrutura macro de telas

### Home operacional

Tela inicial com foco no que importa no momento.

Blocos sugeridos:

* logs novos encontrados
* rolos em aberto
* último rolo fechado
* alertas ou suspeitas
* atalho para novo fechamento de rolo
* atalho para consultar rolos
* acesso rápido a planejamento e estoque

### Inbox de logs / montagem do rolo

Tela principal da operação.

### Fechamento do rolo

Tela de confirmação e exportação.

### Consulta de rolos registrados

Tela inspirada conceitualmente no PXSearchOrders, adaptada ao domínio do Nexor.

### Planejamento

Tela separada da operação diária.

### Estoque

Tela separada e objetiva.

### Cadastros e configurações

Área administrativa do sistema.

---

## Estratégia local-first

A operação principal do Nexor deve funcionar localmente.

### Fase inicial

* banco local
* leitura de pasta local ou de rede
* exportações locais
* funcionamento independente de internet

### Expansão futura

O online deve entrar como camada complementar.

Possibilidades futuras:

* sincronização opcional
* backup remoto
* atualização remota
* centralização de métricas
* consolidação entre postos ou máquinas

### Regra arquitetural

A operação principal nunca deve depender da internet para funcionar.

---

## Estratégia de produto instalável

O Nexor deve nascer preparado para distribuição como produto instalável.

Isso implica:

* estrutura de diretórios previsível
* criação automática de banco local
* configuração inicial guiada
* validação de pastas
* mensagens de erro claras
* logs internos do sistema
* identidade visual consistente
* empacotamento estável
* caminho futuro para atualização

---

## Ordem de implementação recomendada

### Camada 1 — Núcleo operacional

* logs
* jobs
* rolos
* classificação e status
* persistência
* métricas básicas
* fechamento de rolo

### Camada 2 — Cadastros de apoio

* operadores
* máquinas
* tecidos
* aliases

### Camada 3 — Consulta e auditoria

* busca de rolos
* detalhe do rolo
* revisão de composição
* reexportação

### Camada 4 — Planejamento

* fila
* agrupamento por tecido
* estimativas
* rolos previstos
* gaps

### Camada 5 — Estoque

* rolos
* pedaços
* disponibilidade
* abatimento após confirmação

### Camada 6 — Evolução híbrida

* sincronização opcional
* backup
* centralização futura

---

## Roadmap resumido

### Fase 1 — Base operacional confiável

* ingestão e normalização de logs
* modelo consistente de job
* métricas corretas
* regra de suspeita unificada
* persistência sólida

### Fase 2 — Fechamento de rolos

* inbox de logs
* seleção dos logs do rolo
* estados de processamento
* fechamento estruturado
* PDF e JPG mirror

### Fase 3 — Cadastros e rastreabilidade ampliada

* operadores
* máquinas
* tecidos
* aliases

### Fase 4 — Consulta e auditoria

* busca de rolos
* filtros
* abertura de detalhes
* reexportação
* revisão histórica

### Fase 5 — Planejamento de produção

* fila por tecido
* estimativas
* capacidade de rolos
* gaps

### Fase 6 — Estoque

* rolos e pedaços
* disponibilidade por tecido
* integração com planejamento

### Fase 7 — Analytics

* produtividade
* eficiência
* padrões operacionais
* apoio à decisão

### Fase 8 — Evolução híbrida

* monitoramento contínuo por agente local
* sincronização opcional
* backup e centralização futura

---

## Estado do projeto

O Nexor está em construção, com foco atual na consolidação do núcleo operacional e do modelo de produção.

A prioridade neste momento é fortalecer a base antes de avançar para uma UI completa e para camadas mais altas como planejamento, estoque avançado e sincronização híbrida.

---

## Direção oficial

**O Nexor deve evoluir como uma plataforma operacional de produção têxtil, com base local confiável, fluxo intuitivo de uso diário, rastreabilidade real, camadas de planejamento e estoque, e expansão híbrida planejada com maturidade.**
