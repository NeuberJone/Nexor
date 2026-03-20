# ⚡ Guia Rápido de Compilação - Nexor

**Compilar em 3 passos!**

---

## 🪟 Windows

### Opção 1: Script Automático (Recomendado)

```batch
# Duplo clique em compile.bat
# Escolha opção 1 ou 2
# Pronto!
```

### Opção 2: Linha de Comando

```batch
# Abra PowerShell ou CMD na pasta do projeto

# 1. Instalar dependências
pip install -r requirements.txt

# 2. Compilar
pyinstaller --onefile --windowed --name=Nexor --icon=app/static/icon.ico nexor.spec

# 3. Resultado
# dist/Nexor.exe
```

### Opção 3: Com Instalador NSIS

```batch
# 1. Instale NSIS: https://nsis.sourceforge.io/

# 2. Execute compile.bat
# Escolha opção 2

# 3. Resultado
# Nexor-Setup.exe
```

---

## 🍎 macOS

### Script Automático

```bash
# Abra Terminal na pasta do projeto

# Dar permissão de execução
chmod +x compile.sh

# Executar
./compile.sh

# Escolha opção 1 ou 3
```

### Linha de Comando

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Compilar
pyinstaller --onefile --windowed --name=Nexor --icon=app/static/icon.icns nexor.spec

# 3. Resultado
# dist/Nexor.app
```

### Criar DMG (Imagem de Disco)

```bash
# Após compilar
hdiutil create -volname "Nexor" -srcfolder dist/Nexor.app -ov -format UDZO Nexor.dmg

# Resultado
# Nexor.dmg
```

---

## 🐧 Linux

### Script Automático

```bash
# Abra Terminal na pasta do projeto

# Dar permissão de execução
chmod +x compile.sh

# Executar
./compile.sh

# Escolha opção 1 ou 4
```

### Linha de Comando

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Compilar
pyinstaller --onefile --windowed --name=Nexor nexor.spec

# 3. Resultado
# dist/Nexor
```

### Criar Pacote DEB

```bash
# Criar estrutura
mkdir -p nexor-deb/usr/bin
mkdir -p nexor-deb/DEBIAN

# Copiar executável
cp dist/Nexor nexor-deb/usr/bin/

# Criar control file
cat > nexor-deb/DEBIAN/control << EOF
Package: nexor
Version: 1.0.0
Architecture: amd64
Maintainer: Seu Nome <seu@email.com>
Description: Sistema de Produção Têxtil
EOF

# Criar pacote
dpkg-deb --build nexor-deb nexor_1.0.0_amd64.deb

# Resultado
# nexor_1.0.0_amd64.deb
```

---

## 📋 Checklist Rápido

- [ ] Python 3.11+ instalado
- [ ] Dependências instaladas: `pip install -r requirements.txt`
- [ ] Arquivo `nexor.spec` presente
- [ ] Arquivo `app_desktop.py` presente
- [ ] Ícone em `app/static/icon.ico` (Windows)
- [ ] Ícone em `app/static/icon.icns` (macOS)

---

## 🚀 Compilar Agora

### Windows
```batch
compile.bat
```

### macOS/Linux
```bash
chmod +x compile.sh
./compile.sh
```

---

## 📦 Resultado

| SO | Arquivo | Tamanho |
|----|---------|--------|
| Windows | `dist/Nexor.exe` | ~150 MB |
| macOS | `dist/Nexor.app` | ~180 MB |
| Linux | `dist/Nexor` | ~140 MB |

---

## ⚙️ Troubleshooting Rápido

### "PyInstaller não encontrado"
```bash
pip install pyinstaller
```

### "Módulo não encontrado"
- Verifique `nexor.spec`
- Adicione ao `hiddenimports`

### "Ícone não encontrado"
- Crie arquivo vazio: `touch app/static/icon.ico`
- Ou remova `--icon` do comando

### "Porta 5001 em uso"
```bash
# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5001
kill -9 <PID>
```

---

## 💡 Dicas

1. **Compilação mais rápida**: Use `--onedir` em vez de `--onefile`
2. **Arquivo menor**: Remova `--upx` do spec
3. **Debug**: Adicione `console=True` no spec
4. **Múltiplas plataformas**: Compile em cada SO

---

## 🎁 Próximos Passos

1. ✅ Compilar executável
2. ✅ Testar em máquina limpa
3. ✅ Criar instalador (opcional)
4. ✅ Distribuir!

---

**Pronto! Agora é só compilar! 🎉**
