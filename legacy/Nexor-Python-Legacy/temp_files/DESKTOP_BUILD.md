# 🖥️ Guia de Compilação - Nexor Desktop

**Transformar Nexor em aplicação desktop instalável**

---

## 📋 Visão Geral

Este guia explica como compilar o Nexor em uma aplicação desktop instalável para Windows, macOS e Linux usando PyInstaller.

### O que você vai obter

- ✅ **Executável Windows** (.exe) - Instalador com clique duplo
- ✅ **App macOS** (.app) - Aplicação nativa para Mac
- ✅ **Executável Linux** - Aplicação para Linux
- ✅ **Sem dependências externas** - Tudo bundled
- ✅ **Atalhos no menu** - Integração com SO

---

## 🔧 Pré-requisitos

### Todos os Sistemas

```bash
# Python 3.11+
python --version

# Instalar PyInstaller
pip install pyinstaller

# Instalar dependências do projeto
pip install -r requirements.txt
```

### Windows Adicional

- **NSIS** (para criar instalador) - https://nsis.sourceforge.io/
- **Visual C++ Build Tools** (opcional, para compilação otimizada)

### macOS Adicional

- **Xcode Command Line Tools**
  ```bash
  xcode-select --install
  ```

### Linux Adicional

```bash
# Debian/Ubuntu
sudo apt-get install build-essential python3-dev

# Fedora/RHEL
sudo dnf install gcc python3-devel
```

---

## 🚀 Compilação Rápida

### Opção 1: Script Automático (Recomendado)

```bash
# Executar o script de build
python build_installer.py

# Escolher opção:
# 1. Windows (.exe)
# 2. macOS (.app)
# 3. Linux (executável)
# 4. Todas as plataformas
```

### Opção 2: Comando Manual

```bash
# Windows
pyinstaller --onefile --windowed --name=Nexor app_desktop.py

# macOS
pyinstaller --onefile --windowed --name=Nexor app_desktop.py

# Linux
pyinstaller --onefile --windowed --name=Nexor app_desktop.py
```

---

## 📦 Compilação Detalhada por Plataforma

### Windows

#### 1. Compilar Executável

```bash
pyinstaller --onefile --windowed --name=Nexor --icon=app/static/icon.ico app_desktop.py
```

#### 2. Resultado

```
dist/
└── Nexor.exe  (executável único)
```

#### 3. Criar Instalador (Opcional)

Instale NSIS: https://nsis.sourceforge.io/

```bash
# Editar nexor_installer.nsi conforme necessário
makensis nexor_installer.nsi

# Resultado: Nexor-Setup.exe
```

#### 4. Distribuir

- **Opção A**: Compartilhar `Nexor.exe` diretamente
- **Opção B**: Criar instalador com `Nexor-Setup.exe`

---

### macOS

#### 1. Compilar App

```bash
pyinstaller --onefile --windowed --name=Nexor --icon=app/static/icon.icns app_desktop.py
```

#### 2. Resultado

```
dist/
└── Nexor.app/  (aplicação macOS)
```

#### 3. Criar DMG (Opcional)

```bash
# Criar imagem de disco
hdiutil create -volname "Nexor" -srcfolder dist/Nexor.app -ov -format UDZO Nexor.dmg
```

#### 4. Distribuir

- **Opção A**: Compartilhar `Nexor.app` (pasta)
- **Opção B**: Compartilhar `Nexor.dmg` (imagem de disco)

---

### Linux

#### 1. Compilar Executável

```bash
pyinstaller --onefile --windowed --name=Nexor app_desktop.py
```

#### 2. Resultado

```
dist/
└── Nexor  (executável)
```

#### 3. Criar Pacote DEB (Debian/Ubuntu)

Crie um script `create_deb.sh`:

