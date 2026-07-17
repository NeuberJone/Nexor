# Nexor — Padrões de Código

## 1. Objetivo

Este documento define os padrões oficiais de desenvolvimento do **Nexor**.

O objetivo é manter o código:

- legível;
- previsível;
- consistente;
- testável;
- fácil de revisar;
- seguro para manutenção;
- alinhado à arquitetura do projeto.

O Nexor utiliza:

- C#;
- .NET 8;
- WPF;
- SQLite;
- MVVM;
- nullable reference types;
- analyzers do .NET.

Estes padrões se aplicam a todo código novo e às alterações realizadas na implementação oficial em C#.

---

## 2. Princípios gerais

### 2.1 Clareza antes de concisão

Prefira código fácil de entender a construções excessivamente compactas.

Evite:

```csharp
var result = items.Where(x => x.IsValid).Select(x => new ItemDto(x.Id, x.Name)).ToList();
```

Quando a expressão possuir várias responsabilidades, prefira separar:

```csharp
var validItems = items
    .Where(item => item.IsValid)
    .ToList();

var result = validItems
    .Select(item => new ItemDto(item.Id, item.Name))
    .ToList();
```

---

### 2.2 Uma responsabilidade por componente

Cada classe, método e serviço deve possuir uma responsabilidade clara.

Evite classes que:

- importem arquivos;
- façam parsing;
- persistam no banco;
- atualizem a interface;
- gerem PDF;
- controlem navegação;

ao mesmo tempo.

---

### 2.3 Regras de negócio fora da interface

Views e code-behind não devem conter:

- cálculo de metragem;
- ordenação operacional;
- agrupamento por tecido;
- validação de fechamento;
- SQL;
- prevenção de duplicidade;
- regras de exportação.

Essas responsabilidades pertencem ao domínio, aplicação ou infraestrutura.

---

### 2.4 Código explícito

Não esconda comportamento importante em:

- propriedades com efeitos colaterais;
- conversores visuais;
- eventos genéricos;
- extensões pouco intuitivas;
- construtores excessivamente complexos.

Ações importantes devem ser representadas por métodos ou casos de uso claros.

---

### 2.5 Evitar abstração prematura

Não crie:

- interfaces sem necessidade;
- fábricas para uma única implementação;
- wrappers sem valor;
- hierarquias profundas;
- padrões complexos apenas por antecipação.

Uma abstração deve resolver um problema real de:

- substituição;
- teste;
- isolamento;
- dependência externa;
- reutilização.

---

## 3. Idioma

### 3.1 Código

O código deve utilizar nomes em inglês.

Exemplos:

```csharp
ImportedLog
PrintItem
Roll
RollItem
RollEvent
ImportLogService
RollClosureService
```

---

### 3.2 Interface

Textos visíveis ao usuário devem permanecer em português brasileiro.

Exemplos:

```text
Importar arquivos
Fechar rolo
Nenhum registro encontrado
Configurações salvas
```

---

### 3.3 Documentação

A documentação principal do Nexor deve ser escrita em português, salvo quando houver decisão explícita em contrário.

---

### 3.4 Termo Job

O termo `Job` pode ser utilizado internamente somente quando tecnicamente necessário.

Evite o termo em textos visíveis ao usuário.

Use:

- item;
- registro;
- impressão;
- arquivo;
- pedido;
- processamento.

Quando possível, prefira também nomes internos mais específicos, como:

```csharp
PrintItem
ProductionRecord
ImportedLog
```

---

## 4. Convenções de nomenclatura

## 4.1 Namespaces

Usar PascalCase.

Exemplos:

```csharp
Nexor.Domain.Entities
Nexor.Application.Operations
Nexor.Infrastructure.Persistence
Nexor.Desktop.ViewModels
```

O namespace deve corresponder à estrutura lógica do projeto.

---

## 4.2 Classes

Usar PascalCase.

```csharp
public sealed class ImportedLog
{
}
```

---

