# Nexor — Documentation Alignment Review

## Objetivo

Este documento revisa o conjunto atual da documentação do Nexor para garantir consistência entre:

* README
* Architecture
* Roadmap

O foco aqui é alinhar terminologia, escopo, prioridade, identidade do produto e linguagem, reduzindo repetições e evitando ambiguidades antes da próxima rodada de refinamento.

---

## 1. Diagnóstico geral

O conjunto atual já está coerente em direção estratégica.

Os três documentos convergem em pontos importantes:

* Nexor como plataforma operacional de produção têxtil
* abordagem local-first
* fechamento de rolos como núcleo operacional
* crescimento por camadas
* separação entre operação, cadastros, consulta, planejamento, estoque e analytics
* expansão híbrida como fase posterior

Isso é positivo, porque evita que cada documento conte uma história diferente.

### Porém, ainda existem pontos a ajustar

* repetição excessiva de certas definições
* mistura entre linguagem de produto e linguagem técnica
* alternância entre português e inglês nos títulos dos documentos
* alguns termos ainda podem ser mais padronizados
* o README ainda pode ficar mais enxuto para uso real em repositório
* a Architecture pode ficar mais objetiva em alguns trechos
* o Roadmap pode ficar mais executivo e menos explicativo em certas seções

---

## 2. Problema principal identificado

O maior risco atual não é contradição grave.
O maior risco é **redundância**.

A documentação já está bem posicionada, mas alguns blocos repetem a mesma ideia com pequenas variações:

* Nexor não é um hub genérico
* Nexor é local-first
* o rolo é uma entidade central
* crescimento por camadas
* online entra depois

Essas ideias são corretas, mas aparecem muitas vezes.

### Impacto disso

* o README pode ficar mais longo do que precisa
* a leitura pode parecer menos objetiva
* a diferenciação entre os papéis de cada documento pode enfraquecer

### Regra recomendada

Cada documento deve ter uma função dominante:

* **README** = visão do produto e escopo geral
* **Architecture** = estrutura técnica e modelo de camadas
* **Roadmap** = ordem de evolução e prioridades

Se cada documento começar a explicar tudo de novo, eles perdem nitidez.

---

## 3. Padronização de naming

### 3.1 Nome do produto

Usar sempre:

* **Nexor**

Evitar variações desnecessárias ou misturas com nomes antigos quando não houver contexto histórico.

---

### 3.2 Termos centrais recomendados

Padronizar estes termos como vocabulário oficial:

* **log** = entrada bruta operacional
* **job** = evento normalizado de produção
* **roll / rolo** = unidade operacional fechada
* **operator / operador**
* **machine / máquina**
* **fabric / tecido**
* **inventory / estoque**
* **production planning / planejamento de produção**
* **historical search / consulta histórica**
* **audit / auditoria**
* **local-first** = manter como termo estratégico
* **hybrid evolution** ou **evolução híbrida** = usar de forma consistente

---

### 3.3 Decisão de idioma

Hoje há uma mistura intencional:

* README em português
* Architecture em inglês
* Roadmap em português

Isso pode funcionar, mas precisa ser uma decisão explícita.

### Caminhos possíveis

#### Opção A — Repositório bilíngue por função

* README em português
* Architecture em inglês
* Roadmap em português

Funciona se o objetivo for:

* comunicação mais próxima com sua realidade operacional
* documentação técnica mais internacionalizada

#### Opção B — Tudo em português

Melhor para consistência local.

#### Opção C — Tudo em inglês

Melhor para posicionamento técnico externo.

### Recomendação atual

A mistura só vale a pena se for deliberada.
Se não houver motivo estratégico forte, o ideal é unificar.

Como o contexto real do produto, operação e uso ainda é local, a opção mais coerente agora parece ser:

**README + Roadmap em português, Architecture em inglês apenas se você quiser marcar uma camada técnica mais formal.**

---

## 4. Ajustes recomendados no README

### O que está bom

* posicionamento do produto está claro
* escopo macro está bem definido
* diferenciação entre o que entra e o que não entra dos PX ficou boa
* princípios do produto estão consistentes
* fluxo principal está bem explicado

### O que pode melhorar

#### 4.1 Enxugar blocos repetidos

O README não precisa repetir em tantos pontos que o Nexor não é Jocasta 2 nem hub genérico.
Basta afirmar isso com força uma vez.

#### 4.2 Tornar a seção de escopo mais visual

Em vez de explicar demais cada domínio, pode ser melhor resumir em blocos mais curtos.