```bash
#!/bin/bash
mkdir -p nexor-deb/usr/bin
mkdir -p nexor-deb/usr/share/applications
mkdir -p nexor-deb/DEBIAN

cp dist/Nexor nexor-deb/usr/bin/
chmod +x nexor-deb/usr/bin/Nexor

cat > nexor-deb/usr/share/applications/nexor.desktop << EOF
[Desktop Entry]
Name=Nexor
Exec=/usr/bin/Nexor
Type=Application
Icon=nexor
EOF

cat > nexor-deb/DEBIAN/control << EOF
Package: nexor
Version: 1.0.0
Architecture: amd64
Maintainer: Seu Nome <seu@email.com>
Description: Sistema de Produção Têxtil
EOF

dpkg-deb --build nexor-deb nexor_1.0.0_amd64.deb
```

#### 4. Distribuir

- **Opção A**: Compartilhar `Nexor` (executável)
- **Opção B**: Compartilhar `nexor_1.0.0_amd64.deb` (pacote)

---

## 🎨 Customização

### Adicionar Ícone

1. **Windows**: Converter imagem para `.ico`
   ```bash
   pip install pillow
   python -c "from PIL import Image; Image.open('icon.png').save('icon.ico')"
   ```

2. **macOS**: Converter imagem para `.icns`
   ```bash
   # Usar ferramenta online ou:
   # https://github.com/bitflag/png2icns
   ```

3. **Linux**: Usar `.png` diretamente

### Adicionar Dados

Edite o arquivo `.spec` para incluir arquivos adicionais:

```python
datas=[
    ('app/templates', 'app/templates'),
    ('app/static', 'app/static'),
    ('data/config.json', 'data'),
],
```

---

## 📊 Tamanho dos Executáveis

| Plataforma | Tamanho | Tempo Build |
|-----------|--------|-----------|
| Windows (.exe) | ~150 MB | 2-3 min |
| macOS (.app) | ~180 MB | 2-3 min |
| Linux | ~140 MB | 2-3 min |

---

## 🐛 Troubleshooting

### Erro: "PyInstaller não encontrado"

```bash
pip install pyinstaller
```

### Erro: "Módulo não encontrado"

Adicione ao arquivo `.spec`:

```python
hiddenimports=[
    'flask',
    'flask_cors',
    'requests',
    'jinja2',
    'werkzeug',
    'reportlab',
    'PIL',
],
```

### Erro: "Ícone não encontrado"

```bash
# Criar ícone padrão
touch app/static/icon.ico
```

### App não abre no macOS

```bash
# Remover quarentena
xattr -d com.apple.quarantine dist/Nexor.app
```

---

## 🔐 Assinatura de Código (Opcional)

### Windows

```bash
# Usar certificado de assinatura
signtool sign /f certificate.pfx /p password /t http://timestamp.server Nexor.exe
```

### macOS

```bash
# Assinar aplicação
codesign -s - dist/Nexor.app
```

---

## 📤 Distribuição

### Opção 1: GitHub Releases

1. Fazer upload dos executáveis
2. Criar release
3. Compartilhar link

### Opção 2: Website

```html
<a href="https://seu-site.com/downloads/Nexor.exe">
  Baixar para Windows
</a>
```

### Opção 3: Instalador

1. Criar instalador com NSIS/DMG/DEB
2. Fazer upload
3. Compartilhar

---

## ✅ Checklist de Build

- [ ] PyInstaller instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Ícone preparado (`.ico`, `.icns`, `.png`)
- [ ] Arquivo `app_desktop.py` presente
- [ ] Executar `python build_installer.py`
- [ ] Testar executável em máquina limpa
- [ ] Criar instalador (opcional)
- [ ] Fazer upload para distribuição

---

## 🚀 Próximas Ações

1. **Testar em máquina limpa** - Sem Python instalado
2. **Criar instalador** - Para distribuição profissional
3. **Assinatura de código** - Para confiança do usuário
4. **Distribuir** - GitHub, website, etc.

---

## 📞 Suporte

Para problemas:

1. Consulte a documentação do PyInstaller: https://pyinstaller.org/
2. Verifique os logs de build
3. Tente compilar com `--debug` para mais informações

---

**Última atualização**: 20 de março de 2026

**Versão**: 1.0.0

**Status**: ✅ Pronto para compilação
