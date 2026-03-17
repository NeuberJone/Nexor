# Nexor — Wireframe Specification

## 1. Objetivo

Este documento traduz a UI/UX Specification em estrutura visual de telas.

O foco aqui não é identidade gráfica final, mas sim:

* distribuição dos blocos
* hierarquia visual
* prioridade das ações
* organização do conteúdo
* leitura operacional

Os wireframes devem validar se a interface faz sentido antes de entrar em design refinado ou implementação visual.

---

## 2. Regras gerais de wireframe

### 2.1 Estrutura base da aplicação

Layout principal sugerido:

* barra lateral esquerda para navegação principal
* topo com título da seção, contexto atual e ações secundárias
* área central como conteúdo dominante
* painéis laterais apenas quando agregarem contexto útil

### 2.2 Lógica visual global

* o conteúdo principal sempre deve ocupar o maior espaço
* a ação principal da tela deve ser óbvia
* resumos e totais devem ficar visíveis sem competir com a lista principal
* filtros devem ficar próximos da lista que afetam
* painéis laterais devem mostrar contexto, não duplicar informação

### 2.3 Padrão de navegação

Menu lateral com:

* Home
* Operação
* Rolos
* Planejamento
* Estoque
* Cadastros
* Configurações

---

## 3. Wireframe da Home

## 3.1 Objetivo

Ser um painel operacional simples que responda imediatamente o que está acontecendo agora.

## 3.2 Estrutura sugerida

### Topo

* título: Home
* subtítulo curto com status do sistema
* ação rápida destacada: **Novo fechamento de rolo**

### Corpo

Distribuição em cards/blocos:

#### Linha 1

* **Logs novos encontrados**
* **Rolos em aberto**
* **Último rolo fechado**
* **Alertas / suspeitas**

#### Linha 2

* bloco maior: **Ações rápidas**

  * ir para Operação
  * consultar rolos
  * abrir Planejamento
  * abrir Estoque

#### Linha 3

* bloco largo: **Resumo operacional recente**

  * últimos registros ou eventos recentes

## 3.3 Prioridade visual

* maior destaque para o botão de novo fechamento
* segundo maior destaque para alertas e rolos em aberto
* resumos recentes com peso visual menor

---

## 4. Wireframe da tela Operação

## 4.1 Objetivo

Permitir que o operador selecione os itens do rolo atual com clareza e rapidez.

## 4.2 Estrutura sugerida

### Topo

* título: Operação
* subtítulo com quantidade de itens disponíveis
* ações secundárias:

  * atualizar lista
  * limpar filtros

### Corpo em 3 zonas

#### Zona A — Filtros superiores

Barra horizontal com:

* máquina
* tecido
* status
* período
* busca textual

#### Zona B — Lista principal (centro, maior área)

Tabela/lista com colunas como:

* seleção
* job / nome
* máquina
* tecido
* data/hora
* metragem
* status

#### Zona C — Painel lateral direito: Rolo em montagem

Conteúdo:

* título: Rolo atual
* quantidade de itens selecionados
* total em metros
* máquina
* tecido
* observações curtas
* ações:

  * revisar rolo
  * limpar seleção
  * avançar para fechamento

## 4.3 Comportamento esperado

* selecionar item atualiza o resumo lateral em tempo real
* estados visíveis com badge + texto
* painel lateral sempre visível durante a montagem

## 4.4 Prioridade visual

* lista principal domina a tela
* painel lateral é o segundo foco
* filtros são compactos e sempre visíveis

---

## 5. Wireframe da tela Fechamento do Rolo

## 5.1 Objetivo

Transformar a seleção atual em um registro confirmado.

## 5.2 Estrutura sugerida

### Topo

* título: Fechamento do Rolo
* indicador resumido do total de itens e metragem

### Corpo em duas colunas

#### Coluna esquerda — Dados e revisão

* identificação do rolo
* máquina
* tecido
* operador
* observações
* outros campos necessários

#### Coluna direita — Resumo consolidado

* total de jobs
* total consumido
* total impresso
* gaps
* status do fechamento

### Rodapé fixo de ações

* voltar para montagem
* salvar como rascunho, se existir esse conceito
* confirmar fechamento
* fechar e exportar

## 5.3 Faixa inferior opcional

* lista resumida dos itens vinculados

## 5.4 Prioridade visual

* ações finais sempre fáceis de localizar
* resumo consolidado deve dar segurança ao usuário antes de confirmar

---

## 6. Wireframe da tela Rolos

## 6.1 Objetivo

Consultar rapidamente registros já fechados.

## 6.2 Estrutura sugerida

### Topo

* título: Rolos
* busca principal
* filtros rápidos

### Corpo em duas áreas principais

#### Área A — Lista de resultados (lado esquerdo / centro)

Tabela com:

* identificação
* data
* máquina
* tecido
* operador
* total em metros
* status

#### Área B — Painel de detalhe (lado direito)

Ao selecionar um rolo, exibir:

* dados gerais
* observações
* jobs vinculados
* ações de exportação
* histórico futuro, se houver

### Faixa de filtros acima da lista

* período
* máquina
* tecido
* operador
* status

## 6.3 Prioridade visual

* busca e lista dominam
* detalhes aparecem sem exigir nova navegação

---

## 7. Wireframe da tela Planejamento