## 4.3 Interfaces

Usar prefixo `I`.

```csharp
public interface IRollRepository
{
}
```

---

## 4.4 Métodos

Usar PascalCase e verbo que represente a ação.

```csharp
ImportFilesAsync()
CloseRollAsync()
FindRollsAsync()
CalculatePrintedLength()
```

Evite nomes vagos:

```csharp
DoWork()
Process()
Handle()
ExecuteStuff()
```

Quando o contexto não deixar a ação clara.

---

## 4.5 Propriedades

Usar PascalCase.

```csharp
public string DocumentName { get; init; }
public decimal PrintedLengthMeters { get; private set; }
```

---

## 4.6 Campos privados

Usar `_camelCase`.

```csharp
private readonly IRollRepository _rollRepository;
private bool _isLoading;
```

---

## 4.7 Variáveis locais

Usar camelCase.

```csharp
var importedFiles = new List<string>();
var totalPrintedLength = 0m;
```

---

## 4.8 Constantes

Usar PascalCase.

```csharp
private const int DefaultSearchLimit = 300;
private const decimal MillimetersPerMeter = 1000m;
```

---

## 4.9 Enums

Usar PascalCase no tipo e nos valores.

```csharp
public enum RollStatus
{
    Draft,
    Closed,
    Exported,
    Reviewed,
    Reopened
}
```

---

## 4.10 Eventos

Usar nomes que representem acontecimentos.

```csharp
public event EventHandler? ThemeChanged;
public event EventHandler<RollClosedEventArgs>? RollClosed;
```

---

## 5. Organização dos arquivos

### 5.1 Uma classe principal por arquivo

Preferir:

```text
Roll.cs
RollRepository.cs
RollClosureService.cs
```

Evitar múltiplas classes públicas não relacionadas no mesmo arquivo.

---

### 5.2 Nome do arquivo

O nome do arquivo deve corresponder ao tipo principal.

```text
RollClosureService.cs
```

contendo:

```csharp
public sealed class RollClosureService
```

---

### 5.3 Ordem interna recomendada

Dentro de uma classe:

1. constantes;
2. campos;
3. construtor;
4. propriedades;
5. eventos;
6. métodos públicos;
7. métodos internos;
8. métodos privados.

---

## 6. Formatação

O projeto deve utilizar `.editorconfig`.

Preferências:

- indentação com 4 espaços;
- chaves em nova linha;
- uma instrução por linha;
- linha em branco entre blocos lógicos;
- arquivos terminando com nova linha;
- remoção de espaços finais.

Exemplo:

```csharp
public async Task<Roll?> FindByCodeAsync(
    string code,
    CancellationToken cancellationToken)
{
    ArgumentException.ThrowIfNullOrWhiteSpace(code);

    return await _repository.FindByCodeAsync(
        code,
        cancellationToken);
}
```

---

## 7. Tipagem

## 7.1 Nullable reference types

Manter habilitado:

```xml
<Nullable>enable</Nullable>
```

Não utilizar `!` apenas para silenciar o compilador sem justificativa.

Evite:

```csharp
var roll = repository.Find(id)!;
```

Prefira tratar corretamente:

```csharp
var roll = await repository.FindByIdAsync(id, cancellationToken);

if (roll is null)
{
    return OperationResult.NotFound("Rolo não encontrado.");
}
```

---

## 7.2 `var`

Use `var` quando o tipo for evidente.

Adequado:

```csharp
var roll = new Roll(code, machineId);
var total = items.Sum(item => item.PrintedLengthMeters);
```

Prefira tipo explícito quando melhorar a leitura:

```csharp
IReadOnlyList<RollSummary> results =
    await repository.SearchAsync(filter, cancellationToken);
```

---

## 7.3 Tipos monetários e métricos

Utilizar `decimal` para:

- milímetros;
- metros;
- totais operacionais;
- larguras;
- valores que exijam precisão decimal.

Evitar `float` e `double` para metragem persistida.

