# Nexor — Estrutura do Projeto

## 1. Objetivo

Este documento descreve a organização oficial do **Nexor**, as responsabilidades de cada diretório e as regras para inclusão de novos arquivos.

O objetivo é evitar:

- classes colocadas em camadas incorretas;
- duplicação de serviços;
- regras de negócio dentro da interface;
- dependências circulares;
- arquivos genéricos sem responsabilidade clara;
- crescimento desorganizado da solução.

A implementação oficial utiliza:

- C#;
- .NET 8;
- WPF;
- SQLite;
- arquitetura em camadas;
- MVVM;
- Windows x64.

---

# 2. Estrutura geral

A estrutura principal do repositório deve seguir a organização abaixo:

```text
Nexor/
├── .github/
│   └── workflows/
│
├── docs/
├── installer/
├── legacy/
├── dist/
│
├── src/
│   ├── Nexor.Desktop/
│   ├── Nexor.Application/
│   ├── Nexor.Domain/
│   ├── Nexor.Infrastructure/
│   └── Nexor.Reporting/
│
├── tests/
│   ├── Nexor.Domain.Tests/
│   ├── Nexor.Application.Tests/
│   └── Nexor.Infrastructure.Tests/
│
├── CHANGELOG.md
├── Directory.Build.props
├── LICENSE.md
├── Nexor.sln
└── README.md
```

A estrutura real do repositório deve ser respeitada.

Antes de criar um novo diretório, verifique se já existe uma área adequada para o arquivo.

---

# 3. Solução principal

Arquivo:

```text
Nexor.sln
```

A solução reúne os projetos oficiais da implementação em C#.

Ela deve incluir:

- aplicação desktop;
- camada de aplicação;
- domínio;
- infraestrutura;
- relatórios;
- testes.

Não devem ser adicionados à solução:

- código Python legado;
- arquivos da pasta `dist`;
- bancos locais;
- projetos temporários;
- ferramentas de teste descartáveis sem justificativa.

---

# 4. Diretório `src`

O diretório `src` contém o código oficial da aplicação.

```text
src/
├── Nexor.Desktop/
├── Nexor.Application/
├── Nexor.Domain/
├── Nexor.Infrastructure/
└── Nexor.Reporting/
```

Cada projeto possui responsabilidade específica.

---

# 5. `Nexor.Domain`

## 5.1 Objetivo

Representar as regras centrais do negócio.

O domínio deve permanecer independente de:

- WPF;
- SQLite;
- arquivos;
- relatórios;
- sistema operacional;
- configurações visuais;
- Trial;
- serviços externos.

---

## 5.2 Estrutura sugerida

```text
Nexor.Domain/
├── Entities/
├── Enums/
├── Events/
├── Exceptions/
├── Rules/
├── ValueObjects/
└── Nexor.Domain.csproj
```

---

## 5.3 `Entities`

Contém entidades com identidade e ciclo de vida.

Exemplos:

```text
ImportedLog.cs
PrintItem.cs
Roll.cs
RollItem.cs
RollEvent.cs
Machine.cs
Fabric.cs
FabricAlias.cs
ExportRecord.cs
```

Uma entidade deve:

- proteger suas invariantes;
- controlar mudanças críticas;
- evitar setters públicos irrestritos;
- não depender da interface;
- não executar persistência.

---

## 5.4 `Enums`

Contém estados e classificações finitas.

Exemplos:

```text
ImportedLogStatus.cs
PrintItemStatus.cs
RollStatus.cs
RollEventType.cs
ExportType.cs
ExportMode.cs
```

Enums devem representar estados reais.

Não criar enum apenas para substituir uma constante sem benefício.

---

## 5.5 `Events`

Contém eventos de domínio quando necessários.

Exemplos:

```text
RollClosedDomainEvent.cs
RollReopenedDomainEvent.cs
```

Eventos de domínio devem representar acontecimentos relevantes para o negócio.

Não confundir com eventos visuais WPF.

---

## 5.6 `Exceptions`

