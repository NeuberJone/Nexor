# Nexor

**Centro de controle da produção de impressão têxtil**

Nexor é uma plataforma de gestão e inteligência operacional para ambientes de produção de impressão têxtil.

O sistema transforma dados de produção em informação estruturada para monitorar, rastrear, planejar e otimizar a operação. Seu ponto de partida são os logs gerados pelas máquinas, mas sua proposta vai além da leitura de logs: o Nexor foi concebido como uma base operacional para produção, relatórios, planejamento e análise de eficiência.

---

## Visão

Operações de impressão têxtil frequentemente dependem de processos fragmentados:

* logs dispersos nas máquinas
* controle manual de produção
* baixa visibilidade da produtividade real
* dificuldade de rastrear o que foi produzido
* pouca padronização na geração de relatórios
* dificuldade de reaproveitar materiais e consolidar informações operacionais

O Nexor centraliza esses dados e os transforma em inteligência operacional.

O objetivo é permitir que líderes de produção tenham uma visão clara de:

* o que foi produzido
* quanto foi produzido
* quanto tempo levou
* como os rolos foram organizados
* quanto foi consumido na operação
* como melhorar a eficiência do processo

---

## Categoria do Sistema

O Nexor se enquadra na categoria de sistemas industriais conhecidos como **MES — Manufacturing Execution System**.

Arquitetura conceitual:

ERP
↓
MES (Nexor)
↓
Máquinas / Produção

O Nexor atua entre o planejamento e a execução da produção, conectando:

* máquinas
* logs de impressão
* relatórios operacionais
* planejamento de fila
* métricas de produtividade
* análise de consumo

---

## Proposta do Sistema

O Nexor foi pensado para operar como uma plataforma modular de produção têxtil, com foco em quatro frentes principais:

### 1. Rastreabilidade da produção

Transformar eventos de máquina em registros organizados, auditáveis e fáceis de consultar.

### 2. Padronização operacional

Gerar relatórios e arquivos de apoio em formatos consistentes, reduzindo erros e retrabalho.

### 3. Planejamento de produção

Permitir montagem de filas por tecido, controle de rolos e aproveitamento de material disponível.

### 4. Inteligência operacional

Produzir métricas de produtividade, consumo e eficiência para apoiar decisões de produção.

---

## Estrutura do Projeto

```text
nexor/
 ├ core/
 ├ logs/
 ├ planner/
 ├ analytics/
 ├ agent/
 ├ docs/
 └ app.py
```

### core

Infraestrutura central do sistema.

Responsável por:

* modelos de dados
* exceções
* configuração do sistema
* utilidades compartilhadas
* regras centrais de domínio

### logs

Importação e processamento de logs de produção.

Responsável por:

* leitura de arquivos `.txt`
* parsing de dados
* cálculo de duração
* identificação de máquina
* normalização de registros
* rastreabilidade da produção
* tratamento de reposições

### planner

Planejamento da fila de produção.

Recursos previstos:

* agrupamento por tecido
* cálculo de metragem por arquivo
* controle de rolos
* inserção de gaps entre tecidos
* estimativa de tempo de produção
* aproveitamento de tecido disponível em estoque

### analytics

Análise e inteligência operacional da produção.

Inclui:

* produtividade por máquina
* tempo médio por metro
* métricas de produção
* identificação de gargalos
* relatórios de consumo de insumos

### agent

Agente local responsável por coletar dados da produção.

Funções previstas:

* monitorar pastas de logs
* importar automaticamente novos logs
* normalizar dados
* sincronizar com a plataforma

---

## Reposições

O Nexor considera que arquivos de reposição seguem uma convenção operacional própria.

Exemplos:

* `N1 - Dryfit`
* `N1 - Dryfit (1)`
* `N1 - Dryfit (2)`

Nesse tipo de arquivo, o sistema poderá separar:

* nome original do job
* tecido
* tipo de job
* operador responsável
* índice da reposição

Exemplo conceitual:

* `job_name = N1 - Dryfit (2)`
* `fabric = Dryfit`
* `job_type = replacement`
* `operator = N`
* `replacement_index = 1`

O objetivo dessa separação é evitar que variações como `(1)` e `(2)` sejam interpretadas como tecidos diferentes quando, na prática, pertencem à mesma reposição ou ao mesmo grupo de tecido.

Ao mesmo tempo, o Nexor deve manter flexibilidade para que o operador possa ajustar tecido e outros dados antes da exportação final, já que erros de digitação e variações reais de nomenclatura podem acontecer na operação.

Também está previsto o cadastro de operadores para que os relatórios possam exibir o nome completo do responsável, e não apenas sua inicial.

---

## Exportação de Relatórios

A exportação de PDF e JPG espelhado seguirá o mesmo padrão operacional já adotado no ecossistema Jocasta, adaptado à lógica do Nexor.

Cada exportação poderá gerar três arquivos:

### 1. PDF do rolo

Arquivo permanente para consulta e histórico.

Destino:

* pasta de relatórios
* configurável pelo operador

### 2. JPG espelhado do rolo

Arquivo permanente de registro visual do rolo exportado.

Destino:

* pasta de registro de rolos

Objetivo:

* permitir reimpressão ou recuperação do resumo de um rolo anterior caso o resumo operacional tenha sido sobrescrito

### 3. JPG espelhado de resumo operacional

Arquivos temporários de uso direto na impressora:

* `Resumo M1.jpg`
* `Resumo M2.jpg`

Destino:

* pasta de impressão configurável pelo operador

Objetivo:

* deixar sempre disponível na impressora o resumo mais recente da máquina correspondente
* evitar que o operador precise navegar manualmente entre arquivos para localizar o rolo atual

Esses arquivos de resumo serão sobrescritos a cada nova exportação destinada à respectiva máquina.

---

## Planejamento de Produção

O Nexor deverá incluir uma camada de planejamento de produção para organizar impressões antes da execução.

Recursos previstos:

* agrupar jobs por tecido
* controlar capacidade de rolos
* inserir espaçamentos entre grupos
* estimar tempo total de produção
* avaliar aproveitamento de tecido disponível

### Aproveitamento de tecido

O planejamento poderá contar com uma opção marcável de aproveitamento de tecido.

Nesse modo, o operador poderá cadastrar um estoque simples contendo:

* rolos de tecido
* pedaços de tecido

Quando a opção estiver habilitada, o sistema poderá:

* verificar se o tecido disponível é compatível com o job planejado
* distribuir impressões em pedaços de tecido já existentes
* priorizar o reaproveitamento antes de consumir um novo rolo
* remover ou atualizar os itens do estoque após confirmação do planejamento

Na fase inicial, o modelo de estoque será simples, priorizando os campos essenciais para operação real.

---

## Relatórios de Consumo

O Nexor também deverá evoluir para gerar relatórios de gastos e consumo operacional.

Dados previstos:

* consumo de tinta
* consumo de papel
* consumo de tecido
* indicadores de eficiência de produção

As impressoras podem exportar esse tipo de informação em arquivos como:

* XML
* CSV

O formato real desses dados ainda deverá ser validado em ambiente de produção para definir a melhor forma de importação, correlação e análise dentro do Nexor.

---

## Documentação

A documentação técnica do projeto está organizada em:

* `docs/architecture.md`
* `docs/roadmap.md`

---

## Princípios do Sistema

* modularidade
* rastreabilidade de dados
* padronização operacional
* evolução incremental
* arquitetura preparada para escala
* foco em operação real de produção

---

## Autor

**Neuber Jone**
Developer & Designer

GitHub: [https://github.com/NeuberJone](https://github.com/NeuberJone)