```csharp
public decimal HeightMillimeters { get; }
public decimal PrintedLengthMeters { get; }
```

---

## 7.4 Datas

Preferir `DateTimeOffset`.

```csharp
public DateTimeOffset ImportedAt { get; init; }
public DateTimeOffset? ClosedAt { get; private set; }
```

Use `DateTime` apenas quando o fuso não for relevante e isso estiver explícito.

---

## 7.5 Coleções

Quando o consumidor não deve alterar a coleção, exponha:

```csharp
IReadOnlyList<RollItem>
IReadOnlyCollection<ImportedLog>
```

Evite expor `List<T>` mutável diretamente em entidades.

---

## 8. Construtores e inicialização

Construtores devem validar invariantes essenciais.

```csharp
public Roll(string code, string machineCode)
{
    ArgumentException.ThrowIfNullOrWhiteSpace(code);
    ArgumentException.ThrowIfNullOrWhiteSpace(machineCode);

    Code = code;
    MachineCode = machineCode;
    Status = RollStatus.Draft;
    OpenedAt = DateTimeOffset.Now;
}
```

Evite construtores que:

- acessem banco;
- leiam arquivos;
- executem operações assíncronas;
- iniciem navegação;
- mostrem diálogos.

---

## 9. Entidades de domínio

Entidades devem proteger seu próprio estado.

Evite:

```csharp
public RollStatus Status { get; set; }
```

Prefira:

```csharp
public RollStatus Status { get; private set; }

public void Close(DateTimeOffset closedAt)
{
    if (_items.Count == 0)
    {
        throw new DomainException(
            "Um rolo não pode ser fechado sem itens.");
    }

    Status = RollStatus.Closed;
    ClosedAt = closedAt;
}
```

Não permita que qualquer camada altere livremente propriedades críticas.

---

## 10. Value Objects

Use value objects quando um conceito possuir:

- validação própria;
- comportamento;
- regras;
- identidade por valor.

Possíveis exemplos:

```csharp
RollCode
FileFingerprint
PrintedLength
MachineCode
```

Não transforme todo campo simples em value object sem benefício real.

---

## 11. Serviços de aplicação

Casos de uso devem possuir nomes específicos.

Exemplo:

```csharp
public sealed class ImportLogsService
{
    public async Task<ImportLogsResult> ImportAsync(
        IReadOnlyCollection<string> filePaths,
        CancellationToken cancellationToken)
    {
        // Orquestração.
    }
}
```

Um serviço de aplicação pode:

- validar entrada;
- coordenar repositórios;
- chamar domínio;
- iniciar transação;
- produzir resultado;
- registrar eventos.

Ele não deve:

- manipular controles WPF;
- exibir `MessageBox`;
- executar SQL diretamente;
- depender de ViewModel.

---

## 12. Interfaces e repositórios

Interfaces devem representar contratos úteis.

```csharp
public interface IRollRepository
{
    Task<Roll?> FindByIdAsync(
        long id,
        CancellationToken cancellationToken);

    Task AddAsync(
        Roll roll,
        CancellationToken cancellationToken);
}
```

Evite interfaces genéricas excessivamente amplas como:

```csharp
IRepository<T>
```

quando entidades possuem necessidades distintas.

---

## 13. Métodos assíncronos

Métodos assíncronos devem terminar com `Async`.

```csharp
ImportAsync()
SaveAsync()
SearchAsync()
GeneratePdfAsync()
```

Não use `async void`, exceto em event handlers de UI.

Prefira:

```csharp
public async Task LoadAsync()
{
}
```

Em comandos MVVM, use infraestrutura própria para comandos assíncronos.

---

## 14. CancellationToken

Operações potencialmente demoradas devem aceitar `CancellationToken`.

Exemplos:

- importação de pasta;
- parsing em lote;
- consulta extensa;
- geração de relatórios;
- migração;
- leitura de arquivos.