Contém exceções específicas do domínio.

Exemplos:

```text
DomainException.cs
InvalidRollStateException.cs
InvalidPrintedLengthException.cs
```

Não criar uma exceção diferente para cada mensagem simples.

---

## 5.7 `Rules`

Contém regras puras que não pertencem naturalmente a uma única entidade.

Exemplos:

```text
PrintedLengthCalculator.cs
ConsecutiveFabricGroupingRule.cs
RollCodeRule.cs
```

Antes de criar uma classe em `Rules`, confirme que a lógica não deveria estar em uma entidade ou value object.

---

## 5.8 `ValueObjects`

Contém conceitos representados por valor.

Possíveis exemplos:

```text
RollCode.cs
FileFingerprint.cs
PrintedLength.cs
MachineCode.cs
```

Value objects devem:

- ser imutáveis;
- validar o próprio valor;
- possuir igualdade por conteúdo;
- resolver um problema real.

---

# 6. `Nexor.Application`

## 6.1 Objetivo

Coordenar os casos de uso do sistema.

A camada de aplicação traduz uma intenção do usuário em uma sequência de operações.

Ela pode:

- carregar dados;
- validar uma solicitação;
- chamar regras do domínio;
- coordenar repositórios;
- iniciar transações;
- retornar resultados estruturados.

Ela não deve:

- executar SQL;
- abrir `MessageBox`;
- manipular controles WPF;
- depender de uma View;
- definir cores ou layout;
- conhecer caminhos físicos fixos.

---

## 6.2 Estrutura sugerida

```text
Nexor.Application/
├── Abstractions/
├── Common/
├── Imports/
├── Operations/
├── Rolls/
├── Exports/
├── Settings/
└── Nexor.Application.csproj
```

---

## 6.3 `Abstractions`

Contém contratos necessários para os casos de uso.

Exemplos:

```text
IImportedLogRepository.cs
IPrintItemRepository.cs
IRollRepository.cs
IRollEventRepository.cs
IExportRecordRepository.cs
IFileReader.cs
IFileFingerprintService.cs
IUnitOfWork.cs
IClock.cs
```

Uma interface deve existir quando houver necessidade de:

- isolamento;
- substituição;
- teste;
- implementação externa;
- inversão de dependência.

Não criar interfaces apenas por padrão automático.

---

## 6.4 `Common`

Contém estruturas compartilhadas pela aplicação.

Exemplos:

```text
OperationResult.cs
PagedResult.cs
ValidationError.cs
ApplicationException.cs
```

Evite transformar `Common` em um depósito genérico.

Cada arquivo deve possuir uso claro em mais de um módulo.

---

## 6.5 `Imports`

Contém casos de uso de importação.

Estrutura possível:

```text
Imports/
├── ImportFiles/
│   ├── ImportFilesCommand.cs
│   ├── ImportFilesResult.cs
│   └── ImportFilesService.cs
│
├── ImportFolder/
│   ├── ImportFolderCommand.cs
│   ├── ImportFolderResult.cs
│   └── ImportFolderService.cs
│
└── Parsing/
    └── ParseImportedLogService.cs
```

Pode ser adotada organização por funcionalidade ou por tipo.

A escolha deve permanecer consistente.

---

## 6.6 `Operations`

Contém casos de uso da tela Operação.

Exemplos:

```text
GetAvailablePrintItemsService.cs
BuildRollDraftService.cs
CalculateRollSummaryService.cs
GroupSelectedItemsService.cs
```

---

## 6.7 `Rolls`

Contém casos de uso relacionados ao rolo.

Exemplos:

```text
CloseRollService.cs
SearchRollsService.cs
GetRollDetailsService.cs
GetRollEventsService.cs
CopyRollCodeService.cs
```

A cópia para clipboard pode permanecer no Desktop, mas a preparação do valor pode ficar na aplicação quando necessário.

---

## 6.8 `Exports`

Contém orquestração das exportações.

Exemplos:

