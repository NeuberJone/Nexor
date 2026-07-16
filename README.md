# Nexor

Nexor é um aplicativo desktop local-first para operação de produção têxtil. A implementação oficial está sendo reconstruída em C# com .NET 8, WPF, Windows x64 e SQLite.

Versão atual: **0.2.6** — seleção ativa e inativa com contraste correto.

## Estado atual

Já implementado:

- solução separada em Desktop, Application, Domain, Infrastructure e Reporting;
- shell WPF com sidebar, topbar, conteúdo, status e navegação MVVM para Home, Operação, Rolos, Configurações e Sobre;
- temas Nexor Dark, Nexor Light e SISBolt em `ResourceDictionary`, com troca imediata e preferência persistida;
- entidades iniciais de logs, rolos, itens e eventos;
- parser inicial para logs no formato de seções do PX, incluindo `EndTime`, documento, `HeightMM` e `VPositionMM`;
- cálculo de metragem real somente por `HeightMM / 1000`;
- ordenação por última impressão, agrupamento consecutivo por tecido e prevenção de duplicidade por SHA-256;
- SQLite com criação automática, versão explícita de schema e repositórios;
- testes automatizados de domínio, aplicação, parsing e persistência.

Planejado:

- importação por arquivo, pasta e arrastar-e-soltar na interface;
- fluxo completo de fechamento de rolos;
- consulta detalhada, filtros e reexportação;
- PDF completo/resumido e JPG espelhado;
- telas funcionais de configurações e refinamento de temas;
- instalador validado em ambiente limpo.

Planejamento, Estoque, Cadastros e Analytics permanecem fora da interface desta etapa; entrarão somente quando houver casos de uso reais.

## Referências

O núcleo funcional é baseado nas regras observadas no PXPrintLogs e PXSearchOrders do Projeto Jocasta. O ListForge serve somente como referência de composição visual; nenhum recurso de listas, Trial, licença ou texto daquele produto integra o Nexor.

O código Python anterior está preservado temporariamente, com sua estrutura original, em [`legacy/Nexor-Python-Legacy`](legacy/Nexor-Python-Legacy). Ele é referência histórica e não compõe a aplicação oficial.

## Estrutura

```text
src/       projetos da aplicação
tests/     testes automatizados
docs/      especificações e decisões técnicas
installer/ definição do instalador
legacy/    implementação Python preservada
dist/      artefatos separados por versão
```

## Executar

Requer Windows e SDK do .NET 8:

```powershell
dotnet restore Nexor.sln
dotnet run --project src/Nexor.Desktop/Nexor.Desktop.csproj
```

O banco é criado automaticamente em `%LOCALAPPDATA%/Nexor/nexor.db` no primeiro início. Nenhum banco do Jocasta é alterado.

## Testes

```powershell
dotnet build Nexor.sln -c Release
dotnet test Nexor.sln -c Release
```

## Screenshots

Ainda não há screenshots rastreados que representem fielmente a nova interface WPF. As imagens serão adicionadas em `docs/screenshots/` após a validação visual das telas; o README não aponta para arquivos inexistentes nem reutiliza imagens do legado ou do ListForge.

## Distribuição

Os artefatos da versão 0.2.6 permanecem em `dist/0.2.6/`, sem sobrescrever versões anteriores. A edição Trial é um build separado, identificado na interface, com avaliação local de 30 dias.

Consulte também [arquitetura](docs/architecture.md), [especificação funcional](docs/Functional_Spec_Operational_Core.md), [UI/UX](docs/UI_UX_Specification.md) e [instalação](docs/installation.md).