## 7.1 Objetivo

Montar a fila futura sem misturar com operação real já fechada.

## 7.2 Estrutura sugerida

### Topo

* título: Planejamento
* ação principal: gerar / revisar planejamento

### Corpo em três zonas

#### Zona A — Itens planejáveis

Lista de jobs ou grupos disponíveis para planejar

#### Zona B — Regras e parâmetros

Painel com:

* tecido
* capacidade do rolo
* gaps
* ordem
* estimativa

#### Zona C — Resultado / fila montada

Visual em lista ou blocos com:

* segmentos
* totais
* tempo estimado
* observações

## 7.3 Prioridade visual

* resultado do planejamento deve ganhar destaque depois de gerado
* parâmetros não devem esmagar a área principal

---

## 8. Wireframe da tela Estoque

## 8.1 Objetivo

Mostrar disponibilidade de material de forma clara e prática.

## 8.2 Estrutura sugerida

### Topo

* título: Estoque
* ação principal: novo item

### Corpo

#### Linha superior

* cards de resumo:

  * total de itens
  * tecidos com saldo
  * itens críticos ou baixos

#### Área principal

Tabela com:

* tecido
* tipo do item
* metragem disponível
* status
* observações

#### Painel lateral opcional

* detalhe do item selecionado
* histórico simples ou vínculo com uso futuro

### Faixa de filtros

* tecido
* tipo
* status
* disponibilidade

---

## 9. Wireframe da tela Cadastros

## 9.1 Objetivo

Centralizar manutenção de dados de apoio sem poluir a operação.

## 9.2 Estrutura sugerida

### Topo

* título: Cadastros

### Navegação interna por abas ou submenu

* Operadores
* Máquinas
* Tecidos
* Aliases

### Corpo padrão para cada cadastro

#### Faixa superior

* busca
* filtros simples
* botão novo cadastro

#### Área principal

Tabela/lista de registros

#### Painel lateral ou modal

* criação/edição do item selecionado

## 9.3 Prioridade visual

* lista e busca primeiro
* formulário aparece como contexto, não como tela pesada

---

## 10. Wireframe da tela Configurações

## 10.1 Objetivo

Concentrar parâmetros estruturais do sistema.

## 10.2 Estrutura sugerida

### Topo

* título: Configurações

### Navegação interna por seções

* Geral
* Pastas
* Exportações
* Parâmetros
* Futuro sync/backup

### Corpo

#### Seção exemplo: Pastas

* origem dos logs
* exportação PDF
* exportação JPG mirror
* validação dos caminhos

#### Seção exemplo: Geral

* comportamento do sistema
* padrões operacionais
* defaults

### Rodapé de ações

* salvar alterações
* restaurar padrão, se fizer sentido
* testar caminhos, quando aplicável

---

## 11. Fluxo visual do operador

Fluxo recomendado entre telas:

Home  →  Operação  →  Fechamento do Rolo  →  Exportação concluída

### Regras do fluxo

* a Home deve levar o operador direto para Operação
* Operação deve levar naturalmente ao Fechamento
* após fechar, o sistema deve mostrar sucesso e caminho para consultar o rolo

---

## 12. Fluxo visual da conferência

Rolos  →  Selecionar registro  →  Ver detalhe  →  Reexportar / revisar

### Regra

Esse fluxo deve depender do menor número possível de telas separadas.

---

## 13. Fluxo visual da administração

Cadastros / Configurações  →  Ajustar item  →  Salvar  →  Voltar ao contexto

### Regra

A manutenção do sistema deve ser previsível e sem labirintos.

---

## 14. Estados que precisam aparecer visualmente

Os wireframes devem prever espaço visual para:

* badges de status
* mensagens de validação
* alertas de suspeita
* empty states
* loading states
* confirmação de sucesso
* erro técnico ou de configuração

Esses estados não são detalhe; eles fazem parte da experiência real.

---

## 15. Decisões de hierarquia visual

### Sempre destacar

* ação principal da tela
* total ou resumo mais importante
* alertas relevantes
* contexto do item selecionado

### Sempre reduzir visualmente

* ações secundárias
* filtros avançados
* informação histórica não essencial na tarefa atual

---

## 16. O que testar com esses wireframes

Antes de avançar para front, os wireframes devem responder:

* a Home mostra claramente por onde começar?
* a tela de Operação está simples ou já ficou pesada demais?
* o painel lateral do rolo ajuda ou atrapalha?
* o Fechamento transmite segurança?
* a tela de Rolos permite consulta rápida de verdade?
* Cadastros e Configurações estão fora do caminho da operação?
* Planejamento e Estoque parecem áreas próprias, sem poluir o fluxo principal?

---

## 17. Próximo desdobramento recomendado

Depois desta especificação de wireframes, os próximos passos naturais são:

* rascunho visual de baixa fidelidade
* design system básico
* functional specification por tela
* protótipo navegável

---

## 18. Síntese final

Os wireframes do Nexor devem confirmar uma arquitetura visual baseada em domínio, com foco no fluxo operacional e em uma navegação simples, previsível e fácil de usar.

### Definição final

**Wireframe do Nexor = estrutura clara + ação principal evidente + contexto visível + baixa fricção + separação entre operação, consulta, planejamento, estoque e administração.**