```text
ExportRollService.cs
ReexportRollService.cs
ExportRollCommand.cs
ExportRollResult.cs
```

A camada de aplicação coordena a exportação.

A geração concreta dos arquivos pertence ao Reporting.

---

## 6.9 `Settings`

Contém casos de uso das configurações.

Exemplos:

```text
LoadSettingsService.cs
SaveSettingsService.cs
ValidateExportFolderService.cs
```

---

# 7. `Nexor.Infrastructure`

## 7.1 Objetivo

Implementar as dependências concretas da aplicação.

Contém:

- SQLite;
- repositórios;
- migrations;
- parsing;
- sistema de arquivos;
- hashing;
- logging;
- configurações;
- caminhos locais.

---

## 7.2 Estrutura sugerida

```text
Nexor.Infrastructure/
├── Database/
├── Migrations/
├── Repositories/
├── Parsing/
├── FileSystem/
├── Fingerprints/
├── Logging/
├── Settings/
├── DependencyInjection/
└── Nexor.Infrastructure.csproj
```

---

## 7.3 `Database`

Contém a configuração principal de acesso ao SQLite.

Exemplos:

```text
NexorDatabase.cs
DatabaseConnectionFactory.cs
DatabaseInitializer.cs
SchemaVersionRepository.cs
```

Também pode conter:

```text
schema.sql
```

quando esse for o padrão real adotado.

---

## 7.4 `Migrations`

Contém as mudanças versionadas do banco.

Exemplo:

```text
Migrations/
├── Migration001InitialSchema.cs
├── Migration002AddExportRecords.cs
└── Migration003AddRollEvents.cs
```

Cada migration deve:

- possuir número;
- ser executada uma única vez;
- preservar dados;
- possuir teste;
- atualizar a versão do schema.

---

## 7.5 `Repositories`

Contém implementações concretas dos contratos de persistência.

Exemplos:

```text
ImportedLogRepository.cs
PrintItemRepository.cs
RollRepository.cs
RollEventRepository.cs
ExportRecordRepository.cs
SettingsRepository.cs
```

Repositórios devem:

- usar parâmetros;
- evitar SQL concatenado;
- mapear dados;
- não conter regras de interface;
- não gerar relatórios.

---

## 7.6 `Parsing`

Contém o parser concreto dos logs.

Exemplos:

```text
PxPrintLogParser.cs
PrintLogParseResult.cs
PrintLogSectionReader.cs
```

O parser deve:

- ler o formato real;
- preservar falhas estruturadas;
- aceitar culturas definidas;
- não depender da UI;
- possuir testes.

---

## 7.7 `FileSystem`

Contém acesso a arquivos e diretórios.

Exemplos:

```text
LocalFileReader.cs
FolderScanner.cs
LocalPathService.cs
ExplorerService.cs
TemporaryFileService.cs
```

---

## 7.8 `Fingerprints`

Contém a implementação de SHA-256.

Exemplo:

```text
Sha256FileFingerprintService.cs
```

---

## 7.9 `Logging`

Contém configuração de logs.

Exemplos:

```text
LoggingConfiguration.cs
LocalLogPathProvider.cs
```

---

## 7.10 `Settings`

Contém persistência concreta das preferências.

Exemplos:

```text
JsonSettingsStore.cs
LocalSettingsPathProvider.cs
```

---

## 7.11 `DependencyInjection`

Contém o registro das implementações.

Exemplo:

```text
InfrastructureServiceCollectionExtensions.cs
```

Esse arquivo pode registrar:

- banco;
- repositórios;
- parsers;
- arquivos;
- logging;
- configurações.

---

# 8. `Nexor.Reporting`

## 8.1 Objetivo

Gerar os relatórios e imagens do Nexor.

Deve permanecer separado da interface e do banco concreto.

---

## 8.2 Estrutura sugerida

```text
Nexor.Reporting/
├── Models/
├── Pdf/
├── Mirror/
├── Templates/
├── Services/
└── Nexor.Reporting.csproj
```

---