```csharp
public Task<ImportResult> ImportFolderAsync(
    string folderPath,
    CancellationToken cancellationToken)
```

Propague o token às operações internas.

---

## 15. Exceções

## 15.1 Exceções de domínio

Use exceções específicas para violação de invariantes.

```csharp
public sealed class DomainException : Exception
{
    public DomainException(string message)
        : base(message)
    {
    }
}
```

---

## 15.2 Não usar exceções para fluxo comum

Duplicidade esperada não precisa obrigatoriamente ser exceção.

Prefira resultado estruturado:

```csharp
return ImportFileResult.Duplicate(existingLogId);
```

---

## 15.3 Não ocultar exceções

Evite:

```csharp
try
{
    await SaveAsync();
}
catch
{
}
```

No mínimo:

- registre;
- converta para resultado;
- preserve contexto;
- relance quando necessário.

---

## 15.4 Mensagens técnicas e mensagens ao usuário

Exceções técnicas devem ir para logs.

A interface deve apresentar mensagem amigável.

```csharp
_logger.LogError(
    exception,
    "Failed to persist roll {RollCode}.",
    roll.Code);
```

Texto visível:

```text
Não foi possível fechar o rolo.
Consulte os logs para obter mais detalhes.
```

---

## 16. Resultados de operação

Para fluxos previsíveis, use resultados estruturados.

Exemplo:

```csharp
public sealed record OperationResult(
    bool IsSuccess,
    string? UserMessage,
    string? ErrorCode);
```

Ou tipos específicos:

```csharp
ImportLogsResult
CloseRollResult
ExportRollResult
```

O resultado deve permitir distinguir:

- sucesso;
- validação;
- duplicidade;
- não encontrado;
- falha técnica;
- cancelamento.

---

## 17. Logging

Utilize logging estruturado.

Prefira:

```csharp
_logger.LogInformation(
    "Imported {ImportedCount} files and skipped {DuplicateCount} duplicates.",
    result.ImportedCount,
    result.DuplicateCount);
```

Evite:

```csharp
_logger.LogInformation(
    $"Imported {result.ImportedCount} files.");
```

O logging estruturado preserva propriedades pesquisáveis.

---

## 18. Dados sensíveis

Não registrar:

- conteúdo completo de produção sem necessidade;
- nomes de clientes em excesso;
- tokens;
- chaves;
- senhas;
- dados da licença;
- caminhos sensíveis desnecessários.

Quando o caminho for necessário para diagnóstico, avaliar o nível do log.

---

## 19. Parsing

Parsers devem ser determinísticos e independentes da UI.

Exemplo de contrato:

```csharp
public interface IPrintLogParser
{
    ParsePrintLogResult Parse(
        string content,
        string sourceName);
}
```

O parser deve retornar:

- sucesso;
- dados interpretados;
- campos ausentes;
- erros de validação;
- texto bruto quando necessário.

Evite lançar exceções para cada arquivo inválido de um lote.

---

## 20. Cultura e números

Não dependa implicitamente da cultura do sistema.

Ao interpretar arquivos externos, defina as culturas aceitas.

```csharp
decimal.TryParse(
    value,
    NumberStyles.Number,
    CultureInfo.InvariantCulture,
    out var result);
```

Quando necessário, tente formatos conhecidos explicitamente.

A apresentação ao usuário pode usar `pt-BR`.

---

## 21. Cálculo de metragem

A regra deve existir em um único ponto confiável.

```csharp
public static decimal CalculatePrintedLengthMeters(
    decimal heightMillimeters)
{
    if (heightMillimeters <= 0)
    {
        throw new DomainException(
            "A altura impressa deve ser maior que zero.");
    }

    return heightMillimeters / 1000m;
}
```

Não repetir a fórmula em:

- ViewModel;
- converter;
- relatório;
- repositório;
- code-behind.

---

## 22. Banco de dados

SQL deve ficar na infraestrutura.

Evite montar SQL por concatenação.

Inadequado:

