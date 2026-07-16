# 📑 Índice de Arquivos - Nexor

## 📂 Estrutura do Projeto

```
nexor-flask/
├── 📄 main.py                          # Aplicação Flask principal (1.162 linhas)
├── 📄 requirements.txt                 # Dependências Python
├── 📄 run.sh                           # Script de inicialização
├── 📄 README.md                        # Guia rápido de instalação
├── 📄 NEXOR_USAGE_GUIDE.md            # Documentação completa de uso
├── 📄 FILE_INDEX.md                    # Este arquivo
│
├── 📁 app/
│   ├── 📄 __init__.py                  # Inicialização do módulo
│   ├── 📄 backend_client.py            # Cliente REST para backend Python (278 linhas)
│   ├── 📄 validators.py                # Validadores de dados (274 linhas)
│   ├── 📄 error_handler.py             # Tratamento robusto de erros (206 linhas)
│   ├── 📄 database.py                  # Operações SQLite
│   ├── 📄 parsers.py                   # Parsing de logs (ProjetoJocasta)
│   ├── 📄 planning.py                  # Planejamento de produção
│   ├── 📄 analytics.py                 # Análise de dados e métricas
│   ├── 📄 sync.py                      # Sincronização com backend
│   ├── 📄 backup.py                    # Sistema de backup/restore
│   ├── 📄 exporters.py                 # Exportação de dados (PDF, JPG)
│   │
│   ├── 📁 templates/                   # Templates Jinja2
│   │   ├── 📄 base.html                # Template base (layout, sidebar, topbar)
│   │   ├── 📄 index.html               # Dashboard/Home
│   │   ├── 📄 operacao.html            # Inbox de jobs
│   │   ├── 📄 rolos.html               # Gerenciamento de rolos
│   │   ├── 📄 planejamento.html        # Planejamento de produção
│   │   ├── 📄 planejamento-novo.html   # Novo planejamento
│   │   ├── 📄 estoque.html             # Gestão de estoque
│   │   ├── 📄 estoque-novo.html        # Novo estoque
│   │   ├── 📄 cadastros.html           # Dados mestres
│   │   ├── 📄 configuracoes.html       # Configurações
│   │   ├── 📄 analytics-novo.html      # Analytics
│   │   ├── 📄 auditoria.html           # Auditoria
│   │   ├── 📄 reexportacao.html        # Re-exportação
│   │   ├── 📄 revisao-inconsistencias.html  # Revisão de inconsistências
│   │   ├── 📄 sistema.html             # Sistema
│   │   ├── 📄 404.html                 # Página não encontrada
│   │   └── 📄 500.html                 # Erro interno
│   │
│   └── 📁 static/
│       ├── 📁 css/
│       │   └── 📄 styles.css           # Estilos CSS (tema escuro)
│       │
│       └── 📁 js/
│           ├── 📄 feedback.js          # Sistema de feedback visual (400+ linhas)
│           └── 📄 app.js               # Lógica da aplicação
│
└── 📁 venv/                            # Ambiente virtual Python (não incluir em distribuição)
```

## 📋 Descrição dos Arquivos Principais

### Backend (Python)

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| **main.py** | 1.162 | Aplicação Flask com 40+ endpoints REST |
| **backend_client.py** | 278 | Cliente HTTP para comunicação com backend Python |
| **validators.py** | 274 | Validadores de dados para Jobs, Rolos, Máquinas, Tecidos, Operadores |
| **error_handler.py** | 206 | Tratamento centralizado de erros com decorators |
| **database.py** | ~250 | Operações SQLite para persistência local |
| **parsers.py** | ~300 | Parsing de logs baseado em ProjetoJocasta |
| **planning.py** | ~250 | Planejamento de produção e alocação de jobs |
| **analytics.py** | ~200 | Análise de métricas e geração de gráficos |
| **sync.py** | ~200 | Sincronização bidirecional com backend |
| **backup.py** | ~200 | Sistema de backup/restore com compressão |
| **exporters.py** | ~200 | Exportação de dados para PDF e JPG |

### Frontend (HTML/CSS/JavaScript)