## 8.3 `Models`

Contém modelos específicos para relatórios.

Exemplos:

```text
RollReportModel.cs
RollReportItemModel.cs
RollReportBlockModel.cs
```

Esses modelos não devem ser entidades persistidas.

---

## 8.4 `Pdf`

Contém a geração de PDF.

Exemplos:

```text
FullRollPdfGenerator.cs
SummaryRollPdfGenerator.cs
PdfLayoutHelper.cs
```

---

## 8.5 `Mirror`

Contém geração do JPG espelhado.

Exemplos:

```text
MirrorImageGenerator.cs
MirrorImageOptions.cs
ImageSizeCalculator.cs
```

---

## 8.6 `Templates`

Contém recursos ou definições de layout.

Exemplos:

```text
FullRollTemplate.cs
SummaryRollTemplate.cs
```

A estrutura dependerá da biblioteca adotada.

---

## 8.7 `Services`

Contém implementações que atendem contratos usados pela aplicação.

Exemplos:

```text
RollReportService.cs
MirrorExportService.cs
```

---

# 9. `Nexor.Desktop`

## 9.1 Objetivo

Representar a aplicação WPF e a interação com o usuário.

---

## 9.2 Estrutura sugerida

```text
Nexor.Desktop/
├── App.xaml
├── App.xaml.cs
├── Assets/
├── Controls/
├── Converters/
├── Dialogs/
├── Navigation/
├── Resources/
├── Services/
├── Themes/
├── ViewModels/
├── Views/
└── Nexor.Desktop.csproj
```

---

## 9.3 `Assets`

Contém recursos visuais.

Exemplos:

```text
Assets/
├── Icons/
├── Images/
└── Logo/
```

Não colocar screenshots da documentação nessa pasta.

Screenshots pertencem a:

```text
docs/screenshots/
```

---

## 9.4 `Controls`

Contém componentes reutilizáveis.

Exemplos:

```text
StatusBadge.xaml
MetricCard.xaml
SearchBox.xaml
EmptyState.xaml
LoadingOverlay.xaml
```

Um controle deve ser criado quando houver reutilização ou comportamento visual próprio.

---

## 9.5 `Converters`

Contém converters exclusivamente visuais.

Exemplos:

```text
BooleanToVisibilityConverter.cs
RollStatusToBrushConverter.cs
NullToVisibilityConverter.cs
```

Converters não devem executar regras de negócio.

---

## 9.6 `Dialogs`

Contém diálogos e seus ViewModels.

Exemplos:

```text
Dialogs/
├── RollReviewDialog.xaml
├── RollReviewDialog.xaml.cs
├── RollReviewDialogViewModel.cs
│
├── ImportResultDialog.xaml
└── ImportResultDialogViewModel.cs
```

Quando possível, prefira serviço de diálogo em vez de criar diretamente a janela em qualquer ViewModel.

---

## 9.7 `Navigation`

Contém a navegação da aplicação.

Exemplos:

```text
INavigationService.cs
NavigationService.cs
NavigationItem.cs
NavigationTarget.cs
```

A `MainWindow` não deve concentrar toda a troca de telas manualmente.

---

## 9.8 `Resources`

Contém recursos globais.

Exemplos:

```text
Resources/
├── Icons.xaml
├── Typography.xaml
├── Controls.xaml
└── Strings.xaml
```

---

## 9.9 `Services`

Contém serviços específicos da interface.

Exemplos:

```text
DialogService.cs
ClipboardService.cs
FilePickerService.cs
FolderPickerService.cs
WindowService.cs
```

Esses serviços podem acessar APIs do Windows ou WPF.

---

## 9.10 `Themes`

Contém os temas.

```text
Themes/
├── NexorDarkTheme.xaml
├── NexorLightTheme.xaml
└── SisBoltTheme.xaml
```

Também pode conter estilos compartilhados.

Não duplicar o mesmo estilo em cada tema quando apenas os valores de cor mudarem.

---

## 9.11 `ViewModels`