```csharp
var sql = "SELECT * FROM Rolls WHERE Code = '" + code + "'";
```

Adequado:

```csharp
const string sql = """
    SELECT *
    FROM Rolls
    WHERE Code = @Code;
    """;
```

Sempre utilizar parâmetros.

---

## 23. Transações

Fluxos críticos devem ser transacionais.

Exemplos:

- fechamento do rolo;
- vínculo dos itens;
- registro do evento;
- atualização dos estados.

A transação deve ser coordenada pela camada de aplicação ou por uma abstração de unidade de trabalho.

---

## 24. Migrations

Cada migration deve:

- possuir número;
- possuir descrição;
- ser idempotente dentro do mecanismo de controle;
- possuir teste;
- preservar dados;
- registrar falhas.

Não alterar o schema silenciosamente no meio de um repositório.

---

## 25. WPF

## 25.1 Views

Views devem conter:

- layout;
- bindings;
- recursos visuais;
- comportamento estritamente visual.

---

## 25.2 ViewModels

ViewModels devem conter:

- estado da tela;
- comandos;
- propriedades observáveis;
- chamada de casos de uso;
- mensagens preparadas para exibição.

---

## 25.3 Code-behind

Code-behind é aceitável para:

- foco;
- atalhos;
- drag and drop;
- integração com janela;
- comportamento visual específico.

Não deve conter regras de negócio.

---

## 25.4 Bindings

Prefira bindings explícitos.

```xml
<TextBlock Text="{Binding TotalPrintedLengthDisplay}" />
```

Use `Mode=TwoWay` somente quando houver edição real.

---

## 25.5 Converters

Converters devem tratar apresentação.

Exemplos aceitáveis:

- bool para visibilidade;
- status para brush;
- valor nulo para estado visual.

Não devem:

- consultar banco;
- calcular metragem;
- alterar domínio;
- registrar eventos;
- executar navegação.

---

## 26. ViewModels observáveis

Propriedades devem notificar alteração apenas quando o valor mudar.

```csharp
private bool _isLoading;

public bool IsLoading
{
    get => _isLoading;
    set => SetProperty(ref _isLoading, value);
}
```

Evite disparar `PropertyChanged` desnecessariamente.

---

## 27. Comandos

Comandos devem representar ações claras.

```csharp
ImportFilesCommand
ImportFolderCommand
ReviewRollCommand
CloseRollCommand
ClearSelectionCommand
```

O estado de habilitação deve refletir as pré-condições.

Exemplo:

```csharp
ReviewRollCommand.CanExecute
```

deve ser falso quando não houver item selecionado.

---

## 28. Navegação

A navegação deve ser centralizada.

ViewModels não devem criar Views diretamente.

Contrato sugerido:

```csharp
public interface INavigationService
{
    void NavigateTo<TViewModel>()
        where TViewModel : class;
}
```

Evite múltiplos `Visibility` espalhados na janela principal.

---

## 29. Temas

Não usar cores fixas diretamente nas Views quando houver recurso semântico.

Evite:

```xml
<Border Background="#20242A" />
```

Prefira:

```xml
<Border Background="{DynamicResource SurfaceBrush}" />
```

Os recursos devem ser testados nos temas:

- Nexor Dark;
- Nexor Light;
- SISBolt.

---

## 30. Recursos visuais

Use `DynamicResource` para elementos que precisam responder à troca de tema.

Use `StaticResource` para recursos imutáveis durante a execução.

Não recrie componentes apenas para aplicar tema quando o recurso dinâmico resolver corretamente.

---

## 31. Textos da interface

Textos devem ser:

- diretos;
- curtos;
- operacionais;
- consistentes.

Adequado:

```text
Importar arquivos
Limpar seleção
Confirmar fechamento
Abrir pasta
```

Evite:

```text
Clique aqui para realizar a importação dos arquivos
```

---

## 32. Comentários

Comentários devem explicar o motivo, não repetir o código.

Inadequado:

```csharp
// Incrementa o contador.
count++;
```

