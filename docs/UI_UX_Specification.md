# Nexor — UI/UX Specification

## 1. Objetivo

Este documento define a direção de interface e experiência do usuário para o Nexor.

O objetivo não é apenas desenhar telas bonitas, mas estruturar uma interface operacional que seja:

* intuitiva
* rápida
* confiável
* fácil de aprender
* consistente com o domínio do produto
* adequada para uso diário em contexto real de produção

A UI do Nexor deve refletir o modelo do sistema, priorizando o fluxo operacional antes de qualquer complexidade visual desnecessária.

---

## 2. Princípios de UI/UX

### 2.1 Operação primeiro

A interface deve priorizar as tarefas mais frequentes e mais críticas da rotina.

### 2.2 Uma ação principal por tela

Cada tela precisa ter um objetivo dominante claro.

### 2.3 Menos fricção, mais confirmação

O sistema deve reduzir etapas desnecessárias, mas proteger ações sensíveis com validação e confirmação.

### 2.4 Informação visível

Status, totais, alertas e contexto não devem ficar escondidos.

### 2.5 Linguagem operacional

Os nomes, botões e mensagens devem usar termos diretos e compreensíveis no contexto de produção.

### 2.6 Consistência visual

A mesma lógica visual deve se repetir em todas as áreas do sistema.

### 2.7 Clareza acima de sofisticação

Uma UI elegante é desejável, mas nunca à custa da compreensão.

### 2.8 Local-first na experiência

A experiência principal deve ser sólida e completa mesmo offline.

---

## 3. Premissas de uso

O Nexor é um sistema operacional de uso recorrente.

Isso implica que a interface precisa funcionar bem para:

* uso repetitivo ao longo do dia
* consulta rápida
* baixa tolerância a erro operacional
* usuários com diferentes níveis de familiaridade com tecnologia
* cenários com pressão de tempo

Portanto, a experiência deve favorecer:

* leitura rápida
* ações claras
* pouco esforço cognitivo
* boa hierarquia visual
* baixa dependência de treinamento complexo

---

## 4. Perfis de usuário

A UI deve considerar, no mínimo, três perfis principais.

## 4.1 Operador

### Objetivo

Registrar e fechar a produção do dia de forma simples e segura.

### Necessidades principais

* ver logs pendentes
* montar o rolo atual
* revisar totais
* fechar rolo
* exportar relatórios
* identificar rapidamente o que está faltando ou pendente

### O que evitar para esse perfil

* excesso de opções administrativas
* telas confusas com muitos filtros avançados
* excesso de dados históricos na tela principal

---

## 4.2 Gestão / conferência

### Objetivo

Consultar histórico, revisar registros e acompanhar situação operacional.

### Necessidades principais

* buscar rolos registrados
* filtrar por período, tecido, máquina, operador e status
* abrir detalhes do rolo
* conferir composição
* reexportar relatórios
* identificar inconsistências

---

## 4.3 Administração

### Objetivo

Configurar e manter a base do sistema.

### Necessidades principais

* cadastrar operadores
* cadastrar máquinas
* cadastrar tecidos
* manter aliases
* ajustar parâmetros
* configurar pastas
* acessar áreas de estoque e parâmetros mais estruturais

### O que evitar para esse perfil

* esconder configurações críticas demais
* exigir caminhos indiretos para manutenção do sistema

---

## 5. Navegação principal

A navegação precisa refletir a hierarquia real do produto.

## 5.1 Estrutura principal recomendada

### Seções principais

* **Home**
* **Operação**
* **Rolos**
* **Planejamento**
* **Estoque**
* **Cadastros**
* **Configurações**

### Observação crítica

A navegação não deve começar por “módulos” genéricos. Ela deve começar por tarefas e domínios compreensíveis.

---

## 5.2 Lógica da navegação

### Home

Ponto de entrada e visão do momento atual.

### Operação

Fluxo do dia: logs, montagem e fechamento.

### Rolos

Consulta histórica, revisão e reexportação.

### Planejamento

Fila futura e preparação da produção.

### Estoque

Disponibilidade de tecido e materiais.

### Cadastros

Operadores, máquinas, tecidos e aliases.

### Configurações

Pastas, parâmetros, comportamento do sistema e recursos futuros.

---

## 6. Estrutura da Home

A Home deve ser operacional, não decorativa.

Ela deve responder rapidamente a perguntas como:

* o que chegou de novo?
* o que está pendente?
* o que foi fechado por último?
* há algo suspeito ou travado?
* qual é a ação principal agora?

## 6.1 Blocos recomendados

### Bloco 1 — Logs novos encontrados

Mostra quantidade e acesso rápido.

### Bloco 2 — Rolos em aberto

Mostra quantos estão em andamento ou aguardando fechamento.

### Bloco 3 — Último rolo fechado

Mostra identificação, horário e atalho para detalhe.

### Bloco 4 — Alertas / suspeitas

Mostra itens que exigem revisão.

### Bloco 5 — Atalho principal

Botão de destaque para:
**Novo fechamento de rolo**

### Bloco 6 — Acesso rápido