Organizar por tela ou funcionalidade.

```text
ViewModels/
├── MainViewModel.cs
├── Home/
│   └── HomeViewModel.cs
├── Operation/
│   ├── OperationViewModel.cs
│   ├── PrintItemViewModel.cs
│   └── RollSummaryViewModel.cs
├── Rolls/
│   ├── RollsViewModel.cs
│   └── RollDetailsViewModel.cs
├── Settings/
│   └── SettingsViewModel.cs
└── About/
    └── AboutViewModel.cs
```

ViewModels não devem acessar diretamente:

- SQLite;
- arquivos;
- relatórios;
- controles WPF por nome.

---

## 9.12 `Views`

Organizar conforme os ViewModels.

```text
Views/
├── MainWindow.xaml
├── Home/
│   └── HomeView.xaml
├── Operation/
│   └── OperationView.xaml
├── Rolls/
│   └── RollsView.xaml
├── Settings/
│   └── SettingsView.xaml
└── About/
    └── AboutView.xaml
```

A relação entre View e ViewModel deve ser previsível.

---

# 10. Diretório `tests`

## 10.1 Estrutura

```text
tests/
├── Nexor.Domain.Tests/
├── Nexor.Application.Tests/
└── Nexor.Infrastructure.Tests/
```

Pode existir futuramente:

```text
Nexor.Reporting.Tests/
Nexor.Integration.Tests/
Nexor.Desktop.Tests/
```

somente quando houver necessidade real.

---

## 10.2 `Nexor.Domain.Tests`

Deve testar:

- metragem;
- estados;
- invariantes;
- códigos;
- agrupamento;
- ordenação;
- fechamento.

A estrutura pode espelhar o domínio:

```text
Nexor.Domain.Tests/
├── Entities/
├── Rules/
└── ValueObjects/
```

---

## 10.3 `Nexor.Application.Tests`

Deve testar:

- importação;
- montagem;
- fechamento;
- consulta;
- exportação;
- reexportação;
- resultados.

Usar mocks ou fakes somente quando ajudarem a isolar o caso de uso.

---

## 10.4 `Nexor.Infrastructure.Tests`

Deve testar:

- parser;
- banco;
- migrations;
- repositórios;
- arquivos;
- fingerprint;
- configurações.

Testes devem utilizar caminhos e bancos temporários.

---

# 11. Diretório `docs`

## 11.1 Objetivo

Concentrar a documentação técnica e funcional.

Estrutura atual esperada:

```text
docs/
├── screenshots/
├── architecture.md
├── Build_Guide.md
├── Coding_Standards.md
├── Database_Guide.md
├── Data_Model.md
├── Development_Guide.md
├── Functional_Spec_Operational_Core.md
├── installation.md
├── MVVM_Guide.md
├── Project_Structure.md
├── Release_Process.md
├── roadmap.md
├── UI_UX_Specification.md
└── Wireframe_Specification.md
```

Não criar documentos duplicados com nomes diferentes para o mesmo assunto.

---

## 11.2 `screenshots`

Deve conter apenas screenshots reais da aplicação.

```text
docs/screenshots/
├── 01-home.png
├── 02-operacao.png
├── 03-rolos.png
├── 04-configuracoes.png
└── 05-sobre.png
```

Não colocar:

- imagens do ListForge;
- mockups antigos;
- prints do legado;
- arquivos sem uso;
- imagens com dados confidenciais.

---

# 12. Diretório `installer`

Contém os arquivos do instalador.

```text
installer/
└── Nexor.iss
```

Pode conter:

```text
installer/
├── Nexor.iss
├── Assets/
└── Scripts/
```

somente se necessário.

O instalador não deve incluir:

- banco de desenvolvimento;
- código-fonte;
- legado;
- testes;
- logs;
- dados reais.

---

# 13. Diretório `legacy`

## 13.1 Objetivo

Preservar a implementação anterior.

Estrutura esperada:

```text
legacy/
└── Nexor-Python-Legacy/
```

O legado serve para:

- consulta;
- histórico;
- comparação;
- recuperação de regras.

Não deve:

- fazer parte da solução;
- ser executado no runtime atual;
- ser dependência do C#;
- receber novas funcionalidades;
- definir a arquitetura oficial.

---

# 14. Diretório `dist`

## 14.1 Objetivo

Armazenar os artefatos gerados por versão.

```text
dist/
└── X.Y.Z/
    ├── onefile/
    ├── trial/
    ├── installable/
    └── installer/
```

## 14.2 Regras

- não apagar versões anteriores;
- não sobrescrever builds antigos;
- não usar como fonte oficial;
- não editar código dentro de `dist`;
- não misturar versão oficial e Trial;
- não incluir arquivos de desenvolvimento.

A política de versionamento de `dist` no Git deve ser definida separadamente.

---

# 15. Diretório `.github`

Contém automações do GitHub.

```text
.github/
└── workflows/
    └── ci.yml
```

O pipeline pode executar:

- restore;
- build;
- testes;
- validação de formatação;
- geração futura de artefatos.

Segredos devem permanecer em GitHub Secrets.

---

# 16. Arquivos da raiz

## `README.md`

Porta de entrada do projeto.

Deve conter:

- visão geral;
- estado atual;
- execução;
- arquitetura resumida;
- documentação;
- licença.

---

## `CHANGELOG.md`

Histórico real das versões.

---

## `LICENSE.md`

Termos de licença do Nexor.

---

## `Directory.Build.props`

Configurações compartilhadas entre projetos.

Pode conter:

```xml
<Nullable>enable</Nullable>
<ImplicitUsings>enable</ImplicitUsings>
<EnableNETAnalyzers>true</EnableNETAnalyzers>
```

Evite duplicar essas configurações em todos os `.csproj` quando puderem ser centralizadas.

---

## `.gitignore`

Deve ignorar:

- `bin`;
- `obj`;
- bancos locais;
- logs;
- configurações pessoais;
- caches;
- temporários;
- segredos.

Não ignore documentação ou scripts necessários ao projeto.

---

# 17. Dependências entre projetos

Direção esperada:

```text
Nexor.Desktop
      ↓
Nexor.Application
      ↓
Nexor.Domain
```

Implementações externas:

```text
Nexor.Infrastructure
      ↓
Nexor.Application / Nexor.Domain
```

Relatórios:

```text
Nexor.Reporting
      ↓
contratos ou modelos internos
```

## Regras

- Domain não depende de nenhum outro projeto.
- Application não depende de Desktop.
- Infrastructure não depende de Desktop.
- Reporting não depende de WPF.
- Desktop não contém SQL.
- Domain não contém caminhos de arquivo.
- Repositórios não conhecem ViewModels.

---

# 18. Onde colocar cada tipo de código

| Código | Local |
|---|---|
| Entidade | `Nexor.Domain/Entities` |
| Enum de estado | `Nexor.Domain/Enums` |
| Regra de metragem | `Nexor.Domain/Rules` |
| Caso de uso | `Nexor.Application` |
| Contrato de repositório | `Nexor.Application/Abstractions` |
| SQL | `Nexor.Infrastructure/Repositories` |
| Migration | `Nexor.Infrastructure/Migrations` |
| Parser | `Nexor.Infrastructure/Parsing` |
| Hash SHA-256 | `Nexor.Infrastructure/Fingerprints` |
| PDF | `Nexor.Reporting/Pdf` |
| JPG espelhado | `Nexor.Reporting/Mirror` |
| View | `Nexor.Desktop/Views` |
| ViewModel | `Nexor.Desktop/ViewModels` |
| Converter | `Nexor.Desktop/Converters` |
| Tema | `Nexor.Desktop/Themes` |
| Dialog | `Nexor.Desktop/Dialogs` |
| Teste de domínio | `Nexor.Domain.Tests` |
| Teste de parser | `Nexor.Infrastructure.Tests` |

---

# 19. Onde não colocar