Adequado:

```csharp
// O agrupamento é consecutivo; o mesmo tecido após outro bloco
// deve gerar uma nova sequência.
blockSequence++;
```

---

## 33. XML Documentation

Documentação XML é recomendada para:

- APIs públicas;
- interfaces;
- regras não óbvias;
- componentes reutilizáveis;
- contratos de infraestrutura.

```csharp
/// <summary>
/// Calculates printed length using only HeightMM.
/// VPositionMM is intentionally excluded.
/// </summary>
public decimal CalculatePrintedLength(decimal heightMillimeters)
```

Não é necessário documentar trivialidades.

---

## 34. Regiões

Evite `#region` como forma de esconder classes grandes.

Se uma classe precisa de muitas regiões, provavelmente deve ser dividida.

Use somente em casos pontuais e justificados.

---

## 35. Métodos

Métodos devem ser pequenos o suficiente para ter propósito claro.

Não existe limite rígido de linhas, mas métodos longos devem ser revisados.

Sinais de necessidade de divisão:

- muitos níveis de indentação;
- múltiplas responsabilidades;
- muitas variáveis temporárias;
- vários blocos `try/catch`;
- muitos comentários para explicar etapas.

---

## 36. Parâmetros

Evite métodos com muitos parâmetros.

Inadequado:

```csharp
CloseRoll(
    string code,
    long machineId,
    DateTimeOffset openedAt,
    DateTimeOffset closedAt,
    string notes,
    IReadOnlyList<long> itemIds,
    bool exportPdf,
    bool exportMirror);
```

Prefira um comando:

```csharp
public sealed record CloseRollCommand(
    string Code,
    long MachineId,
    string? Notes,
    IReadOnlyList<long> ItemIds);
```

---

## 37. Records e classes

Use `record` para:

- DTOs;
- comandos;
- resultados;
- filtros;
- valores imutáveis.

Use classes para:

- entidades;
- serviços;
- componentes com identidade e ciclo de vida;
- ViewModels.

---

## 38. DTOs

DTOs não devem conter lógica de negócio relevante.

Exemplo:

```csharp
public sealed record RollSummaryDto(
    long Id,
    string Code,
    string Machine,
    int TotalItems,
    decimal TotalPrintedLengthMeters,
    RollStatus Status);
```

Evite expor entidades diretamente à UI quando isso gerar acoplamento.

---

## 39. Testes

## 39.1 Nome dos testes

Padrão recomendado:

```text
MethodName_Scenario_ExpectedResult
```

Exemplo:

```csharp
CalculatePrintedLength_ValidHeight_ReturnsMeters()
CloseRoll_WithoutItems_ThrowsDomainException()
ImportFile_DuplicateHash_ReturnsDuplicateResult()
```

---

## 39.2 Estrutura Arrange, Act, Assert

```csharp
[Fact]
public void CalculatePrintedLength_ValidHeight_ReturnsMeters()
{
    // Arrange
    const decimal heightMillimeters = 6361m;

    // Act
    var result = PrintMetrics.CalculatePrintedLengthMeters(
        heightMillimeters);

    // Assert
    Assert.Equal(6.361m, result);
}
```

---

## 39.3 Testes determinísticos

Testes não devem depender de:

- data atual sem abstração;
- ordem aleatória;
- rede;
- pasta pessoal;
- banco real;
- estado de outro teste.

Use:

- relógio abstrato;
- diretório temporário;
- banco isolado;
- dados fixos.

---

## 39.4 Testes de banco

Cada teste deve usar banco próprio ou transação isolada.

Não utilizar o banco real em:

```text
%LOCALAPPDATA%\Nexor
```

---

## 40. Dependências

Antes de adicionar um pacote:

- verificar se o .NET já oferece a funcionalidade;
- avaliar manutenção;
- avaliar licença;
- avaliar tamanho;
- avaliar compatibilidade com one-file;
- avaliar impacto no instalador.

