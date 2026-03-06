# Nexor

**Centro de controle da produção de impressão têxtil**

Nexor é uma plataforma de gestão e inteligência operacional para ambientes de produção de impressão têxtil.

O sistema transforma **logs de produção das máquinas** em dados estruturados que permitem monitorar, rastrear e otimizar a operação.

---

# Visão

Operações de impressão têxtil frequentemente dependem de processos fragmentados:

* logs dispersos nas máquinas
* controle manual de produção
* baixa visibilidade da produtividade real
* dificuldade de rastrear o que foi produzido

O Nexor centraliza esses dados e os transforma em **inteligência operacional**.

O objetivo é permitir que líderes de produção tenham uma visão clara de:

* o que foi produzido
* quanto foi produzido
* quanto tempo levou
* como melhorar a eficiência da operação

---

# Categoria do Sistema

O Nexor se enquadra na categoria de sistemas industriais conhecidos como:

**MES — Manufacturing Execution System**

Arquitetura típica:

ERP
↓
MES (Nexor)
↓
Máquinas / Produção

O Nexor atua entre o planejamento e a execução da produção, conectando:

* máquinas
* logs de impressão
* planejamento de fila
* análise de produtividade

---

# Interface do Sistema

Voltado principalmente para **líderes de produção**.

Menu principal:

Fila de Produção
Produção
Produtividade
Cadastros
Configurações

---

# Estrutura do Projeto

```
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

* configuração
* paths
* modelos de dados
* utilidades

---

### logs

Importação e processamento de logs de produção.

Responsável por:

* leitura de logs `.txt`
* normalização de dados
* cálculo de duração
* identificação de máquina
* rastreabilidade da produção

---

### planner

Planejamento da fila de produção.

Recursos:

* agrupamento por tecido
* cálculo de metragem por arquivo
* controle de rolo
* inserção de gaps entre tecidos
* estimativa de tempo de produção

---

### analytics

Análise e inteligência operacional da produção.

Inclui:

* produtividade por máquina
* tempo médio por metro
* métricas de produção
* identificação de gargalos

---

### agent

Agente local responsável por coletar dados da produção.

Funções:

* monitorar pastas de logs
* importar automaticamente novos logs
* normalizar dados
* sincronizar dados

---

# Documentação

A documentação técnica do projeto está organizada em:

* `docs/architecture.md`
* `docs/roadmap.md`

---

# Princípios do Sistema

* modularidade
* rastreabilidade de dados
* evolução incremental
* arquitetura preparada para escala
* foco em operação real de produção

---

# Autor

Neuber Jone
Developer & Designer

GitHub
https://github.com/NeuberJone