## Não colocar em ViewModel

- SQL;
- leitura direta de arquivo;
- SHA-256;
- geração de PDF;
- regra de metragem;
- transação.

## Não colocar em entidade

- `MessageBox`;
- acesso ao banco;
- seleção de pasta;
- configuração visual;
- logs de interface.

## Não colocar em repositório

- agrupamento visual;
- validação de botão;
- geração de código de rolo sem relação com persistência;
- mensagens para o usuário.

## Não colocar em code-behind

- fechamento;
- duplicidade;
- cálculo;
- busca histórica;
- persistência.

---

# 20. Organização por camada versus funcionalidade

Dentro de cada projeto, prefira organização que facilite localizar o comportamento.

Para projetos pequenos, separar por tipo pode funcionar:

```text
Services/
Models/
Interfaces/
```

À medida que a aplicação crescer, pode ser melhor agrupar por funcionalidade:

```text
Imports/
Rolls/
Exports/
Settings/
```

Não misture os dois padrões sem critério.

A estrutura deve evoluir quando o volume justificar, não antecipadamente.

---

# 21. Arquivos auxiliares

Arquivos temporários ou scripts de investigação devem ficar fora da estrutura oficial ou ser removidos após o uso.

Não criar na raiz:

```text
test2.cs
new_file.cs
temp.txt
backup-old.cs
final-final.cs
```

Use Git para histórico.

---

# 22. Arquivos gerados

Não versionar normalmente:

```text
bin/
obj/
*.user
*.suo
*.db
*.log
```

Artefatos gerados devem ficar em:

```text
dist/
```

Arquivos temporários de testes devem usar a pasta temporária do sistema.

---

# 23. Nomes de pastas e arquivos

Usar nomes em inglês no código.

Exemplos:

```text
Repositories
ViewModels
Rolls
Imports
Settings
```

Documentos podem manter os nomes já existentes para não quebrar links.

Evite criar arquivos diferentes apenas por variação de capitalização:

```text
architecture.md
Architecture.md
ARCHITECTURE.md
```

Escolha um nome e atualize os links.

---

# 24. Criação de novo módulo

Antes de criar um módulo:

1. confirme que existe caso de uso real;
2. confirme que não cabe em módulo existente;
3. defina a camada;
4. defina contratos;
5. identifique persistência;
6. planeje testes;
7. atualize documentação.

Não criar imediatamente:

- Planning;
- Inventory;
- Analytics;
- Sync;

sem demanda e escopo aprovados.

---

# 25. Criação de novo projeto `.csproj`

Um novo projeto só deve ser criado quando houver necessidade clara de:

- isolamento;
- dependência diferente;
- distribuição independente;
- testes específicos;
- fronteira arquitetural real.

Não criar um projeto por tela ou por entidade.

---

# 26. Registro de dependências

As implementações devem ser registradas em um ponto central.

Exemplo:

```csharp
services.AddNexorApplication();
services.AddNexorInfrastructure();
services.AddNexorReporting();
```

A composição deve ocorrer no projeto Desktop.

A camada Domain não deve conhecer injeção de dependência.

---

# 27. Regras para expansão futura

## Cadastros

Quando implementados, podem entrar como funcionalidade em:

```text
Nexor.Application/MasterData
Nexor.Desktop/Views/MasterData
Nexor.Desktop/ViewModels/MasterData
```

## Planejamento

```text
Nexor.Application/Planning
Nexor.Domain/Planning
Nexor.Desktop/Views/Planning
```

Somente criar novos projetos se o volume e o isolamento justificarem.

## Estoque

Seguir o mesmo princípio.

## Analytics

Pode exigir projeto próprio futuramente, mas não nesta etapa.

---

# 28. Estrutura dos namespaces

Os namespaces devem refletir o projeto.

Exemplos:

```csharp
namespace Nexor.Domain.Entities;
namespace Nexor.Application.Rolls;
namespace Nexor.Infrastructure.Parsing;
namespace Nexor.Desktop.ViewModels.Operation;
```

