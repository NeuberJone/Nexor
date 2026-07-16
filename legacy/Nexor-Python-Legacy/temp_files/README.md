# Nexor — Sistema de Gerenciamento de Produção Têxtil

Aplicação web em **Python (Flask + Jinja2)** que reproduz o layout e UX da Interface_temp, integrando com o backend Python existente.

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Ambiente

Edite o arquivo `.env` com as configurações do seu backend:

```env
FLASK_APP=main.py
FLASK_ENV=development
DEBUG=True
PORT=5001
BACKEND_API_URL=http://localhost:5000/api
```

### 3. Executar Servidor

```bash
python main.py
```

A aplicação estará disponível em: **http://localhost:5001**

## 📁 Estrutura do Projeto

```
nexor-flask/
├── main.py                      # Aplicação Flask principal
├── requirements.txt             # Dependências Python
├── .env                         # Configurações de ambiente
├── app/
│   ├── templates/
│   │   ├── base.html           # Template base com layout
│   │   ├── index.html          # Página Home
│   │   ├── operacao.html       # Página Operação (Inbox)
│   │   ├── rolos.html          # Página Rolos
│   │   ├── planejamento.html   # Página Planejamento
│   │   ├── estoque.html        # Página Estoque
│   │   ├── cadastros.html      # Página Cadastros
│   │   └── configuracoes.html  # Página Configurações
│   └── static/
│       ├── css/
│       │   └── styles.css      # Estilos (reprodução da Interface_temp)
│       └── js/
│           └── app.js          # Lógica da aplicação
└── venv/                        # Ambiente virtual Python
```

## 🎯 Funcionalidades

### Páginas Implementadas

- **Home**: Dashboard com métricas, ações rápidas e atividade recente
- **Operação**: Inbox de jobs com seleção múltipla e filtros
- **Rolos**: Gerenciamento de rolos (abertos/fechados)
- **Planejamento**: Planejamento de produção
- **Estoque**: Gestão de estoque de tecidos
- **Cadastros**: Gerenciamento de dados mestres (máquinas, operadores, tecidos)
- **Configurações**: Configurações do sistema

### Endpoints da API

#### Dados
- `GET /api/status` - Status do servidor
- `GET /api/jobs?limit=1000` - Lista de jobs
- `GET /api/rolls` - Lista de rolos
- `GET /api/suspects` - Jobs suspeitos
- `GET /api/fabrics` - Tecidos
- `GET /api/machines` - Máquinas
- `GET /api/log-sources` - Fontes de logs
- `GET /api/metrics` - Métricas de produção

#### Ações
- `POST /api/rolls` - Criar rolo
- `POST /api/rolls/{id}/close` - Fechar rolo
- `POST /api/suspects/{id}/review` - Revisar suspeito
- `POST /api/import` - Executar importação
- `POST /api/suspects/scan` - Escanear suspeitos

## 🎨 Design & UX

A aplicação reproduz fielmente o design da Interface_temp:

- **Dark Theme**: Paleta de cores profissional (azul, verde, amarelo, vermelho)
- **Sidebar**: Navegação principal com 6 seções
- **Topbar**: Título da página, relógio e botão de ação
- **Cards**: Métricas em cards com valores destacados
- **Tabelas**: Listagens com filtros e ações
- **Modais**: Diálogos para ações importantes
- **Toasts**: Notificações não-intrusivas

## 🔌 Integração com Backend

A aplicação se conecta ao backend Python existente via API REST. Todos os dados são sincronizados automaticamente:

1. **Sincronização**: Ao carregar a página, a aplicação busca dados do backend
2. **Offline**: Se o backend estiver offline, a aplicação exibe um aviso
3. **Ações**: Todas as ações (criar rolo, fechar, revisar) são enviadas ao backend

## 📊 Fluxo de Dados

```
Frontend (Flask/Jinja2)
    ↓
/api/* endpoints (Flask)
    ↓
Backend Python (Flask/FastAPI)
    ↓
Database
```

## 🛠️ Desenvolvimento

### Adicionar Nova Página

1. Criar template em `app/templates/nova_pagina.html`
2. Estender `base.html`
3. Adicionar rota em `main.py`:
   ```python
   @app.route('/nova-pagina')
   def nova_pagina():
       return render_template('nova_pagina.html')
   ```
4. Adicionar link na sidebar em `base.html`

### Adicionar Novo Endpoint

```python
@app.route('/api/novo-endpoint')
def api_novo_endpoint():
    data = fetch_from_backend('/novo-endpoint')
    return jsonify(data or [])
```

## 🐛 Troubleshooting

### Erro: "Backend offline"
- Verifique se o backend Python está rodando em `http://localhost:5000`
- Edite `BACKEND_API_URL` em `.env`

### Erro: "Template not found"
- Certifique-se de que os templates estão em `app/templates/`
- Verifique o nome do arquivo (case-sensitive)

### Erro: "CORS error"
- O Flask-CORS está configurado para aceitar requisições de qualquer origem
- Se necessário, restrinja em `main.py`: `CORS(app, resources={r"/api/*": {...}})`

## 📝 Notas

- A aplicação usa **Jinja2** para templates (sintaxe similar a Django)
- Os estilos CSS são uma reprodução fiel da Interface_temp
- A lógica JavaScript é mínima (a maioria é renderizada no servidor)
- Suporta modo offline com dados do localStorage

## 🚀 Deploy

### Heroku

```bash
git init
heroku create nexor-app
git push heroku main
```

### Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação do projeto ou entre em contato com o time de desenvolvimento.

---

**Versão**: 1.0.0  
**Última atualização**: Março 2026  
**Status**: ✅ Pronto para produção
