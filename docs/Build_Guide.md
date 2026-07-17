# Nexor — Build Guide

## 1. Objetivo

Este documento descreve o processo oficial de compilação do Nexor.

O objetivo é garantir que qualquer desenvolvedor consiga gerar uma versão reproduzível da aplicação utilizando a mesma estrutura e os mesmos comandos.

Este documento trata apenas do processo de **build**.

O processo completo de publicação encontra-se em:

```
docs/Release_Process.md
```

---

# 2. Ambiente de desenvolvimento

O Nexor é desenvolvido utilizando:

- C#
- .NET 8
- WPF
- SQLite
- Windows x64

---

# 3. Ferramentas necessárias

- Visual Studio 2022 (recomendado)
- .NET SDK 8
- Git
- PowerShell
- Inno Setup (para geração do instalador)

---

# 4. Estrutura do projeto

```
Nexor.sln

src/
tests/
installer/
docs/
```

Toda compilação deve ser iniciada pela solução principal.

---

# 5. Restaurar dependências

Antes de qualquer build:

```powershell
dotnet restore Nexor.sln
```

A restauração deve concluir sem erros.

---

# 6. Build

Executar:

```powershell
dotnet build Nexor.sln -c Release
```

Critérios esperados:

- sem erros
- warnings revisados
- todos os projetos compilados

---

# 7. Testes

Executar:

```powershell
dotnet test Nexor.sln -c Release
```

O build oficial não deve ser publicado caso existam testes críticos falhando.

---

# 8. Publicação OneFile

Exemplo:

```powershell
dotnet publish src/Nexor.Desktop/Nexor.Desktop.csproj ^
-c Release ^
-r win-x64 ^
--self-contained true ^
-p:PublishSingleFile=true
```

O executável final deverá possuir o formato:

```
Nexor-vX.Y.Z.exe
```

---

# 9. Publicação Trial

A versão Trial utiliza o mesmo processo de publicação, porém utilizando a configuração Trial adotada pelo projeto.

Nome esperado:

```
Nexor-Trial-vX.Y.Z.exe
```

A Trial deve permanecer completamente separada da versão oficial.

---

# 10. Publicação instalável

Também deve ser gerada uma publicação tradicional contendo todos os arquivos necessários.

Destino sugerido:

```
dist/X.Y.Z/installable
```

---

# 11. Instalador

O instalador utiliza Inno Setup.

Arquivo esperado:

```
installer/Nexor.iss
```

Compilação:

```powershell
ISCC.exe installer\Nexor.iss
```

Saída:

```
Nexor-Setup-vX.Y.Z.exe
```

---

# 12. Estrutura dos artefatos

```
dist/

└── X.Y.Z/

    ├── onefile/

    │      Nexor-vX.Y.Z.exe

    │

    ├── trial/

    │      Nexor-Trial-vX.Y.Z.exe

    │

    ├── installable/

    │      ...

    │

    └── installer/

           Nexor-Setup-vX.Y.Z.exe
```

---

# 13. Regras

Sempre:

- manter builds antigos
- criar pasta da versão
- não sobrescrever releases anteriores
- incluir a versão no nome dos arquivos
- manter Trial separada
- gerar apenas os artefatos oficiais

Nunca:

- apagar a pasta dist
- publicar Debug
- distribuir arquivos temporários
- distribuir bancos de desenvolvimento
- distribuir logs de testes

---

# 14. Verificações após o build

Confirmar:

- aplicativo abre
- versão correta
- tema funciona
- banco SQLite é criado
- configurações são persistidas
- tela Sobre exibe a versão correta

Quando o núcleo operacional estiver completo, validar também:

- importação
- fechamento
- exportação
- consulta
- reexportação

---

# 15. Problemas comuns

## Restore falhou

Verificar:

- SDK instalado
- conexão
- NuGet

---

## Build falhou

Verificar:

- referências
- recursos WPF
- projetos não compilados

---

## Publish falhou

Verificar:

- runtime
- permissões
- espaço em disco

---

## Instalador não gerou

Verificar:

- Inno Setup
- caminho do arquivo .iss
- permissões

---

# 16. Checklist de Build

Antes de considerar o build concluído:

- [ ] Restore executado
- [ ] Build Release executado
- [ ] Testes aprovados
- [ ] OneFile oficial gerado
- [ ] OneFile Trial gerado
- [ ] Publicação instalável gerada
- [ ] Instalador gerado
- [ ] Versão correta em todos os artefatos
- [ ] Nenhum arquivo sensível incluído
- [ ] Estrutura da pasta dist validada

---

# 17. Considerações

O objetivo do Build Guide é garantir que qualquer desenvolvedor consiga gerar exatamente os mesmos artefatos utilizando o mesmo procedimento.

O processo de publicação, documentação, changelog, versionamento, GitHub Release e checklist final é tratado separadamente em:

```
docs/Release_Process.md
```