Não usar namespaces herdados do ListForge ou Jocasta.

---

# 29. Referências ao legado

Comentários e documentos podem mencionar:

- PXPrintLogs;
- PXSearchOrders;
- ListForge.

O código novo não deve usar namespaces como:

```text
Jocasta
PXPrintLogs
ListForge
```

salvo em ferramentas explícitas de migração ou testes de compatibilidade devidamente isolados.

---

# 30. Testes próximos ao comportamento

A estrutura dos testes deve facilitar encontrar a cobertura correspondente.

Exemplo:

```text
Nexor.Domain/
└── Rules/
    └── ConsecutiveFabricGroupingRule.cs

Nexor.Domain.Tests/
└── Rules/
    └── ConsecutiveFabricGroupingRuleTests.cs
```

---

# 31. Documentação próxima ao projeto

Documentação geral fica em:

```text
docs/
```

Documentação específica de código pode usar:

- XML Documentation;
- comentários;
- README local somente quando realmente necessário.

Evite vários arquivos README espalhados sem finalidade.

---

# 32. Critérios para mover arquivos

Um arquivo deve ser movido quando:

- está na camada errada;
- cria dependência indevida;
- não corresponde à responsabilidade da pasta;
- dificulta a localização;
- pertence ao legado.

Ao mover:

- atualizar namespace;
- atualizar referências;
- atualizar testes;
- atualizar documentação;
- validar build;
- preservar histórico pelo Git.

---

# 33. Critérios de qualidade da estrutura

A estrutura será considerada saudável quando:

- cada classe possui local previsível;
- regras não estão na UI;
- SQL está isolado;
- parsing está isolado;
- relatórios estão isolados;
- os testes refletem os projetos;
- não há pastas genéricas cheias de arquivos sem relação;
- não há dependências circulares;
- novos desenvolvedores encontram rapidamente o código.

---

# 34. Sinais de desorganização

Devem ser corrigidos:

- `Utils` com dezenas de classes não relacionadas;
- `Helpers` usados como depósito;
- serviços com muitas responsabilidades;
- ViewModels gigantes;
- `MainWindow.xaml.cs` controlando todo o sistema;
- entidades com setters públicos para tudo;
- SQL dentro da aplicação;
- caminhos locais espalhados;
- duplicação de modelos;
- documentação contraditória;
- arquivos temporários versionados.

---

# 35. Checklist para novo arquivo

Antes de criar:

- [ ] O arquivo é necessário.
- [ ] Não existe equivalente.
- [ ] A camada foi identificada.
- [ ] A pasta representa sua responsabilidade.
- [ ] O namespace está correto.
- [ ] O nome é específico.
- [ ] Há teste quando aplicável.
- [ ] A documentação será atualizada se necessário.

---

# 36. Checklist para novo projeto

- [ ] Existe fronteira arquitetural real.
- [ ] A dependência é diferente.
- [ ] O projeto não cria acoplamento circular.
- [ ] A distribuição separada é necessária.
- [ ] A manutenção ficará mais simples.
- [ ] A solução foi atualizada.
- [ ] A documentação foi atualizada.
- [ ] O CI foi revisado.

---

# 37. Estado atual e evolução

A estrutura descrita representa a direção oficial do Nexor.

Durante a reconstrução, algumas classes podem ainda não estar exatamente nos locais ideais.

A evolução deve ocorrer de forma incremental:

1. preservar funcionamento;
2. identificar responsabilidade;
3. mover com testes;
4. validar referências;
5. atualizar documentação.

Não realizar reorganizações extensas sem necessidade funcional ou arquitetural clara.

---

# 38. Regra final

A organização do Nexor deve permitir responder rapidamente:

```text
Onde está a regra?
Onde está o caso de uso?
Onde está o acesso ao banco?
Onde está o parser?
Onde está a tela?
Onde está o relatório?
Onde está o teste?
```

A resposta deve ser previsível pela estrutura do projeto, não depender de conhecer todo o histórico do código.