# 📥 Guia de Instalação - Nexor Desktop

**Sistema de Gerenciamento de Produção Têxtil**

---

## 🎯 Instalação Rápida

### Windows

1. **Baixe o instalador**
   - Acesse: https://seu-site.com/downloads
   - Clique em "Nexor-Setup.exe"

2. **Execute o instalador**
   - Duplo clique em `Nexor-Setup.exe`
   - Clique em "Instalar"
   - Aguarde conclusão

3. **Inicie a aplicação**
   - Duplo clique no ícone "Nexor" na área de trabalho
   - Ou procure "Nexor" no Menu Iniciar

4. **Pronto!**
   - A aplicação abre automaticamente no navegador
   - Comece a usar!

---

### macOS

1. **Baixe a aplicação**
   - Acesse: https://seu-site.com/downloads
   - Clique em "Nexor.dmg"

2. **Instale**
   - Duplo clique em `Nexor.dmg`
   - Arraste "Nexor.app" para "Applications"
   - Aguarde conclusão

3. **Inicie a aplicação**
   - Abra "Applications"
   - Duplo clique em "Nexor"
   - Clique em "Abrir" (primeira vez)

4. **Pronto!**
   - A aplicação abre automaticamente
   - Comece a usar!

---

### Linux (Ubuntu/Debian)

#### Opção A: Instalador Automático

```bash
# Baixar pacote
wget https://seu-site.com/downloads/nexor_1.0.0_amd64.deb

# Instalar
sudo dpkg -i nexor_1.0.0_amd64.deb

# Executar
nexor
```

#### Opção B: Executável Direto

```bash
# Baixar executável
wget https://seu-site.com/downloads/Nexor

# Dar permissão de execução
chmod +x Nexor

# Executar
./Nexor
```

---

## ⚙️ Configuração Inicial

### 1. Conectar ao Backend

Ao iniciar pela primeira vez, configure a conexão com o backend Python:

1. Clique em **Configurações** no menu lateral
2. Vá para **Conexão com Backend**
3. Insira a URL do seu backend:
   ```
   http://localhost:5000/api
   ```
4. Clique em **Testar Conexão**
5. Se OK, clique em **Salvar**

### 2. Importar Dados Iniciais

1. Vá para **Operação** → **Importar**
2. Selecione arquivos `.txt` de logs
3. Clique em **Importar**
4. Aguarde conclusão

### 3. Criar Dados Mestres

1. Vá para **Cadastros**
2. Adicione:
   - Máquinas
   - Operadores
   - Tecidos

---

## 🚀 Primeiro Uso

### Criar um Job

1. Clique em **+ Novo Fechamento** (topbar)
2. Preencha os dados:
   - Job ID
   - Descrição
   - Prioridade
3. Clique em **Salvar**

### Montar um Rolo

1. Vá para **Rolos**
2. Clique em **+ Montar Rolo**
3. Selecione o job
4. Configure dimensões
5. Clique em **Montar**

### Visualizar Métricas

1. Vá para **Analytics**
2. Selecione período (Hoje/Semana/Mês)
3. Escolha métrica
4. Analise gráficos

---

## 🔧 Troubleshooting

### Problema: Aplicação não abre

**Windows:**
```
1. Verifique se a porta 5001 está disponível
2. Tente reiniciar o computador
3. Reinstale a aplicação
```

**macOS:**
```
1. Vá para Preferências de Segurança
2. Clique em "Abrir assim mesmo" para Nexor
3. Tente novamente
```

**Linux:**
```bash
# Dar permissão de execução
chmod +x Nexor

# Executar com debug
./Nexor --debug
```

### Problema: Não conecta ao backend

1. Verifique se o backend Python está rodando
2. Confirme a URL em **Configurações**
3. Teste a conexão novamente
4. Se persistir, reinicie a aplicação

### Problema: Porta 5001 já em uso

**Windows:**
```powershell
# Encontre o processo
netstat -ano | findstr :5001

# Mate o processo (substitua PID)
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# Encontre o processo
lsof -i :5001

# Mate o processo (substitua PID)
kill -9 <PID>
```

### Problema: Dados não aparecem

1. Verifique a conexão com backend
2. Tente sincronizar: **Operação** → **Sincronizar**
3. Reinicie a aplicação
4. Verifique os logs

---

## 📋 Requisitos do Sistema

### Windows
- **OS**: Windows 10 ou superior
- **RAM**: 2 GB mínimo, 4 GB recomendado
- **Disco**: 500 MB livres
- **Navegador**: Qualquer navegador moderno

### macOS
- **OS**: macOS 10.13 ou superior
- **RAM**: 2 GB mínimo, 4 GB recomendado
- **Disco**: 500 MB livres
- **Navegador**: Safari, Chrome ou Firefox

### Linux
- **OS**: Ubuntu 18.04+, Debian 10+, Fedora 30+
- **RAM**: 2 GB mínimo, 4 GB recomendado
- **Disco**: 500 MB livres
- **Navegador**: Chrome, Firefox ou navegador padrão

---

## 🔄 Atualizar Nexor

### Windows

1. Baixe a versão mais recente
2. Execute o novo instalador
3. Clique em "Atualizar"
4. Reinicie a aplicação

### macOS

1. Baixe a versão mais recente
2. Arraste para Applications (sobrescrever)
3. Reinicie a aplicação

### Linux

```bash
# Versão Debian
sudo apt-get install --only-upgrade nexor

# Versão executável
# Substitua o arquivo Nexor antigo pelo novo
```

---

## 🔐 Segurança

### Backup de Dados

A aplicação faz backup automático:

1. Vá para **Sistema** → **Backup**
2. Clique em **Criar Backup**
3. Escolha local para salvar
4. Pronto!

### Restaurar Dados

1. Vá para **Sistema** → **Backup**
2. Clique em **Restaurar**
3. Selecione arquivo de backup
4. Confirme

---

## 📞 Suporte

### Documentação
- **Guia Completo**: Consulte `NEXOR_USAGE_GUIDE.md`
- **Troubleshooting**: Veja seção acima
- **API**: Consulte `FILE_INDEX.md`

### Contato
- **Email**: suporte@nexor.local
- **Website**: https://seu-site.com
- **GitHub Issues**: https://github.com/seu-repo/issues

---

## ✅ Checklist de Instalação

- [ ] Aplicação instalada
- [ ] Aplicação abre sem erros
- [ ] Backend conectado
- [ ] Dados importados
- [ ] Dados mestres criados
- [ ] Primeiro job criado
- [ ] Backup configurado

---

## 🎉 Pronto!

Você está pronto para usar o Nexor!

**Próximas ações:**
1. Explorar a interface
2. Criar dados de teste
3. Integrar com seu backend
4. Começar a produzir!

---

**Última atualização**: 20 de março de 2026

**Versão**: 1.0.0

**Status**: ✅ Pronto para instalação