Atalhos para:

* consultar rolos
* planejamento
* estoque
* cadastros

---

## 6.2 Regra visual da Home

A ação principal da Home deve ser óbvia em poucos segundos.

Se houver muitos blocos do mesmo peso visual, a Home perde direção.

---

## 7. Tela de Operação

A tela de Operação é o centro da experiência do operador.

Ela precisa unir clareza, velocidade e segurança.

## 7.1 Objetivo da tela

Transformar logs/jobs disponíveis em um rolo estruturado e fechável.

## 7.2 Estrutura recomendada

### Área A — Lista principal de itens disponíveis

Exibe logs/jobs elegíveis.

Informações úteis por linha:

* nome do job
* máquina
* tecido
* data/hora
* metragem relevante
* status

### Área B — Filtros rápidos

Filtros simples e visíveis:

* máquina
* tecido
* status
* período
* texto livre

### Área C — Painel lateral do rolo em montagem

Resumo vivo com:

* quantidade de itens selecionados
* total em metros
* máquina predominante ou escolhida
* tecido
* status da montagem
* observações rápidas

### Área D — Ações principais

* selecionar / remover item
* limpar seleção
* revisar rolo
* avançar para fechamento

---

## 7.3 Estados importantes nessa tela

O usuário deve perceber claramente se um item está:

* novo
* pronto para uso
* suspeito
* já vinculado
* ignorado
* inválido

Esses estados não podem depender só de cor. Também devem ter texto ou rótulo visível.

---

## 8. Tela de Fechamento do Rolo

Essa tela deve funcionar como confirmação operacional final.

## 8.1 Objetivo

Confirmar metadados, revisar totais e fechar o rolo com segurança.

## 8.2 Estrutura recomendada

### Resumo superior

* quantidade de jobs
* total estimado/consumido
* informações principais do rolo

### Seção de metadados

Campos como:

* identificação do rolo
* máquina
* tecido
* operador
* observações

### Seção de revisão

Lista resumida dos itens vinculados.

### Ações finais

* voltar para montagem
* confirmar fechamento
* fechar e exportar

---

## 8.3 Regra de UX

O fechamento não deve parecer irreversível sem aviso.
Se o sistema impedir edição posterior, isso precisa ficar claro.

---

## 9. Tela de Rolos / Consulta Histórica

Esta tela é inspirada conceitualmente na lógica do SearchOrders, mas adaptada ao domínio do Nexor.

## 9.1 Objetivo

Encontrar, abrir, revisar e reexportar registros já fechados.

## 9.2 Estrutura recomendada

### Área A — Filtros

* período
* máquina
* tecido
* operador
* status
* busca textual

### Área B — Lista de resultados

Cada linha deve mostrar pelo menos:

* identificação do rolo
* data
* máquina
* tecido
* operador
* total em metros
* status

### Área C — Painel de detalhes

Ao selecionar um rolo, exibir:

* dados gerais
* jobs vinculados
* observações
* exportações disponíveis
* ações de reexportação

### Área D — Ações contextuais

* abrir detalhe completo
* reexportar PDF
* reexportar JPG mirror
* revisar registro

---

## 9.3 Regra de UX

A consulta deve ser rápida. O sistema não pode exigir navegação profunda para exibir informações básicas do rolo.

---

## 10. Tela de Planejamento

Essa tela deve ser separada da operação diária para não poluir o fluxo principal.

## 10.1 Objetivo

Organizar a fila futura de produção.

## 10.2 Estrutura recomendada

### Área A — Itens planejáveis

Lista de jobs ou agrupamentos a planejar.

### Área B — Regras e agrupamento

* tecido
* ordem
* capacidade do rolo
* gaps
* estimativa

### Área C — Resultado do planejamento

Resumo da fila montada, com blocos ou segmentos.

### Área D — Ações

* gerar plano
* revisar
* ajustar ordem
* salvar planejamento

---

## 10.3 Regra de UX

Planejamento deve ter uma linguagem visual diferente da operação diária, deixando claro que é preparação, não fechamento real.

---

## 11. Tela de Estoque

A tela de estoque deve ser simples e orientada à disponibilidade.

## 11.1 Objetivo

Permitir visualizar e manter materiais utilizáveis no sistema.

## 11.2 Estrutura recomendada

### Lista principal

* tecido
* tipo do item
* metragem disponível
* status
* observações

### Filtros

* tecido
* tipo
* disponibilidade
* status

### Ações

* novo item
* editar item
* registrar ajuste
* visualizar consumo relacionado

---

## 11.3 Regra de UX

Estoque não deve parecer um ERP complexo. A experiência precisa ser enxuta e voltada ao que realmente será utilizado.

---

## 12. Tela de Cadastros

Cadastros devem ser fáceis de manter, mas não devem atrapalhar a operação.

## 12.1 Estrutura recomendada

Subseções:

* Operadores
* Máquinas
* Tecidos
* Aliases

Cada subseção deve ter:

* lista
* busca
* criação
* edição
* status ativo/inativo

## 12.2 Regra de UX

