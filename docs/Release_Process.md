# Nexor — Release Process

## 1. Objetivo

Este documento descreve o processo oficial de publicação (Release) do Nexor.

Seu objetivo é garantir que todas as versões sejam distribuídas de forma consistente, rastreável e reproduzível.

O processo de compilação encontra-se em:

```
docs/Build_Guide.md
```

Este documento cobre somente as etapas necessárias para transformar um build validado em uma versão oficial.

---

# 2. Política de versionamento

O Nexor utiliza Versionamento Semântico.

Formato:

```
MAJOR.MINOR.PATCH
```

Exemplo:

```
0.3.0
```

## MAJOR

Mudanças incompatíveis.

Exemplo:

```
1.0.0 → 2.0.0
```

---

## MINOR

Novas funcionalidades compatíveis.

Exemplo:

```
0.2.6 → 0.3.0
```

---

## PATCH

Correções.

Exemplo:

```
0.2.6 → 0.2.7
```

---

# 3. Atualização da versão

Antes da release, atualizar a versão em:

- projeto principal
- AssemblyVersion
- FileVersion
- tela Sobre
- README
- CHANGELOG
- documentação relevante
- instalador

Todas as referências devem possuir exatamente o mesmo número.

---

# 4. Atualização da documentação

Sempre revisar:

- README.md
- CHANGELOG.md
- docs/installation.md
- docs/roadmap.md
- docs/architecture.md
- docs/Data_Model.md
- docs/Functional_Spec_Operational_Core.md

Atualizar apenas documentos afetados pela release.

---

# 5. Atualização do CHANGELOG

Mover os itens concluídos da seção **Unreleased** para uma nova versão.

Exemplo:

```markdown
## [0.3.0] - 2026-08-15

### Added

- Importação de arquivos.

### Changed

- Novo parser.

### Fixed

- Correção na persistência.
```

Nunca adicionar funcionalidades que ainda não existam.

---

# 6. Atualização do README

Confirmar:

- versão atual
- screenshots
- funcionalidades
- limitações
- roadmap resumido
- instruções de instalação
- requisitos

---

# 7. Atualização dos screenshots

Sempre que houver alteração significativa da interface:

Atualizar:

```
docs/screenshots/
```

Arquivos recomendados:

```
01-home.png

02-operacao.png

03-rolos.png

04-configuracoes.png

05-sobre.png
```

Os screenshots devem refletir exatamente a versão publicada.

---

# 8. Organização dos artefatos

Cada release deve possuir sua própria pasta.

Exemplo:

```
dist/

└── 0.3.0/

    ├── onefile/

    ├── trial/

    ├── installable/

    └── installer/
```

Nunca sobrescrever versões anteriores.

---

# 9. Nome dos arquivos

Executável oficial:

```
Nexor-v0.3.0.exe
```

Trial:

```
Nexor-Trial-v0.3.0.exe
```

Instalador:

```
Nexor-Setup-v0.3.0.exe
```

---

# 10. Testes manuais obrigatórios

Antes da publicação:

- abrir aplicação
- navegar pelas telas
- alterar tema
- reiniciar
- verificar persistência
- abrir Configurações
- abrir Sobre
- validar versão

Quando o núcleo operacional estiver concluído:

- importar
- montar rolo
- fechar
- exportar
- consultar
- reexportar

---

# 11. Testes da versão Trial

Confirmar:

- identificação visual
- período restante
- bloqueio ao término
- funcionamento antes do vencimento
- versão oficial continua sem bloqueio

---

# 12. Teste de atualização

Instalar uma versão anterior.

Atualizar para a nova.

Confirmar:

- banco preservado
- configurações preservadas
- tema preservado
- versão atualizada
- migrations executadas

---

# 13. Teste em ambiente limpo

Validar em um computador sem:

- Visual Studio
- SDK do .NET
- Python

Confirmar:

- instalação
- abertura
- criação do banco
- criação das configurações
- criação dos logs

---

# 14. Arquivos proibidos

Nunca publicar:

- código-fonte
- banco de desenvolvimento
- arquivos temporários
- logs
- tokens
- chaves privadas
- arquivos pessoais
- conteúdo da pasta legacy

---

# 15. Hash SHA-256

Gerar hash dos arquivos distribuídos.

Exemplo:

```powershell
Get-FileHash `
"Nexor-v0.3.0.exe" `
-Algorithm SHA256
```

Repetir para:

- Trial
- instalador

---

# 16. Commit da release

Após validar a versão:

```
chore(release): prepare version 0.3.0
```

Esse commit deve conter:

- atualização de versão
- changelog
- documentação
- ajustes finais

---

# 17. Tag

Criar tag:

```bash
git tag -a v0.3.0 -m "Nexor 0.3.0"
```

Enviar:

```bash
git push origin v0.3.0
```

---

# 18. GitHub Release

Título:

```
Nexor v0.3.0
```

Descrição contendo:

- novidades
- melhorias
- correções
- limitações conhecidas

Anexar:

- OneFile
- Trial
- Instalador

---

# 19. Rollback

Caso uma release apresente problema crítico:

- interromper distribuição
- preservar os artefatos
- documentar o problema
- publicar uma nova versão PATCH

Nunca substituir arquivos mantendo o mesmo número de versão.

Correto:

```
0.3.0

↓

0.3.1
```

Nunca:

```
0.3.0

↓

0.3.0 (arquivo diferente)
```

---

# 20. Checklist Pré-Release

- [ ] versão atualizada
- [ ] CHANGELOG atualizado
- [ ] README atualizado
- [ ] documentação revisada
- [ ] Build Release aprovado
- [ ] testes aprovados
- [ ] artefatos gerados
- [ ] screenshots atualizados
- [ ] instalador validado
- [ ] Trial validada
- [ ] ambiente limpo validado

---

# 21. Checklist Pós-Release

- [ ] tag enviada
- [ ] release criada
- [ ] arquivos anexados
- [ ] hashes publicados
- [ ] README atualizado
- [ ] documentação sincronizada

---

# 22. Relatório da Release

Registrar:

- versão
- data
- branch
- commit
- SDK
- runtime
- testes executados
- artefatos gerados
- limitações conhecidas

---

# 23. Fluxo oficial

O processo oficial de publicação do Nexor segue a sequência:

```
Atualizar versão
        ↓
Atualizar documentação
        ↓
Executar Build
        ↓
Executar Testes
        ↓
Gerar artefatos
        ↓
Validar instalação
        ↓
Gerar hashes
        ↓
Commit
        ↓
Tag
        ↓
GitHub Release
```

Uma release somente deve ser considerada concluída após todas essas etapas terem sido executadas com sucesso.