Toda dependência relevante deve ser documentada.

---

## 41. Segurança

Nunca adicionar ao repositório:

- tokens;
- chaves privadas;
- senhas;
- arquivos `.env` reais;
- dados de clientes;
- banco operacional;
- arquivos reais de produção;
- dados da Trial de usuários.

Use arquivos de exemplo quando necessário.

---

## 42. Configurações

Não usar caminhos absolutos de desenvolvimento no código.

Inadequado:

```csharp
const string DatabasePath =
    @"F:\Projetos\Nexor\data\nexor.db";
```

Adequado:

```csharp
var databasePath = Path.Combine(
    Environment.GetFolderPath(
        Environment.SpecialFolder.LocalApplicationData),
    "Nexor",
    "nexor.db");
```

---

## 43. Feature flags e Trial

Regras de Trial devem ficar isoladas.

Não espalhar:

```csharp
if (isTrial)
```

por todas as camadas.

Prefira serviço específico:

```csharp
public interface ILicenseService
{
    LicenseState GetCurrentState();
}
```

O domínio operacional não deve depender da Trial.

---

## 44. Tratamento global de erros

A aplicação deve possuir tratamento global para exceções não observadas.

O tratamento deve:

- registrar;
- evitar perda de detalhes;
- exibir mensagem apropriada;
- não esconder corrupção;
- não manter aplicação em estado inseguro.

---

## 45. Performance

Evite bloquear a thread da UI com:

- leitura de pasta;
- hashing de muitos arquivos;
- consultas extensas;
- exportação;
- parsing em lote.

Use tarefas assíncronas e indicadores de progresso.

Não use paralelismo sem medir o benefício.

---

## 46. Revisão de código

Antes de concluir uma alteração, verificar:

- responsabilidade correta;
- nomes claros;
- testes;
- mensagens;
- nullable;
- tratamento de erro;
- logging;
- impacto no banco;
- impacto na documentação;
- ausência de segredos;
- consistência visual.

---

## 47. Commits

Utilizar Conventional Commits.

Exemplos:

```text
feat: add folder log import
fix: prevent duplicate roll assignments
refactor: isolate roll closure transaction
docs: update operational flow
test: cover consecutive fabric grouping
chore(release): prepare version 0.3.0
```

---

## 48. Alterações de banco

Mudanças de schema devem incluir:

- migration;
- teste;
- atualização do `Data_Model.md`;
- atualização do `Database_Guide.md`;
- nota no changelog quando relevante;
- avaliação de backup.

---

## 49. Alterações de interface

Mudanças visuais relevantes devem incluir:

- teste nos três temas;
- teste com escala do Windows;
- atualização de wireframes quando estrutural;
- atualização de screenshots quando a versão for publicada;
- validação de contraste.

---

## 50. Checklist antes do commit

- [ ] Código formatado.
- [ ] Build executado.
- [ ] Testes relevantes aprovados.
- [ ] Nullable revisado.
- [ ] Analyzers revisados.
- [ ] Sem código comentado desnecessário.
- [ ] Sem arquivos temporários.
- [ ] Sem dados sensíveis.
- [ ] Sem caminhos locais fixos.
- [ ] Documentação atualizada quando necessária.
- [ ] Mensagem de commit preparada.

---

## 51. Exceções a este padrão

Uma regra pode ser descumprida quando houver justificativa técnica clara.

A exceção deve:

- resolver um problema real;
- ser localizada;
- não criar precedente silencioso;
- ser documentada em comentário ou decisão arquitetural quando relevante.

---

## 52. Regra final

O código do Nexor deve permitir que outro desenvolvedor compreenda:

```text
o que a classe representa;
qual caso de uso está sendo executado;
onde a regra de negócio está;
como o dado é persistido;
como o erro é tratado;
como o comportamento é testado.
```

A consistência do projeto depende menos de escrever código sofisticado e mais de manter responsabilidades claras, nomes previsíveis e regras centralizadas.