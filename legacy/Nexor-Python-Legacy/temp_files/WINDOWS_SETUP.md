# 🪟 Guia de Instalação - Windows

**Nexor - Sistema de Gerenciamento de Produção Têxtil**

---

## ⚠️ Problemas Comuns no Windows

Você pode encontrar alguns erros ao tentar instalar no Windows. Este guia fornece soluções para cada um.

---

## 🔧 Solução 1: Python Não Encontrado

### Erro

```
Python não foi encontrado; executar sem argumentos para instalar do Microsoft Store
```

### Solução

**Opção A: Instalar Python via Microsoft Store (Recomendado)**

1. Abra o **Microsoft Store**

1. Procure por **Python 3.11** ou **Python 3.12**

1. Clique em **Instalar**

1. Aguarde a instalação

1. Feche e reabra o PowerShell

1. Verifique: `python --version`

**Opção B: Desabilitar o atalho do Microsoft Store**

Se você já tem Python instalado mas o Windows está oferecendo o Microsoft Store:

1. Abra **Configurações** (Win + I)

1. Vá para **Aplicativos** → **Configurações avançadas do aplicativo**

1. Procure por **Aliases de execução do aplicativo**

1. Desabilite `python.exe` e `python3.exe`

1. Reabra o PowerShell

**Opção C: Instalar Python.org (Alternativa)**

1. Visite [https://www.python.org/downloads/](https://www.python.org/downloads/)

1. Baixe **Python 3.11** ou **3.12**

1. Execute o instalador

1. ✅ **IMPORTANTE**: Marque "Add Python to PATH"

1. Clique em **Install Now**

---

## 🔧 Solução 2: Comando 'source' Não Reconhecido

### Erro

```
source : O termo 'source' não é reconhecido como nome de cmdlet
```

### Solução

No Windows PowerShell, o comando é **diferente**:

**Ative o ambiente virtual com:**

```
# Windows PowerShell
venv\Scripts\Activate.ps1

# ou CMD (Command Prompt )
venv\Scripts\activate.bat
```

**Se receber erro de política de execução:**

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente:

```
venv\Scripts\Activate.ps1
```

---

## 🔧 Solução 3: Erro ao Instalar Pillow

### Erro

```
ERROR: Failed to build 'Pillow' when getting requirements to build wheel
KeyError: '__version__'
```

### Solução

Este erro ocorre com versões antigas do Pillow no Python 3.13+.

**Opção A: Atualizar Pillow (Recomendado)**

Edite o arquivo `requirements.txt` e altere:

```
- Pillow==10.1.0
+ Pillow==11.0.0
```

Depois instale novamente:

```
pip install -r requirements.txt
```

**Opção B: Usar versão pré-compilada**

```
pip install --only-binary :all: Pillow==10.1.0
```

**Opção C: Usar Python 3.11 (Mais compatível)**

Se você tem Python 3.13, considere usar Python 3.11:

1. Instale Python 3.11 via Microsoft Store

1. Crie novo venv: `python3.11 -m venv venv`

1. Ative: `venv\Scripts\Activate.ps1`

1. Instale: `pip install -r requirements.txt`

---

## ✅ Instalação Completa no Windows

Siga estes passos na ordem:

### 1. Extrair o Projeto

```
# Extraia o nexor-app-complete.zip
# Navegue até a pasta
cd C:\Projetos\nexor-app-complete\nexor-flask
```

### 2. Criar Ambiente Virtual

```
python -m venv venv
```

### 3. Ativar Ambiente Virtual

```
# PowerShell
venv\Scripts\Activate.ps1

# Se receber erro de política:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1

# Se usar CMD (Command Prompt):
venv\Scripts\activate.bat
```

Você deve ver `(venv)` no início da linha de comando.

### 4. Instalar Dependências

```
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Se houver erro com Pillow, use:

```
pip install -r requirements.txt --only-binary :all:
```

### 5. Configurar Ambiente

Crie um arquivo `.env` na raiz do projeto:

```
FLASK_APP=main.py
FLASK_ENV=development
DEBUG=True
PORT=5001
BACKEND_API_URL=http://localhost:5000/api
```

### 6. Executar a Aplicação

```
python main.py
```

Você deve ver:

```
 * Running on http://127.0.0.1:5001
 * Press CTRL+C to quit
```

### 7. Acessar no Navegador

Abra seu navegador e acesse:

```
http://localhost:5001
```

---

## 🐛 Troubleshooting Windows

### Problema: Porta 5001 já em uso

```
# Encontre o processo usando a porta
netstat -ano | findstr :5001

# Mate o processo (substitua PID )
taskkill /PID <PID> /F

# Ou use outra porta no .env:
# PORT=5002
```

### Problema: Permissão negada ao ativar venv

```
# Tente com Bypass
powershell -ExecutionPolicy Bypass -File venv\Scripts\Activate.ps1

# Ou use CMD:
cmd /c venv\Scripts\activate.bat
```

### Problema: Módulo não encontrado

```
# Verifique se o venv está ativado (deve ter (venv) no prompt)
# Se não, ative novamente:
venv\Scripts\Activate.ps1

# Reinstale as dependências:
pip install -r requirements.txt
```

### Problema: Backend não conecta

```
# Verifique se o backend Python está rodando em http://localhost:5000
# Se não, inicie em outro terminal:
# (Você precisará ter o backend Python instalado )

# Edite o .env para apontar para a URL correta:
# BACKEND_API_URL=http://localhost:5000/api
```

---

## 📋 Checklist de Instalação

- [x] Python 3.11+ instalado

- [ ] Projeto extraído

- [ ] Ambiente virtual criado (`venv` )

- [ ] Ambiente virtual ativado (vê `(venv)` no prompt?)

- [ ] Dependências instaladas (`pip install -r requirements.txt`)

- [ ] Arquivo `.env` criado

- [ ] Aplicação iniciada (`python main.py`)

- [ ] Navegador acessa `http://localhost:5001`

---

## 🚀 Próximas Ações

Após a instalação bem-sucedida:

1. **Leia a documentação**: `NEXOR_USAGE_GUIDE.md`

1. **Explore a interface**: Acesse `http://localhost:5001`

1. **Configure o backend**: Aponte para seu backend Python

1. **Teste as funcionalidades**: Crie jobs, rolos, etc.

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique a seção de **Troubleshooting** acima

1. Consulte `NEXOR_USAGE_GUIDE.md`

1. Verifique os logs da aplicação

---

**Última atualização**: 20 de março de 2026

**Versão**: 1.0.0

**Status**: ✅ Pronto para Windows

