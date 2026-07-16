# 📘 Guia Completo de Uso - Nexor

**Sistema de Gerenciamento de Produção Têxtil**

---

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação e Configuração](#instalação-e-configuração)
3. [Interface do Usuário](#interface-do-usuário)
4. [Funcionalidades Principais](#funcionalidades-principais)
5. [Fluxos de Trabalho](#fluxos-de-trabalho)
6. [API REST](#api-rest)
7. [Tratamento de Erros](#tratamento-de-erros)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **Nexor** é uma plataforma operacional local-first para produção têxtil, focada em:

- **Rastreabilidade**: Acompanhamento completo de jobs e rolos
- **Fechamento de Rolos**: Gerenciamento eficiente do ciclo de produção
- **Métricas de Produção**: Analytics em tempo real
- **Sincronização**: Integração com backend Python existente

### Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Navegador (Frontend)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Interface Jinja2 + JavaScript + CSS (Dark Theme)       │ │
│  │ - Dashboard com métricas                              │ │
│  │ - Inbox de jobs                                       │ │
│  │ - Gerenciamento de rolos                              │ │
│  │ - Analytics e relatórios                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                  Flask Application (Backend)                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Endpoints REST com validação e tratamento de erros    │ │
│  │ - /api/jobs                                           │ │
│  │ - /api/rolls                                          │ │
│  │ - /api/suspicious                                     │ │
│  │ - /api/metrics                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Módulos de Negócio                                    │ │
│  │ - Validators (validação de dados)                     │ │
│  │ - Error Handler (tratamento de erros)                 │ │
│  │ - Backend Client (comunicação com Python)             │ │
│  │ - Database (SQLite)                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│              Backend Python (Integração Externa)            │
│  - Processamento de logs                                    │
│  - Algoritmos de produção                                   │
│  - Dados mestres                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes)
- Navegador moderno (Chrome, Firefox, Safari, Edge)

### Instalação

1. **Clone o repositório**
   ```bash
   cd /home/ubuntu/nexor-flask
   ```

2. **Crie um ambiente virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   # Crie um arquivo .env na raiz do projeto
   FLASK_APP=main.py
   FLASK_ENV=development
   BACKEND_URL=http://localhost:5000  # URL do backend Python
   DEBUG=True
   ```

5. **Inicie a aplicação**
   ```bash
   python main.py
   ```

6. **Acesse no navegador**
   ```
   http://localhost:3000
   ```

### Estrutura de Diretórios

```
nexor-flask/
├── main.py                      # Aplicação principal Flask
├── requirements.txt             # Dependências Python
├── .env                         # Variáveis de ambiente
├── app/
│   ├── __init__.py
│   ├── backend_client.py        # Cliente REST para backend
│   ├── validators.py            # Validadores de dados
│   ├── error_handler.py         # Tratamento de erros
│   ├── database.py              # Operações SQLite
│   ├── parsers.py               # Parsing de logs
│   ├── planning.py              # Planejamento de produção
│   ├── analytics.py             # Análise de dados
│   ├── backup.py                # Sistema de backup
│   ├── sync.py                  # Sincronização
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css        # Estilos principais
│   │   │   └── dark-theme.css   # Tema escuro
│   │   ├── js/
│   │   │   ├── feedback.js      # Sistema de feedback
│   │   │   ├── charts.js        # Gráficos
│   │   │   └── utils.js         # Utilitários
│   │   └── images/
│   └── templates/
│       ├── base.html            # Template base
│       ├── dashboard.html       # Dashboard
│       ├── jobs.html            # Gerenciamento de jobs
│       ├── rolls.html           # Gerenciamento de rolos
│       ├── suspicious.html      # Jobs suspeitos
│       ├── analytics.html       # Analytics
│       └── ...
└── tests/
    ├── test_validators.py
    ├── test_error_handler.py
    └── test_backend_client.py
```

---

## 🎨 Interface do Usuário

### Layout Principal

A interface segue um design moderno com tema escuro, composto por:

#### 1. **Sidebar (Navegação Lateral)**
- Logo da aplicação
- Menu de navegação principal
- Links para todas as seções
- Indicador de seção ativa
- Collapse/expand responsivo

#### 2. **Topbar (Barra Superior)**
- Relógio em tempo real
- Notificações
- Perfil do usuário
- Configurações rápidas

#### 3. **Área Principal**
- Conteúdo dinâmico por página
- Breadcrumbs de navegação
- Filtros e busca
- Tabelas com dados

#### 4. **Componentes Comuns**

**Metric Cards** - Exibem KPIs
```
┌─────────────────────┐
│  📊 Métrica         │
│  1,234 unidades     │
│  ↑ 12% vs mês ant.  │
└─────────────────────┘
```

**Action Buttons** - Botões de ação
```
[+ Novo Job] [Sincronizar] [Exportar] [⚙️ Config]
```

**Alerts Section** - Alertas e notificações
```
⚠️ 3 jobs suspeitos aguardando revisão
✅ Última sincronização: 2 minutos atrás
```

**Activity Tables** - Tabelas de dados
```
| ID | Status | Progresso | Ação |
|----+--------+-----------+------|
| 1  | Ativo  | 75%       | [...] |
```

---

## 🚀 Funcionalidades Principais

### 1. Dashboard Operacional

**Localização**: Home / Dashboard

**Funcionalidades**:
- Visualização de métricas em tempo real
- Status de produção
- Alertas de jobs suspeitos
- Atividade recente
- Gráficos de tendências

**Como usar**:
1. Acesse a página inicial
2. Visualize as métricas principais
3. Clique em um card para detalhar
4. Use os filtros para refinar dados

### 2. Gerenciamento de Jobs

**Localização**: Menu → Jobs

**Funcionalidades**:
- Listar todos os jobs
- Criar novo job
- Editar job existente
- Deletar job
- Filtrar por status, prioridade, data
- Buscar por ID ou descrição

**Como usar**:

#### Criar um novo job:
```
1. Clique em "+ Novo Job"
2. Preencha os campos:
   - ID do Job (obrigatório)
   - Descrição
   - Prioridade (Baixa/Média/Alta)
   - Data de entrega
   - Quantidade de rolos
3. Clique em "Salvar"
4. Aguarde a confirmação
```

#### Editar um job:
```
1. Localize o job na tabela
2. Clique no ícone de edição (✏️)
3. Modifique os campos desejados
4. Clique em "Atualizar"
```

#### Filtrar jobs:
```
1. Use a barra de filtros no topo
2. Selecione: Status, Prioridade, Data
3. Clique em "Aplicar Filtros"
4. Clique em "Limpar" para resetar
```

### 3. Gerenciamento de Rolos

**Localização**: Menu → Rolos

**Funcionalidades**:
- Listar rolos ativos
- Montar novo rolo
- Fechar rolo
- Visualizar histórico
- Rastrear localização

**Como usar**:

#### Montar um novo rolo:
```
1. Clique em "+ Montar Rolo"
2. Preencha:
   - Job ID (seleção)
   - Número do rolo
   - Largura (cm)
   - Comprimento (m)
   - Peso (kg)
   - Operador responsável
   - Máquina
3. Clique em "Montar"
```

#### Fechar um rolo:
```
1. Localize o rolo na tabela
2. Clique em "Fechar"
3. Confirme a ação
4. O rolo é marcado como concluído
```

### 4. Revisão de Jobs Suspeitos

**Localização**: Menu → Suspeitos

**Funcionalidades**:
- Listar jobs com anomalias
- Revisar detalhes
- Aprovar ou rejeitar
- Adicionar comentários
- Gerar relatório

**Como usar**:

#### Revisar um job suspeito:
```
1. Acesse a página de Suspeitos
2. Clique no job para expandir detalhes
3. Analise os motivos da suspeita
4. Escolha:
   - ✅ Aprovar (aceitar como válido)
   - ❌ Rejeitar (marcar como erro)
   - 💬 Comentar (adicionar nota)
5. Clique em "Salvar Revisão"
```

### 5. Analytics e Relatórios

**Localização**: Menu → Analytics

**Funcionalidades**:
- Gráficos de produção
- Comparação de períodos
- Análise de eficiência
- Exportar relatórios
- Filtrar por período

**Como usar**:

#### Visualizar gráficos:
```
1. Acesse Analytics
2. Selecione o período (Hoje/Semana/Mês/Ano)
3. Escolha a métrica:
   - Produção por máquina
   - Eficiência por operador
   - Taxa de defeitos
   - Tempo médio de produção
4. Analise o gráfico
```

#### Exportar relatório:
```
1. Clique em "Exportar"
2. Escolha o formato:
   - PDF (para impressão)
   - CSV (para Excel)
   - JSON (para integração)
3. Clique em "Download"
```

### 6. Dados Mestres

**Localização**: Menu → Configurações → Dados Mestres

**Funcionalidades**:
- Gerenciar máquinas
- Gerenciar operadores
- Gerenciar tipos de tecido
- Gerenciar clientes

**Como usar**:

#### Adicionar uma máquina:
```
1. Acesse Dados Mestres → Máquinas
2. Clique em "+ Nova Máquina"
3. Preencha:
   - Nome/Código
   - Tipo
   - Capacidade
   - Status
4. Clique em "Salvar"
```

---

## 📊 Fluxos de Trabalho

### Fluxo 1: Criar e Processar um Job

```
┌─────────────────────────────────────────────────────────┐
│ 1. Criar Job                                            │
│    - Acesse "Novo Job"                                  │
│    - Preencha informações                               │
│    - Salve                                              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Montar Rolos                                         │
│    - Acesse "Montar Rolo"                               │
│    - Selecione o job                                    │
│    - Configure dimensões                                │
│    - Salve                                              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Produção                                             │
│    - Operador inicia produção                           │
│    - Sistema registra tempo e métricas                  │
│    - Monitorar no Dashboard                             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Fechar Rolo                                          │
│    - Clique em "Fechar Rolo"                            │
│    - Confirme dados finais                              │
│    - Sistema registra conclusão                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Análise                                              │
│    - Sistema detecta anomalias                          │
│    - Jobs suspeitos marcados                            │
│    - Revisor aprova/rejeita                             │
└─────────────────────────────────────────────────────────┘
```

### Fluxo 2: Sincronização com Backend

```
┌─────────────────────────────────────────────────────────┐
│ 1. Sincronizar Dados                                    │
│    - Clique em "Sincronizar" no Dashboard               │
│    - Sistema conecta ao backend Python                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Enviar Dados                                         │
│    - Jobs novos/modificados                             │
│    - Rolos completados                                  │
│    - Métricas de produção                               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Receber Dados                                        │
│    - Dados mestres atualizados                          │
│    - Novos jobs do backend                              │
│    - Configurações                                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Atualizar Interface                                  │
│    - Dashboard refrescado                               │
│    - Notificação de sucesso                             │
│    - Timestamp da última sincronização                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 API REST

### Endpoints Disponíveis

#### Jobs

**GET /api/jobs**
- Listar todos os jobs
- Parâmetros: `status`, `priority`, `date_from`, `date_to`
- Resposta: Lista de jobs

```bash
curl -X GET "http://localhost:3000/api/jobs?status=active&priority=high"
```

**POST /api/jobs**
- Criar novo job
- Body: `{ "id": "JOB001", "description": "...", "priority": "high", ... }`
- Resposta: Job criado com ID

```bash
curl -X POST "http://localhost:3000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{"id":"JOB001","description":"Produção de tecido","priority":"high"}'
```

**PUT /api/jobs/<job_id>**
- Atualizar job
- Body: Campos a atualizar
- Resposta: Job atualizado

```bash
curl -X PUT "http://localhost:3000/api/jobs/JOB001" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

**DELETE /api/jobs/<job_id>**
- Deletar job
- Resposta: Confirmação

```bash
curl -X DELETE "http://localhost:3000/api/jobs/JOB001"
```

#### Rolos

**GET /api/rolls**
- Listar rolos
- Parâmetros: `status`, `job_id`
- Resposta: Lista de rolos

```bash
curl -X GET "http://localhost:3000/api/rolls?status=active"
```

**POST /api/rolls**
- Montar novo rolo
- Body: `{ "job_id": "JOB001", "number": 1, "width": 100, ... }`
- Resposta: Rolo criado

```bash
curl -X POST "http://localhost:3000/api/rolls" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"JOB001","number":1,"width":100,"length":500,"weight":25}'
```

**PUT /api/rolls/<roll_id>/close**
- Fechar rolo
- Body: `{ "final_weight": 25, "quality_check": "passed" }`
- Resposta: Rolo fechado

```bash
curl -X PUT "http://localhost:3000/api/rolls/1/close" \
  -H "Content-Type: application/json" \
  -d '{"final_weight":25,"quality_check":"passed"}'
```

#### Suspeitos

**GET /api/suspicious**
- Listar jobs suspeitos
- Parâmetros: `status`, `reason`
- Resposta: Lista de jobs com anomalias

```bash
curl -X GET "http://localhost:3000/api/suspicious?status=pending"
```

**PUT /api/suspicious/<job_id>/review**
- Revisar job suspeito
- Body: `{ "status": "approved", "comment": "..." }`
- Resposta: Revisão registrada

```bash
curl -X PUT "http://localhost:3000/api/suspicious/JOB001/review" \
  -H "Content-Type: application/json" \
  -d '{"status":"approved","comment":"Verificado e aprovado"}'
```

#### Métricas

**GET /api/metrics**
- Obter métricas de produção
- Parâmetros: `period` (day/week/month/year)
- Resposta: Métricas agregadas

```bash
curl -X GET "http://localhost:3000/api/metrics?period=month"
```

#### Sincronização

**POST /api/sync**
- Sincronizar com backend Python
- Body: Dados a sincronizar
- Resposta: Status da sincronização

```bash
curl -X POST "http://localhost:3000/api/sync" \
  -H "Content-Type: application/json" \
  -d '{"type":"full","timestamp":"2024-01-15T10:30:00Z"}'
```

### Formato de Respostas

**Sucesso (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "JOB001",
    "description": "Produção de tecido",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Job criado com sucesso"
}
```

**Erro (400/500)**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Campo 'priority' inválido",
    "details": {
      "field": "priority",
      "value": "invalid",
      "allowed": ["low", "medium", "high"]
    }
  }
}
```

---

## ⚠️ Tratamento de Erros

### Tipos de Erro

| Código | Descrição | Solução |
|--------|-----------|---------|
| `VALIDATION_ERROR` | Dados inválidos | Verifique os campos obrigatórios |
| `NOT_FOUND` | Recurso não existe | Verifique o ID do recurso |
| `CONFLICT` | Conflito de dados | Sincronize com o backend |
| `BACKEND_ERROR` | Erro no backend Python | Verifique a conexão |
| `DATABASE_ERROR` | Erro no banco de dados | Reinicie a aplicação |
| `UNAUTHORIZED` | Sem permissão | Faça login novamente |

### Feedback Visual

A aplicação exibe notificações automáticas:

**Toast Notifications**
```
✅ Sucesso: Operação concluída com sucesso
❌ Erro: Falha ao processar solicitação
⚠️ Aviso: Ação requer confirmação
ℹ️ Info: Informação importante
```

**Loading States**
- Spinner durante operações
- Botão desabilitado enquanto processa
- Overlay semi-transparente

**Modal Dialogs**
- Confirmação de ações críticas
- Exibição de erros detalhados
- Formulários de entrada

### Tratamento de Erros Comuns

**Erro: "Conexão com backend falhou"**
```
Solução:
1. Verifique se o backend Python está rodando
2. Confirme a URL em .env (BACKEND_URL)
3. Verifique a conexão de rede
4. Reinicie a aplicação
```

**Erro: "Validação falhou"**
```
Solução:
1. Leia a mensagem de erro detalhada
2. Corrija os campos indicados
3. Verifique os tipos de dados
4. Tente novamente
```

**Erro: "Recurso não encontrado"**
```
Solução:
1. Verifique o ID do recurso
2. Sincronize com o backend
3. Atualize a página (F5)
4. Tente novamente
```

---

## 🔍 Troubleshooting

### Problema: Aplicação não inicia

**Sintomas**: Erro ao executar `python main.py`

**Soluções**:
1. Verifique se o ambiente virtual está ativado
2. Instale as dependências: `pip install -r requirements.txt`
3. Verifique se a porta 3000 está disponível
4. Verifique os logs de erro

```bash
# Ver logs detalhados
python main.py --debug

# Verificar porta
lsof -i :3000
```

### Problema: Interface não carrega

**Sintomas**: Página em branco ou erro 404

**Soluções**:
1. Limpe o cache do navegador (Ctrl+Shift+Del)
2. Verifique se o servidor está rodando
3. Tente outro navegador
4. Verifique o console do navegador (F12)

### Problema: Dados não sincronizam

**Sintomas**: Dados não aparecem após sincronização

**Soluções**:
1. Verifique a conexão com o backend Python
2. Confirme a URL do backend em .env
3. Verifique os logs da aplicação
4. Tente sincronizar manualmente

```bash
# Forçar sincronização
curl -X POST "http://localhost:3000/api/sync" \
  -H "Content-Type: application/json" \
  -d '{"type":"full"}'
```

### Problema: Erros de validação

**Sintomas**: "Campo inválido" ao criar/editar

**Soluções**:
1. Verifique os tipos de dados
2. Confirme os valores permitidos
3. Verifique o tamanho máximo de campos
4. Consulte a documentação da API

### Problema: Banco de dados corrompido

**Sintomas**: Erro ao acessar dados

**Soluções**:
1. Faça backup do banco de dados
2. Delete o arquivo `nexor.db`
3. Reinicie a aplicação (recria o banco)
4. Sincronize com o backend

```bash
# Backup
cp app/nexor.db app/nexor.db.backup

# Deletar e recriar
rm app/nexor.db
python main.py
```

### Problema: Performance lenta

**Sintomas**: Interface lenta, operações demoram

**Soluções**:
1. Verifique o tamanho do banco de dados
2. Limpe dados antigos
3. Verifique a conexão de rede
4. Aumente os recursos do servidor

```bash
# Ver tamanho do banco
du -h app/nexor.db

# Otimizar banco
sqlite3 app/nexor.db "VACUUM;"
```

---

## 📞 Suporte e Contato

### Recursos Adicionais

- **Documentação Técnica**: Veja `NEXOR_README.md`
- **Código-fonte**: Disponível em `/home/ubuntu/nexor-flask`
- **Logs**: Verifique `app/logs/` para detalhes

### Reportar Problemas

Ao reportar um problema, inclua:
1. Descrição do problema
2. Passos para reproduzir
3. Mensagem de erro exata
4. Logs relevantes
5. Versão do navegador

### Melhorias Sugeridas

Sugestões de melhorias são bem-vindas! Envie para:
- Email: suporte@nexor.local
- Repositório: Issues no GitHub

---

## 📝 Changelog

### Versão 1.0.0 (Inicial)
- ✅ Dashboard operacional
- ✅ Gerenciamento de jobs
- ✅ Gerenciamento de rolos
- ✅ Revisão de suspeitos
- ✅ Analytics
- ✅ Sincronização com backend
- ✅ Sistema de feedback visual
- ✅ Tratamento robusto de erros

---

**Última atualização**: 20 de março de 2026

**Versão do documento**: 1.0.0

**Status**: ✅ Pronto para produção
