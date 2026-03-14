# Nexor Roadmap

Este documento descreve a evolução planejada do Nexor. As fases representam camadas progressivas de maturidade do sistema, começando pela estabilidade operacional e avançando para inteligência de produção e arquitetura escalável.

O roadmap não representa apenas funcionalidades isoladas, mas a construção gradual de uma plataforma de inteligência operacional para produção têxtil.

---

# Phase 1 — Operational Stability

Primeira fase focada em garantir que o Nexor funcione de forma confiável no ambiente real de produção.

Objetivo principal:

Estabelecer uma base sólida de ingestão de dados, normalização de registros e geração consistente de relatórios.

Principais entregas:

* cálculo padronizado de metragem
* normalização de campos extraídos dos logs
* padronização de exportações
* estrutura de diretórios consistente
* funções centralizadas de formatação
* identificação de máquinas via ComputerName

Também nesta fase o sistema deve tratar adequadamente convenções operacionais como arquivos de reposição.

Exemplo de nomenclatura:

* N1 - Dryfit
* N1 - Dryfit (1)
* N1 - Dryfit (2)

O parser deverá separar essas informações em campos estruturados como operador, índice de reposição e tecido, evitando que variações numéricas sejam interpretadas como tecidos diferentes.

Essa fase garante que o Nexor seja confiável para uso diário na operação.

---

# Phase 2 — Production Traceability

Após estabilizar a leitura de dados, o foco passa a ser rastreabilidade completa da produção.

Objetivo principal:

Transformar eventos de máquina em registros estruturados e auditáveis.

Principais recursos:

* registro estruturado de jobs de produção
* classificação de jobs (normal / reposição)
* histórico de produção por máquina
* registro de duração real de impressão
* preservação de gaps e espaçamentos de produção

Também é esperado nesta fase:

* cadastro de operadores
* associação entre código de operador e nome completo

Isso permite que relatórios e análises identifiquem claramente quem participou de cada reposição ou operação.

---

# Phase 3 — Operational Reporting

Nesta fase o Nexor evolui de um sistema de ingestão para uma ferramenta operacional de suporte à produção.

Objetivo principal:

Gerar relatórios claros e padronizados que apoiem diretamente o trabalho do operador.

Principais recursos:

* exportação de relatório de rolo em PDF
* geração de JPG espelhado para registro do rolo
* geração de resumo operacional para impressora

Arquivos gerados:

* ROLO_X.pdf
* ROLO_X.jpg
* Resumo M1.jpg
* Resumo M2.jpg

Cada tipo de arquivo possui um propósito diferente:

PDF

* arquivo permanente
* utilizado para consulta e histórico

JPG do rolo

* registro visual do layout
* backup caso o resumo operacional seja sobrescrito

Resumo da máquina

* arquivo temporário usado diretamente pela impressora
* sempre substituído pelo último rolo exportado

Essa separação evita conflitos entre arquivos históricos e arquivos operacionais.

---

# Phase 4 — Production Planning

Com a rastreabilidade consolidada, o Nexor passa a atuar também no planejamento da produção.

Objetivo principal:

Permitir que operadores organizem filas de impressão antes da execução.

Principais recursos:

* importação de imagens de impressão
* cálculo de comprimento baseado em DPI
* agrupamento automático por tecido
* organização da fila de impressão
* controle de capacidade de rolos
* inserção automática de espaçamentos
* estimativa de tempo de produção

Essa camada transforma o Nexor em uma ferramenta ativa de apoio à decisão operacional.

---

# Phase 5 — Fabric Utilization

Nesta fase o Nexor passa a auxiliar no aproveitamento de material disponível.

Objetivo principal:

Reduzir desperdício de tecido utilizando sobras disponíveis antes de consumir novos rolos.

Principais recursos:

* cadastro de rolos de tecido
* cadastro de pedaços de tecido
* verificação de compatibilidade de tecido
* distribuição de jobs em pedaços disponíveis
* atualização de estoque após confirmação do planejamento

O modelo inicial de estoque é intencionalmente simples, pois a origem exata de pedaços de tecido nem sempre é documentada na operação.

---

# Phase 6 — Production Analytics

Nesta fase o Nexor evolui para análise de eficiência operacional.

Objetivo principal:

Transformar dados de produção em métricas que ajudem a melhorar o desempenho da operação.

Possíveis análises:

* produtividade por máquina
* tempo médio por metro
* identificação de gargalos
* análise de eficiência de produção

Também nesta fase o sistema poderá integrar dados de consumo exportados pela impressora.

Formatos possíveis:

* XML
* CSV

Dependendo do nível de detalhe fornecido pelas máquinas, será possível calcular indicadores como consumo de tinta por job ou consumo médio por metro.

---

# Phase 7 — Hybrid Platform Architecture

Fase voltada para expansão da arquitetura do Nexor.

Objetivo principal:

Permitir operação híbrida com coleta local e análise ampliada.

Arquitetura conceitual:

Machines
↓
Nexor Agent
↓
Nexor Platform

Responsabilidades do agente local:

* monitorar pastas de produção
* detectar novos arquivos automaticamente
* importar logs de forma contínua
* normalizar dados no ambiente local
* sincronizar informações quando necessário

Essa evolução permite que o Nexor escale de uma ferramenta operacional local para uma plataforma de inteligência de produção.

---

# Long Term Vision

No longo prazo, o Nexor pode evoluir para uma plataforma capaz de:

* otimizar planejamento de produção
* sugerir organização de filas de impressão
* analisar desperdício de material
* prever duração de produção
* apoiar decisões estratégicas na operação

A meta é transformar dados de produção em inteligência operacional acessível para toda a cadeia de produção.