| Arquivo | Descrição |
|---------|-----------|
| **base.html** | Template base com layout (sidebar, topbar, main content) |
| **index.html** | Dashboard com métricas e ações rápidas |
| **operacao.html** | Inbox de jobs com filtros e seleção múltipla |
| **rolos.html** | Gerenciamento de rolos (abertos/fechados) |
| **planejamento.html** | Planejamento de produção |
| **estoque.html** | Gestão de estoque de tecidos |
| **cadastros.html** | Gerenciamento de dados mestres |
| **configuracoes.html** | Configurações do sistema |
| **analytics-novo.html** | Analytics com gráficos |
| **styles.css** | Estilos CSS (tema escuro profissional) |
| **feedback.js** | Sistema de feedback visual (toasts, loaders, modals) |
| **app.js** | Lógica da aplicação (relógio, status, navegação) |

### Documentação

| Arquivo | Descrição |
|---------|-----------|
| **README.md** | Guia rápido de instalação e uso |
| **NEXOR_USAGE_GUIDE.md** | Documentação completa com 8 seções |
| **FILE_INDEX.md** | Este arquivo (índice de arquivos) |

### Configuração

| Arquivo | Descrição |
|---------|-----------|
| **requirements.txt** | Dependências Python |
| **run.sh** | Script de inicialização |

## 🚀 Endpoints da API

### Jobs
- `GET /api/jobs` - Listar jobs
- `POST /api/jobs` - Criar job
- `PUT /api/jobs/<id>` - Atualizar job
- `DELETE /api/jobs/<id>` - Deletar job

### Rolos
- `GET /api/rolls` - Listar rolos
- `POST /api/rolls` - Montar rolo
- `PUT /api/rolls/<id>/close` - Fechar rolo
- `GET /api/rolls/<id>/export` - Exportar rolo

### Suspeitos
- `GET /api/suspicious` - Listar jobs suspeitos
- `PUT /api/suspicious/<id>/review` - Revisar suspeito

### Dados Mestres
- `GET /api/machines` - Listar máquinas
- `POST /api/machines` - Criar máquina
- `GET /api/fabrics` - Listar tecidos
- `POST /api/fabrics` - Criar tecido
- `GET /api/operators` - Listar operadores
- `POST /api/operators` - Criar operador

### Métricas
- `GET /api/metrics` - Obter métricas
- `GET /api/metrics/summary` - Resumo de produção
- `GET /api/metrics/machines` - Utilização de máquinas
- `GET /api/metrics/fabrics` - Distribuição de tecidos

### Sistema
- `GET /api/status` - Status do servidor
- `GET /api/health` - Health check
- `POST /api/sync` - Sincronizar dados
- `POST /api/import` - Importar logs

## 📦 Dependências

```
Flask==3.1.3              # Framework web
Flask-CORS==6.0.2         # CORS support
requests==2.32.5          # HTTP client
python-dotenv==1.2.2      # Variáveis de ambiente
Werkzeug==3.1.6           # WSGI utilities
Jinja2==3.1.6             # Template engine
reportlab==4.0.7          # Geração de PDF
Pillow==10.1.0            # Processamento de imagens
```

## 🎯 Funcionalidades Implementadas

✅ **Dashboard Operacional** - Métricas em tempo real
✅ **Gerenciamento de Jobs** - CRUD completo
✅ **Gerenciamento de Rolos** - Montagem e fechamento
✅ **Revisão de Suspeitos** - Análise de anomalias
✅ **Analytics** - Gráficos e relatórios
✅ **Sincronização** - Integração com backend Python
✅ **Backup/Restore** - Sistema de backup automático
✅ **Validação** - Validadores específicos por entidade
✅ **Tratamento de Erros** - Decorators e respostas padronizadas
✅ **Feedback Visual** - Toasts, loading states, modals
✅ **Tema Escuro** - Interface profissional
✅ **Responsividade** - Design adaptativo

## 🔧 Como Usar

### Instalação
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuração
Crie um arquivo `.env` na raiz do projeto:
```
FLASK_APP=main.py
FLASK_ENV=development
DEBUG=True
PORT=5001
BACKEND_API_URL=http://localhost:5000/api
```

### Execução
```bash
python main.py
# ou
bash run.sh
```

### Acesso
```
http://localhost:5001
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte **NEXOR_USAGE_GUIDE.md** para documentação completa
2. Verifique os logs em `app/logs/`
3. Consulte a seção de Troubleshooting

## 📝 Versão

- **Versão**: 1.0.0
- **Data**: Março 2026
- **Status**: ✅ Pronto para produção

---

**Última atualização**: 20 de março de 2026