Cadastros devem usar formulários simples, objetivos e previsíveis.

---

## 13. Tela de Configurações

## 13.1 Objetivo

Controlar o comportamento estrutural do sistema sem poluir outras áreas.

## 13.2 Itens esperados

* pasta de origem dos logs
* pasta de exportação PDF
* pasta de exportação JPG mirror
* parâmetros gerais
* comportamento do sistema
* recursos futuros de backup/sync

## 13.3 Regra de UX

Configurações críticas devem ser claras e seguras. O sistema deve validar caminhos e evitar configurações quebradas.

---

## 14. Fluxo principal do operador

### Fluxo esperado

1. Abrir o Nexor
2. Ver a Home com status atual
3. Entrar em Operação
4. Ver logs/jobs disponíveis
5. Selecionar os que pertencem ao rolo atual
6. Revisar resumo do rolo
7. Avançar para fechamento
8. Confirmar metadados
9. Fechar o rolo
10. Gerar exportações

### Regra central

Esse fluxo deve exigir o menor número possível de decisões desnecessárias.

---

## 15. Fluxo principal da gestão / conferência

1. Abrir Rolos
2. Filtrar período ou contexto
3. Selecionar registro
4. Revisar detalhe
5. Reexportar ou conferir informações

Esse fluxo precisa ser rápido, porque normalmente será usado para resolver dúvidas ou conferências pontuais.

---

## 16. Fluxo principal da administração

1. Abrir Cadastros ou Configurações
2. Encontrar entidade ou parâmetro desejado
3. Criar, ajustar ou corrigir
4. Salvar
5. Voltar ao contexto principal

Esse fluxo precisa ser previsível e sem caminhos escondidos.

---

## 17. Componentes visuais essenciais

A UI deve trabalhar com um conjunto pequeno e consistente de componentes.

### Componentes recomendados

* cards de resumo
* tabelas/listas com filtros
* painéis laterais de contexto
* badges de status
* modais de confirmação
* formulários curtos
* toolbars de ação
* mensagens de validação
* empty states
* alertas visíveis

### Regra importante

Componentes devem ser reutilizados com a mesma lógica visual e semântica.

---

## 18. Hierarquia visual recomendada

### Nível 1 — ação principal

Botão ou bloco dominante da tela.

### Nível 2 — contexto e resumo

Indicadores, totais, cabeçalhos e status.

### Nível 3 — lista ou conteúdo principal

Onde o usuário trabalha.

### Nível 4 — ações secundárias

Ajustes, reexportações, filtros avançados e utilidades.

Se tudo parecer importante ao mesmo tempo, nada será realmente claro.

---

## 19. Feedback do sistema

O Nexor deve responder com clareza às ações do usuário.

### Deve informar claramente

* sucesso da ação
* erro de validação
* erro técnico
* item já usado
* item suspeito
* exportação concluída
* caminho inválido
* configuração incompleta

### Regra de linguagem

Mensagens devem ser diretas, sem tecnicismo desnecessário para o usuário final.

---

## 20. Estados vazios e erros

A experiência precisa considerar ausência de dados e falhas operacionais.

### Exemplos de estados vazios importantes

* nenhum log encontrado
* nenhum rolo registrado no filtro atual
* nenhum item em estoque
* nenhum planejamento salvo

### Regra

Estados vazios devem orientar a próxima ação, não apenas informar ausência.

---

## 21. Regras de responsividade e escalabilidade visual

Mesmo sendo um sistema pensado para ambiente local e uso em desktop, a UI deve ser organizada de forma escalável.

### Deve suportar bem

* janelas médias e grandes
* listas com muitos registros
* leitura prolongada
* navegação estável sem poluição

### Não deve depender de

* efeitos excessivos
* animações pesadas
* interfaces apertadas

---

## 22. Identidade e tom da interface

A identidade visual do Nexor deve transmitir:

* confiabilidade
* organização
* clareza
* sensação de ferramenta séria
* fluidez operacional

A interface não precisa parecer genérica, mas também não deve competir com a leitura dos dados.

---

## 23. Critérios de sucesso da UI

A UI estará no caminho certo quando:

* o operador souber por onde começar rapidamente
* o fluxo de fechamento de rolo for natural
* a consulta histórica for rápida
* as áreas administrativas não atrapalharem a operação
* o sistema parecer simples mesmo com várias capacidades
* os erros forem compreensíveis
* a repetição diária de uso não gerar fadiga desnecessária

---

## 24. Próximo desdobramento recomendado

Depois desta especificação, os próximos documentos naturais são:

* **Wireframe Specification**
* **Design System / UI Kit básico**
* **Functional Specification por tela**

---

## 25. Síntese final

A interface do Nexor deve ser construída como extensão natural do fluxo operacional.

Ela precisa ser intuitiva não porque será minimalista por aparência, mas porque cada tela terá função clara, linguagem correta, hierarquia visual consistente e conexão real com o domínio do sistema.

### Definição final

**UI/UX do Nexor = operação clara + navegação por domínio + baixa fricção + alta legibilidade + segurança nas ações + consistência para uso diário.**
