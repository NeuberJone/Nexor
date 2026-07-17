# Nexor

> Plataforma desktop local-first para operação, rastreabilidade e auditoria de produção têxtil.

![Windows](https://img.shields.io/badge/Windows-10%20%2F%2011-0078D6?style=for-the-badge&logo=windows)
![.NET](https://img.shields.io/badge/.NET-8.0-512BD4?style=for-the-badge&logo=dotnet)
![WPF](https://img.shields.io/badge/UI-WPF-5C2D91?style=for-the-badge)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite)
![Version](https://img.shields.io/badge/version-0.2.8-16A34A?style=for-the-badge)

---

## Sobre

O **Nexor** é um sistema desktop desenvolvido para centralizar e organizar o fluxo operacional da produção têxtil.

O projeto nasceu com foco em substituir processos manuais e ferramentas isoladas por um ambiente único, permitindo importar registros de impressão, organizar informações operacionais, fechar rolos de produção, gerar relatórios e consultar todo o histórico posteriormente.

A aplicação é desenvolvida em **C#**, **.NET 8**, **WPF** e **SQLite**, utilizando uma arquitetura em camadas voltada para crescimento de longo prazo.

---

## Objetivos

O Nexor foi projetado para:

- importar registros de impressão;
- evitar duplicidades;
- interpretar dados operacionais;
- organizar itens por ordem de impressão;
- calcular metragem real;
- montar e fechar rolos;
- gerar relatórios PDF;
- gerar imagens espelhadas para impressão;
- armazenar histórico local;
- localizar rapidamente qualquer produção anterior;
- permitir reexportação de documentos;
- servir como base para planejamento, estoque e analytics futuramente.

---

# Estado do Projeto

Versão atual:

**0.2.8**

## Implementado

- Arquitetura em C#
- .NET 8
- WPF
- SQLite
- Navegação principal
- Sidebar
- Topbar
- Barra de Status
- Temas
- Persistência das configurações
- Estrutura de domínio
- Estrutura da aplicação
- Estrutura de infraestrutura
- Parser inicial
- Fingerprint SHA-256
- Banco SQLite
- Testes iniciais
- Estrutura de build
- Estrutura do instalador

## Em desenvolvimento

- Importação pela interface
- Operação
- Fechamento de rolos
- Consulta de rolos
- Reexportação
- PDF
- JPG Mirror
- Auditoria
- Melhorias de UX

## Planejado

- Cadastros
- Planejamento
- Estoque
- Analytics
- Sincronização
- Backup
- Multiestação

---

# Fluxo Operacional

O fluxo principal do Nexor será:

```text
Importar registros

↓

Interpretar registros

↓

Validar

↓

Eliminar duplicidades

↓

Selecionar itens

↓

Montar o rolo

↓

Revisar

↓

Fechar

↓

Salvar

↓

Exportar

↓

Consultar

↓

Reexportar
```

---

# Regras Operacionais

## Ordenação

Os registros são organizados pelo horário de término (`EndTime`).

O último item impresso aparece primeiro.

---

## Agrupamento

O agrupamento é feito por blocos consecutivos de tecido.

Caso outro tecido apareça entre dois registros iguais, inicia-se um novo bloco.

---

## Metragem

A metragem utilizada é:

```text
HeightMM / 1000
```

O campo `VPositionMM` representa apenas deslocamento.

---

## Duplicidade

Cada registro recebe um fingerprint SHA-256.

Arquivos já importados não são processados novamente.

---

## Persistência

Após o fechamento do rolo:

- composição fica congelada;
- histórico permanece disponível;
- exportações futuras utilizam os dados persistidos.

---

# Arquitetura

```
Nexor.Desktop

↓

Nexor.Application

↓

Nexor.Domain

↑

Nexor.Infrastructure

↓

SQLite

↓

Nexor.Reporting
```

---

## Camadas

### Nexor.Desktop

Responsável pela interface WPF.

Contém:

- Views
- ViewModels
- Temas
- Navegação
- Componentes
- Dialogs

---

### Nexor.Application

Responsável pelos casos de uso.

Contém:

- Importação
- Operação
- Fechamento
- Consulta
- Exportação
- Configurações

---

### Nexor.Domain

Responsável pelas regras de negócio.

Contém:

- Entidades
- Value Objects
- Regras
- Estados
- Interfaces

---

### Nexor.Infrastructure

Responsável por:

- SQLite
- Parsing
- Sistema de Arquivos
- Logging
- Configurações
- Repositórios

---

### Nexor.Reporting

Responsável por:

- PDF
- JPG Mirror
- Templates
- Relatórios

---

# Estrutura do Projeto

```text
Nexor
│
├── docs
├── installer
├── legacy
├── dist
├── src
│   ├── Nexor.Desktop
│   ├── Nexor.Application
│   ├── Nexor.Domain
│   ├── Nexor.Infrastructure
│   └── Nexor.Reporting
│
├── tests
│
├── README.md
├── CHANGELOG.md
├── LICENSE.md
└── Nexor.sln
```

---

# Referências

## Projeto Jocasta

O Nexor utiliza como referência funcional:

- PXPrintLogs
- PXSearchOrders

As regras de negócio são inspiradas nesses módulos.

A arquitetura Python não é reutilizada.

---

## ListForge

O ListForge é utilizado apenas como referência visual.

Foram aproveitados conceitos como:

- Sidebar
- Topbar
- Barra de Status
- Organização visual
- Temas
- Experiência desktop

A lógica de negócio permanece totalmente independente.

---

# Screenshots

As imagens da interface serão adicionadas após estabilização da versão inicial.

Estrutura prevista:

```text
docs/screenshots/

01-home.png

02-operacao.png

03-rolos.png

04-configuracoes.png

05-sobre.png
```

---

# Banco de Dados

O Nexor utiliza SQLite.

O banco é criado automaticamente na primeira execução.

Diretório padrão:

```text
%LOCALAPPDATA%\Nexor
```

---

# Temas

Temas disponíveis:

- Nexor Dark
- Nexor Light
- SISBolt

Os temas utilizam ResourceDictionary.

---

# Requisitos

- Windows 10 ou superior
- Windows x64
- .NET 8 SDK (desenvolvimento)
- Visual Studio 2022 ou Rider

As versões distribuídas serão **Self-Contained**.

---

# Executando

Restaurar dependências:

```powershell
dotnet restore
```

Executar:

```powershell
dotnet run --project src/Nexor.Desktop
```

Build:

```powershell
dotnet build -c Release
```

Testes:

```powershell
dotnet test
```

---

# Distribuição

Os artefatos ficam organizados por versão.

```text
dist/

└── 0.2.8
    ├── onefile
    ├── trial
    ├── installable
    └── installer
```

Exemplo:

```
Nexor-v0.2.8.exe

Nexor-Trial-v0.2.8.exe

Nexor-Setup-v0.2.8.exe
```

---

# Documentação

A documentação completa encontra-se em:

- Architecture
- Roadmap
- Data Model
- Functional Specification
- UI/UX Specification
- Wireframe Specification
- Installation Guide

---

# Roadmap

## Fase 1

Base Operacional

- Parser
- Domínio
- SQLite
- Importação

---

## Fase 2

Operação

- Fechamento
- PDF
- JPG Mirror

---

## Fase 3

Consulta

- Pesquisa
- Auditoria
- Reexportação

---

## Fase 4

Cadastros

- Operadores
- Máquinas
- Tecidos
- Aliases

---

## Fase 5

Planejamento

---

## Fase 6

Estoque

---

## Fase 7

Analytics

---

## Fase 8

Arquitetura Híbrida

---

# Princípios

O Nexor segue cinco princípios fundamentais:

- Local-First
- Simplicidade
- Rastreabilidade
- Domínio antes da Interface
- Crescimento Controlado

---

# Implementação Anterior

A implementação Python permanece preservada temporariamente em:

```text
legacy/Nexor-Python-Legacy
```

Ela é utilizada apenas como referência durante a migração.

---

# Licença

O Nexor é um software proprietário.

Consulte:

**LICENSE.md**

---

# Changelog

Histórico completo de alterações:

**CHANGELOG.md**

---

# Autor

**Neuber Jone Avelar Queiroz**

---

# Status

🚧 Desenvolvimento ativo

Prioridade atual:

```text
Importar

↓

Montar

↓

Fechar

↓

Exportar

↓

Consultar

↓

Reexportar
```