#### 4.3 Separar melhor “visão” de “implementação”

O README está correto, mas começa a entrar em detalhes que já pertencem à Architecture e ao Roadmap.

### Recomendação prática

O README pode ser refinado para ficar mais próximo deste formato:

* visão
* problema
* proposta
* referências herdadas
* domínios do produto
* fluxo central
* direção arquitetural resumida
* roadmap resumido

Isso deixaria o documento mais forte como porta de entrada do repositório.

---

## 5. Ajustes recomendados na Architecture

### O que está bom

* camadas bem separadas
* domínios coerentes
* entidades centrais claras
* fluxo de dados consistente
* preparação para modelo híbrido bem posicionada

### O que pode melhorar

#### 5.1 Reduzir tom excessivamente explicativo

Alguns trechos explicam decisões que já estão maduras. A Architecture pode ser mais seca e estrutural.

#### 5.2 Deixar explícito o papel do banco local

A estratégia de persistência está boa, mas pode valer reforçar o papel do banco local como source of truth inicial.

#### 5.3 Refinar a separação entre Log e Job

Esse ponto é importante e pode ser ainda mais enfatizado, porque é um dos alicerces do sistema.

### Recomendação prática

A Architecture deve privilegiar:

* camadas
* domínios
* entidades
* fluxos
* estados
* serviços
* persistência
* infraestrutura

Menos manifesto, mais estrutura.

---

## 6. Ajustes recomendados no Roadmap

### O que está bom

* sequência das fases está lógica
* prioridades estão corretas
* dependências entre fases estão claras
* não há salto prematuro para online, estoque ou analytics

### O que pode melhorar

#### 6.1 Tornar a leitura mais executiva

Algumas fases podem ser descritas com menos texto e mais nitidez.

#### 6.2 Diferenciar melhor “fase” de “entrega”

Hoje está bom, mas pode ficar ainda mais claro quais são os marcos concretos.

#### 6.3 Criar no futuro uma visão de milestones

O Roadmap atual está ótimo como documento estratégico. Depois, pode valer gerar uma versão mais prática com:

* milestone
* objetivo
* entregas
* status

### Recomendação prática

Manter este Roadmap como visão estratégica e, depois, derivar um roadmap operacional de implementação.

---

## 7. Termos que devem ser travados

Para evitar ambiguidade futura, estes termos devem ser tratados como oficiais:

### Produto

* plataforma operacional de produção têxtil

### Núcleo

* núcleo operacional

### Fluxo central

* leitura de logs
* normalização em jobs
* montagem e fechamento de rolos
* exportação
* consulta histórica

### Camadas superiores

* cadastros
* planejamento de produção
* estoque
* analytics
* evolução híbrida

### Estratégia técnica

* local-first
* instalável
* expansão híbrida posterior

---

## 8. O que ainda falta no conjunto documental

Os três documentos atuais já formam uma boa base, mas ainda faltam alguns complementos naturais.

### Próximos documentos recomendados

#### 8.1 UI/UX Specification

Para transformar estratégia em navegação e experiência real.

Deveria conter:

* mapa de navegação
* telas principais
* fluxo do operador
* fluxo do gestor
* fluxo do admin
* hierarquia de ações
* componentes de dashboard

#### 8.2 Data Model

Para detalhar entidades, campos, relacionamentos e estados de forma mais técnica.

#### 8.3 Functional Specification

Para descrever regras de negócio por módulo ou domínio.

#### 8.4 Installation & Deployment

Para preparar o caminho do modo instalável.

---

## 9. Conclusão crítica

A base documental atual já é forte o suficiente para orientar a próxima etapa do projeto.

O principal cuidado agora não é inventar mais conceitos.
É **consolidar, enxugar e transformar a direção atual em documentação cada vez mais operacional e acionável**.

### Leitura honesta

O conjunto atual não está fraco.
Mas ainda está mais próximo de uma formulação estratégica do que de um pacote totalmente pronto para desenvolvimento guiado por documentação.

Isso não é um defeito.
Apenas indica o próximo passo natural.

---

## 10. Próxima ação recomendada

A próxima etapa mais coerente após esta revisão é criar:

**Nexor — UI/UX Specification**

Porque agora já existem bases suficientes para responder com clareza:

* quem usa
* para fazer o quê
* em qual ordem
* em quais telas
* com quais prioridades visuais e operacionais

### Síntese final

**README, Architecture e Roadmap já estão alinhados o bastante para sustentar a próxima camada: especificação de interface e fluxo.**
