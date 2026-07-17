# Nexor — Guia de MVVM

## 1. Objetivo

Este documento define como o padrão **MVVM** deve ser aplicado no Nexor.

O objetivo é manter a interface WPF separada das regras de negócio, da persistência e dos casos de uso.

O projeto utiliza:

- C#;
- .NET 8;
- WPF;
- MVVM;
- SQLite;
- arquitetura em camadas.

O MVVM deve ajudar a tornar o código:

- testável;
- organizado;
- previsível;
- reutilizável;
- independente da interface;
- preparado para crescimento.

---

# 2. Estrutura do MVVM

MVVM significa:

```text
Model
View
ViewModel
```

No Nexor, essa divisão deve ser interpretada junto com a arquitetura em camadas.

```text
View
  ↓
ViewModel
  ↓
Application
  ↓
Domain
  ↓
Infrastructure
```

A ViewModel não substitui a camada de aplicação.

Ela coordena o estado visual e chama os casos de uso.

---

# 3. Responsabilidades

## 3.1 View

A View representa a interface visual.

Arquivos comuns:

```text
MainWindow.xaml
HomeView.xaml
OperationView.xaml
RollsView.xaml
SettingsView.xaml
AboutView.xaml
```

A View deve conter:

- layout;
- controles;
- bindings;
- estilos;
- templates;
- recursos visuais;
- comportamento estritamente relacionado à apresentação.

A View não deve conter:

- SQL;
- cálculo de metragem;
- prevenção de duplicidade;
- fechamento de rolo;
- regras de agrupamento;
- leitura direta de arquivos;
- geração de PDF;
- geração de JPG;
- lógica de persistência.

---

## 3.2 ViewModel

A ViewModel representa o estado e o comportamento da tela.

Deve conter:

- propriedades observáveis;
- comandos;
- seleção;
- loading;
- mensagens;
- filtros;
- validações de interface;
- chamadas aos casos de uso;
- transformação de dados para apresentação.

A ViewModel não deve:

- manipular diretamente controles;
- acessar elementos por nome;
- executar SQL;
- abrir conexão SQLite;
- interpretar arquivos diretamente;
- gerar relatórios;
- conter regras centrais de domínio;
- criar Views diretamente.

---

## 3.3 Model

No contexto do Nexor, Model não representa uma única pasta.

O Model é composto principalmente por:

- entidades do domínio;
- value objects;
- DTOs;
- resultados;
- modelos de apresentação;
- modelos de relatório.

Exemplos:

```text
ImportedLog
PrintItem
Roll
RollItem
RollEvent
RollSummaryDto
PrintItemRowViewModel
```

---

# 4. Relação entre as camadas

A View deve conhecer apenas sua ViewModel e recursos visuais.

A ViewModel deve chamar serviços da camada Application.

A Application coordena o Domain e contratos externos.

A Infrastructure implementa:

- banco;
- arquivos;
- parser;
- configurações;
- logging.

O Reporting implementa:

- PDF;
- PDF resumido;
- JPG espelhado.

Fluxo correto:

```text
Usuário clica
      ↓
Command da ViewModel
      ↓
Application Service
      ↓
Domain
      ↓
Repository / Infrastructure
      ↓
Resultado
      ↓
ViewModel atualiza estado
      ↓
View exibe
```

---

# 5. Estrutura sugerida

```text
Nexor.Desktop/
├── Navigation/
├── Services/
├── ViewModels/
│   ├── MainViewModel.cs
│   ├── Home/
│   │   └── HomeViewModel.cs
│   ├── Operation/
│   │   ├── OperationViewModel.cs
│   │   ├── PrintItemRowViewModel.cs
│   │   └── RollSummaryViewModel.cs
│   ├── Rolls/
│   │   ├── RollsViewModel.cs
│   │   ├── RollListItemViewModel.cs
│   │   └── RollDetailsViewModel.cs
│   ├── Settings/
│   │   └── SettingsViewModel.cs
│   └── About/
│       └── AboutViewModel.cs
│
└── Views/
    ├── MainWindow.xaml
    ├── Home/
    ├── Operation/
    ├── Rolls/
    ├── Settings/
    └── About/
```

A estrutura real deve ser respeitada antes de criar novas pastas.

---

# 6. BaseViewModel

As ViewModels podem herdar de uma classe base que implemente `INotifyPropertyChanged`.

Exemplo:

```csharp
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace Nexor.Desktop.ViewModels;

public abstract class ViewModelBase : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    protected bool SetProperty<T>(
        ref T field,
        T value,
        [CallerMemberName] string? propertyName = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value))
        {
            return false;
        }

        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }

    protected void OnPropertyChanged(
        [CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(
            this,
            new PropertyChangedEventArgs(propertyName));
    }
}
```

## Regras

- notificar somente quando o valor mudar;
- evitar chamadas duplicadas;
- usar nomes de propriedades corretos;
- não colocar lógica de negócio na classe base;
- não transformar a base em depósito de funcionalidades.

---

# 7. Propriedades observáveis

Exemplo:

```csharp
private string _searchText = string.Empty;

public string SearchText
{
    get => _searchText;
    set
    {
        if (SetProperty(ref _searchText, value))
        {
            ApplyFilters();
        }
    }
}
```

Quando a alteração disparar uma operação pesada, não executar diretamente em cada tecla sem controle.

Pode ser necessário usar:

- debounce;
- comando;
- cancelamento;
- carregamento assíncrono.

---

# 8. Propriedades derivadas

Exemplo:

```csharp
public int SelectedItemCount =>
    Items.Count(item => item.IsSelected);

public decimal SelectedPrintedLength =>
    Items
        .Where(item => item.IsSelected)
        .Sum(item => item.PrintedLengthMeters);
```

Quando uma propriedade dependente mudar, notificar explicitamente:

```csharp
OnPropertyChanged(nameof(SelectedItemCount));
OnPropertyChanged(nameof(SelectedPrintedLength));
```

Para regras centrais, prefira receber o cálculo da camada Application ou Domain.

---

# 9. Commands

Ações da interface devem ser representadas por comandos.

Exemplos:

```text
ImportFilesCommand
ImportFolderCommand
RefreshCommand
ClearFiltersCommand
ClearSelectionCommand
ReviewRollCommand
CloseRollCommand
SearchRollsCommand
ReexportCommand
SaveSettingsCommand
```

Evite eventos `Click` no code-behind quando um command resolver.

---

# 10. RelayCommand

Exemplo simplificado:

```csharp
using System.Windows.Input;

namespace Nexor.Desktop.Commands;

public sealed class RelayCommand : ICommand
{
    private readonly Action _execute;
    private readonly Func<bool>? _canExecute;

    public RelayCommand(
        Action execute,
        Func<bool>? canExecute = null)
    {
        _execute = execute
            ?? throw new ArgumentNullException(nameof(execute));

        _canExecute = canExecute;
    }

    public event EventHandler? CanExecuteChanged;

    public bool CanExecute(object? parameter)
    {
        return _canExecute?.Invoke() ?? true;
    }

    public void Execute(object? parameter)
    {
        _execute();
    }

    public void RaiseCanExecuteChanged()
    {
        CanExecuteChanged?.Invoke(this, EventArgs.Empty);
    }
}
```

O projeto pode utilizar implementação própria ou biblioteca aprovada.

Evite adicionar biblioteca apenas para um command simples sem avaliar necessidade.

---

# 11. AsyncCommand

Operações assíncronas devem utilizar comandos assíncronos.

Exemplo:

```csharp
public interface IAsyncCommand : ICommand
{
    Task ExecuteAsync(object? parameter = null);
}
```

Implementação conceitual:

```csharp
public sealed class AsyncRelayCommand : IAsyncCommand
{
    private readonly Func<Task> _execute;
    private readonly Func<bool>? _canExecute;
    private bool _isExecuting;

    public AsyncRelayCommand(
        Func<Task> execute,
        Func<bool>? canExecute = null)
    {
        _execute = execute
            ?? throw new ArgumentNullException(nameof(execute));

        _canExecute = canExecute;
    }

    public event EventHandler? CanExecuteChanged;

    public bool CanExecute(object? parameter)
    {
        return !_isExecuting &&
               (_canExecute?.Invoke() ?? true);
    }

    public async void Execute(object? parameter)
    {
        await ExecuteAsync(parameter);
    }

    public async Task ExecuteAsync(object? parameter = null)
    {
        if (!CanExecute(parameter))
        {
            return;
        }

        try
        {
            _isExecuting = true;
            RaiseCanExecuteChanged();

            await _execute();
        }
        finally
        {
            _isExecuting = false;
            RaiseCanExecuteChanged();
        }
    }

    public void RaiseCanExecuteChanged()
    {
        CanExecuteChanged?.Invoke(this, EventArgs.Empty);
    }
}
```

`async void` deve ficar restrito à implementação exigida por `ICommand` ou a event handlers.

---

# 12. Estado de carregamento

Toda operação demorada deve possuir estado explícito.

Exemplo:

```csharp
private bool _isLoading;

public bool IsLoading
{
    get => _isLoading;
    private set
    {
        if (SetProperty(ref _isLoading, value))
        {
            ImportFilesCommand.RaiseCanExecuteChanged();
            CloseRollCommand.RaiseCanExecuteChanged();
        }
    }
}
```

A View pode usar:

```xml
<Grid>
    <ContentControl Content="{Binding CurrentContent}" />

    <Grid Visibility="{Binding IsLoading,
        Converter={StaticResource BooleanToVisibilityConverter}}">
        <TextBlock Text="Carregando..." />
    </Grid>
</Grid>
```

O loading não deve travar toda a aplicação quando apenas uma área precisa ser bloqueada.

---

# 13. Mensagens

ViewModels não devem abrir `MessageBox` diretamente.

Evite:

```csharp
MessageBox.Show("Rolo fechado.");
```

Prefira um contrato:

```csharp
public interface IDialogService
{
    Task ShowInformationAsync(
        string title,
        string message);

    Task ShowErrorAsync(
        string title,
        string message);

    Task<bool> ConfirmAsync(
        string title,
        string message);
}
```

A implementação concreta fica no projeto Desktop.

---

# 14. Serviço de diálogo

Exemplo de uso:

```csharp
var confirmed = await _dialogService.ConfirmAsync(
    "Confirmar fechamento",
    "A composição do rolo será preservada no histórico.");

if (!confirmed)
{
    return;
}

var result = await _closeRollService.CloseAsync(
    command,
    cancellationToken);
```

A ViewModel não deve conhecer:

- janela concreta;
- posição;
- `MessageBoxButton`;
- `MessageBoxImage`.

---

# 15. FilePicker e FolderPicker

A seleção de arquivos é responsabilidade da interface.

Use contratos:

```csharp
public interface IFilePickerService
{
    Task<IReadOnlyList<string>> PickFilesAsync(
        FilePickerOptions options);
}

public interface IFolderPickerService
{
    Task<string?> PickFolderAsync();
}
```

A ViewModel recebe os caminhos e chama o caso de uso da Application.

---

# 16. Clipboard

Use serviço próprio:

```csharp
public interface IClipboardService
{
    void SetText(string text);
}
```

Exemplo:

```csharp
_clipboardService.SetText(SelectedRoll.Code);
StatusText = "Código do rolo copiado.";
```

Isso facilita testes e evita dependência direta de `Clipboard`.

---

# 17. Navegação

A navegação deve ser centralizada.

Contrato sugerido:

```csharp
public interface INavigationService
{
    object CurrentViewModel { get; }

    void NavigateTo<TViewModel>()
        where TViewModel : class;
}
```

Outra opção é usar uma chave de navegação:

```csharp
public enum NavigationTarget
{
    Home,
    Operation,
    Rolls,
    Settings,
    About
}
```

---

# 18. MainViewModel

O `MainViewModel` deve coordenar:

- tela atual;
- navegação;
- título;
- status;
- itens da sidebar;
- informações gerais da janela.

Exemplo:

```csharp
public sealed class MainViewModel : ViewModelBase
{
    private object _currentViewModel;

    public object CurrentViewModel
    {
        get => _currentViewModel;
        private set => SetProperty(
            ref _currentViewModel,
            value);
    }

    public string CurrentTitle { get; private set; }

    public string StatusText { get; set; }
}
```

Ele não deve:

- importar arquivos;
- executar SQL;
- gerar relatórios;
- conter toda a lógica das telas;
- criar cada View manualmente.

---

# 19. CurrentViewModel

A janela principal pode possuir:

```xml
<ContentControl Content="{Binding CurrentViewModel}" />
```

Com DataTemplates:

```xml
<DataTemplate DataType="{x:Type vm:HomeViewModel}">
    <views:HomeView />
</DataTemplate>

<DataTemplate DataType="{x:Type vm:OperationViewModel}">
    <views:OperationView />
</DataTemplate>
```

Isso evita controlar cada tela por vários blocos de `Visibility`.

---

# 20. Sidebar

Cada item da sidebar pode ser representado por:

```csharp
public sealed class NavigationItemViewModel : ViewModelBase
{
    public string Label { get; init; } = string.Empty;

    public object Icon { get; init; } = default!;

    public NavigationTarget Target { get; init; }

    public bool IsSelected { get; set; }

    public ICommand NavigateCommand { get; init; } = default!;
}
```

A seleção deve ser derivada da navegação atual.

Evite manter estados contraditórios entre:

- botão ativo;
- tela exibida;
- título da topbar.

---

# 21. OperationViewModel

Responsabilidades esperadas:

- carregar itens disponíveis;
- manter filtros;
- manter seleção;
- disparar importação;
- solicitar resumo do rolo;
- abrir revisão;
- exibir resultados;
- atualizar status visual.

Não deve:

- calcular o hash;
- interpretar arquivos;
- executar SQL;
- decidir regras de fechamento;
- gerar PDF.

Estrutura conceitual:

```csharp
public sealed class OperationViewModel : ViewModelBase
{
    public ObservableCollection<PrintItemRowViewModel> Items { get; }

    public RollSummaryViewModel RollSummary { get; }

    public string SearchText { get; set; }

    public MachineFilterItem? SelectedMachine { get; set; }

    public bool IsLoading { get; }

    public IAsyncCommand ImportFilesCommand { get; }

    public IAsyncCommand ImportFolderCommand { get; }

    public IAsyncCommand ReviewRollCommand { get; }

    public ICommand ClearSelectionCommand { get; }
}
```

---

# 22. PrintItemRowViewModel

Representa uma linha da tabela.

Exemplo:

```csharp
public sealed class PrintItemRowViewModel : ViewModelBase
{
    private bool _isSelected;

    public long Id { get; init; }

    public DateTimeOffset PrintedAt { get; init; }

    public string DocumentName { get; init; } = string.Empty;

    public string FabricName { get; init; } = string.Empty;

    public decimal PrintedLengthMeters { get; init; }

    public PrintItemStatus Status { get; init; }

    public bool CanBeSelected =>
        Status is PrintItemStatus.Ready
            or PrintItemStatus.Suspicious;

    public bool IsSelected
    {
        get => _isSelected;
        set
        {
            if (!CanBeSelected)
            {
                return;
            }

            SetProperty(ref _isSelected, value);
        }
    }
}
```

A regra de elegibilidade definitiva deve vir da camada Application ou Domain.

A ViewModel de linha não deve inventar estados diferentes da regra oficial.

---

# 23. Seleção

Existem duas estratégias possíveis:

## Propriedade por linha

Cada item possui `IsSelected`.

Vantagens:

- binding simples;
- fácil interação com checkbox.

## Coleção de IDs selecionados

A ViewModel principal mantém:

```csharp
HashSet<long> SelectedItemIds
```

Vantagens:

- separação do estado visual;
- eficiência em listas grandes.

A escolha deve ser consistente.

Não usar simultaneamente múltiplas fontes de verdade sem sincronização clara.

---

# 24. Resumo do rolo

O resumo pode possuir ViewModel próprio:

```csharp
public sealed class RollSummaryViewModel : ViewModelBase
{
    public string ProposedCode { get; set; } = string.Empty;

    public string MachineName { get; set; } = string.Empty;

    public int TotalItems { get; set; }

    public decimal TotalPrintedLengthMeters { get; set; }

    public int TotalBlocks { get; set; }

    public IReadOnlyList<FabricBlockViewModel> Blocks { get; set; }
        = Array.Empty<FabricBlockViewModel>();

    public bool HasBlockingWarnings { get; set; }
}
```

O cálculo deve ser fornecido por um serviço da Application.

---

# 25. RollsViewModel

Responsabilidades:

- manter filtros;
- executar busca;
- exibir resultados;
- manter rolo selecionado;
- carregar detalhes;
- executar reexportação;
- copiar código.

Exemplo:

```csharp
public sealed class RollsViewModel : ViewModelBase
{
    public ObservableCollection<RollListItemViewModel> Rolls { get; }

    public RollDetailsViewModel? SelectedRollDetails { get; }

    public string CodeFilter { get; set; } = string.Empty;

    public string DocumentFilter { get; set; } = string.Empty;

    public int ResultLimit { get; set; } = 300;

    public IAsyncCommand SearchCommand { get; }

    public IAsyncCommand ReexportCommand { get; }

    public ICommand CopyCodeCommand { get; }
}
```

---

# 26. SettingsViewModel

Responsabilidades:

- carregar preferências;
- validar entradas;
- selecionar pastas;
- salvar;
- restaurar padrões;
- trocar tema.

Exemplo:

```csharp
public sealed class SettingsViewModel : ViewModelBase
{
    public string SelectedTheme { get; set; } = string.Empty;

    public string ImportFolder { get; set; } = string.Empty;

    public string PdfExportFolder { get; set; } = string.Empty;

    public string MirrorExportFolder { get; set; } = string.Empty;

    public int SearchResultLimit { get; set; }

    public IAsyncCommand SaveCommand { get; }

    public ICommand RestoreDefaultsCommand { get; }
}
```

A validação dos caminhos pode envolver serviços da Application ou Desktop.

---

# 27. AboutViewModel

Responsabilidades:

- versão;
- edição;
- caminho local;
- caminho dos logs;
- informações de licença;
- informações da Trial;
- link do repositório.

A versão deve ser obtida do assembly ou de serviço central.

Evite escrever manualmente:

```csharp
Version = "0.2.6";
```

em vários locais.

---

# 28. ObservableCollection

Use `ObservableCollection<T>` quando a View precisar observar:

- adição;
- remoção;
- substituição.

Para dados somente leitura que são substituídos de uma vez, pode ser suficiente usar:

```csharp
IReadOnlyList<T>
```

Não use `ObservableCollection` automaticamente em toda propriedade.

---

# 29. CollectionView

Filtros e ordenação visual podem utilizar:

```text
ICollectionView
```

Porém, regras de consulta importantes devem ser aplicadas na camada Application e no banco.

Não carregue todos os registros apenas para filtrar na memória quando o volume crescer.

---

# 30. Binding

Exemplo:

```xml
<TextBox Text="{Binding SearchText,
                        UpdateSourceTrigger=PropertyChanged}" />
```

Utilize `UpdateSourceTrigger=PropertyChanged` somente quando a atualização imediata for necessária.

Para campos que serão salvos posteriormente, o comportamento padrão pode ser suficiente.

---

# 31. Binding errors

Erros de binding devem ser tratados como falhas de desenvolvimento.

Durante o desenvolvimento, revisar o Output da aplicação.

Problemas comuns:

- propriedade inexistente;
- DataContext incorreto;
- converter ausente;
- tipo incompatível;
- comando nulo;
- `RelativeSource` incorreto.

Não ignorar mensagens repetidas de binding.

---

# 32. DataContext

Prefira atribuir DataContext por:

- injeção de dependência;
- DataTemplate;
- composição central.

Evite criar ViewModel diretamente no XAML quando ele possuir dependências:

```xml
<UserControl.DataContext>
    <vm:OperationViewModel />
</UserControl.DataContext>
```

Prefira receber a ViewModel já construída.

---

# 33. Dependency Injection

A composição deve ocorrer na inicialização da aplicação.

Exemplo conceitual:

```csharp
services.AddSingleton<MainViewModel>();
services.AddTransient<HomeViewModel>();
services.AddTransient<OperationViewModel>();
services.AddTransient<RollsViewModel>();
services.AddTransient<SettingsViewModel>();
services.AddTransient<AboutViewModel>();
```

A escolha entre Singleton e Transient deve considerar o estado da tela.

---

# 34. Ciclo de vida das ViewModels

## Singleton

Adequado quando:

- estado deve persistir;
- existe uma única instância;
- a tela é central.

Exemplo possível:

```text
MainViewModel
```

## Transient

Adequado quando:

- estado deve ser renovado;
- a tela é recriada;
- não há necessidade de preservar filtros.

## Scoped

Aplicações desktop normalmente não possuem escopo de requisição como aplicações web.

Pode ser criado um escopo manual para operações específicas, mas somente quando necessário.

---

# 35. Preservação de estado

Decidir explicitamente se ao navegar a tela deve manter:

- filtros;
- seleção;
- posição de scroll;
- aba atual;
- dados carregados.

A seleção de um rolo em montagem não deve ser descartada sem confirmação.

Filtros históricos podem ser preservados durante a sessão.

---

# 36. Inicialização assíncrona

Construtores não devem realizar operações assíncronas.

Evite:

```csharp
public OperationViewModel()
{
    LoadAsync().Wait();
}
```

Prefira:

```csharp
public async Task InitializeAsync()
{
    await LoadItemsAsync();
}
```

A navegação ou View pode solicitar inicialização por interface específica:

```csharp
public interface IAsyncInitializable
{
    Task InitializeAsync(
        CancellationToken cancellationToken);
}
```

---

# 37. Ativação de tela

Pode existir:

```csharp
public interface INavigationAware
{
    Task OnNavigatedToAsync(
        CancellationToken cancellationToken);

    Task OnNavigatedFromAsync(
        CancellationToken cancellationToken);
}
```

Use somente se houver necessidade real de carregar ou preservar estado ao navegar.

---

# 38. CancellationToken

ViewModels devem cancelar operações quando:

- usuário cancelar;
- nova busca substituir a anterior;
- tela for fechada;
- navegação invalidar o carregamento.

Exemplo:

```csharp
private CancellationTokenSource? _searchCancellation;

private async Task SearchAsync()
{
    _searchCancellation?.Cancel();
    _searchCancellation?.Dispose();

    _searchCancellation = new CancellationTokenSource();

    await _searchRollsService.SearchAsync(
        CreateFilter(),
        _searchCancellation.Token);
}
```

---

# 39. Debounce

Busca textual pode usar debounce.

Exemplo conceitual:

```text
usuário digita
→ aguarda 300 ms
→ cancela busca anterior
→ executa nova busca
```

Não consultar o banco em cada tecla sem controle.

---

# 40. Validação

Validações de interface podem usar:

- propriedades de erro;
- `INotifyDataErrorInfo`;
- mensagens próximas aos campos.

Exemplo:

```csharp
public bool HasErrors =>
    !string.IsNullOrWhiteSpace(CodeError)
    || !string.IsNullOrWhiteSpace(MachineError);
```

Regras críticas devem permanecer no Domain ou Application.

A UI pode antecipar a validação, mas não ser a única defesa.

---

# 41. INotifyDataErrorInfo

Pode ser utilizado para validação assíncrona e múltiplos erros.

Exemplos:

- código duplicado;
- pasta inacessível;
- valor de DPI inválido;
- limite de consulta inválido.

Não implementar uma infraestrutura complexa se validações simples forem suficientes.

---

# 42. Converters

Converters são adequados para:

- boolean para visibilidade;
- status para brush;
- enum para texto visual;
- valor nulo para estado.

Exemplo:

```csharp
public sealed class BooleanToVisibilityConverter : IValueConverter
{
    public object Convert(
        object value,
        Type targetType,
        object parameter,
        CultureInfo culture)
    {
        return value is true
            ? Visibility.Visible
            : Visibility.Collapsed;
    }

    public object ConvertBack(
        object value,
        Type targetType,
        object parameter,
        CultureInfo culture)
    {
        throw new NotSupportedException();
    }
}
```

Converters não devem executar casos de uso.

---

# 43. MultiBinding

Use `MultiBinding` somente quando melhorar a apresentação.

Não usar para implementar regra operacional complexa.

Exemplo aceitável:

```text
mostrar texto baseado em quantidade e metragem
```

Exemplo inadequado:

```text
determinar se um rolo pode ser fechado
```

A regra de fechamento deve vir de propriedade da ViewModel.

---

# 44. Code-behind permitido

Casos aceitáveis:

- drag and drop;
- foco;
- scroll;
- atalhos de janela;
- integração com controles;
- manipulação visual específica.

Exemplo de drag and drop:

```csharp
private async void OnDrop(
    object sender,
    DragEventArgs e)
{
    if (!e.Data.GetDataPresent(DataFormats.FileDrop))
    {
        return;
    }

    var paths = (string[])e.Data.GetData(
        DataFormats.FileDrop);

    await ViewModel.ImportDroppedPathsAsync(paths);
}
```

O code-behind apenas coleta os caminhos.

A importação real permanece fora dele.

---

# 45. Code-behind proibido

Não colocar:

```csharp
var connection = new SqliteConnection(...);
```

```csharp
var meters = heightMm / 1000m;
```

```csharp
File.WriteAllBytes(...);
```

```csharp
repository.CloseRoll(...);
```

em eventos da View.

---

# 46. Temas e MVVM

A seleção do tema pode estar na ViewModel.

A aplicação do `ResourceDictionary` pertence a um serviço visual.

Contrato:

```csharp
public interface IThemeService
{
    IReadOnlyList<string> AvailableThemes { get; }

    string CurrentTheme { get; }

    void ApplyTheme(string themeName);
}
```

A ViewModel solicita:

```csharp
_themeService.ApplyTheme(SelectedTheme);
```

Ela não deve manipular diretamente:

```text
Application.Current.Resources.MergedDictionaries
```

---

# 47. Status bar

O texto da barra de status pode ser gerenciado por:

- `MainViewModel`;
- serviço de status;
- messenger/event aggregator.

Exemplo de serviço:

```csharp
public interface IStatusService
{
    string CurrentMessage { get; }

    void Show(string message);

    void Clear();
}
```

Evite dependência circular entre ViewModels apenas para atualizar o status.

---

# 48. Comunicação entre ViewModels

Opções:

- serviço compartilhado;
- eventos;
- messenger;
- navegação com parâmetros;
- estado de sessão.

Não referenciar uma ViewModel diretamente em outra sem necessidade.

Evite:

```csharp
_operationViewModel.MainViewModel.StatusText = "...";
```

Prefira um contrato compartilhado.

---

# 49. Messenger

Um messenger pode ser útil para eventos de UI desacoplados.

Exemplos:

- rolo fechado;
- tema alterado;
- importação concluída;
- dados atualizados.

Não usar messenger como substituto de chamadas normais de serviço.

Mensagens globais demais tornam o fluxo difícil de rastrear.

---

# 50. Dialog ViewModels

Diálogos complexos devem possuir ViewModel próprio.

Exemplo:

```text
RollReviewDialogViewModel
```

Responsabilidades:

- dados do rolo;
- código;
- máquina;
- observações;
- confirmação;
- validação visual.

O fechamento real permanece em um caso de uso.

---

# 51. Resultado de diálogo

O serviço pode retornar resultado estruturado:

```csharp
public sealed record RollReviewDialogResult(
    bool Confirmed,
    string RollCode,
    long MachineId,
    string? Notes,
    bool ExportAfterClosing);
```

Isso evita que a ViewModel principal acesse diretamente os campos do diálogo.

---

# 52. Empty states

A ViewModel deve expor estado suficiente para a View decidir o empty state.

Exemplo:

```csharp
public bool HasItems => Items.Count > 0;

public bool ShowEmptyState =>
    !IsLoading && Items.Count == 0;
```

Não use converter complexo para inferir várias condições ocultas.

---

# 53. Erros

A ViewModel pode expor:

```csharp
public string? ErrorMessage { get; private set; }

public bool HasError =>
    !string.IsNullOrWhiteSpace(ErrorMessage);
```

Erros bloqueantes podem usar `IDialogService`.

Erros não bloqueantes podem aparecer em painel.

Detalhes técnicos devem permanecer nos logs.

---

# 54. Modelos de linha

Evite expor entidades diretamente quando a tela precisa de:

- seleção;
- texto formatado;
- comandos por linha;
- estado visual;
- propriedades derivadas.

Use ViewModel específico:

```text
PrintItemRowViewModel
RollListItemViewModel
ExportRecordRowViewModel
```

Não duplique regras de domínio nesses modelos.

---

# 55. Formatação

Pode ser exposta pela ViewModel:

```csharp
public string PrintedLengthDisplay =>
    $"{PrintedLengthMeters:N2} m";
```

Ou via converter.

A decisão deve ser consistente.

Valores brutos devem continuar disponíveis.

---

# 56. DateTime e cultura

A ViewModel pode formatar para `pt-BR`.

Exemplo:

```csharp
public string PrintedAtDisplay =>
    PrintedAt.ToLocalTime()
        .ToString("dd/MM/yyyy HH:mm:ss");
```

A persistência continua usando ISO 8601.

---

# 57. Testes de ViewModel

ViewModels devem ser testadas sem abrir janelas.

Cobrir:

- carregamento;
- comandos;
- `CanExecute`;
- seleção;
- filtros;
- mensagens;
- tratamento de erro;
- loading;
- cancelamento;
- navegação.

Use fakes ou mocks dos serviços.

---

# 58. Exemplo de teste

```csharp
[Fact]
public async Task ImportFilesCommand_ValidFiles_UpdatesItems()
{
    // Arrange
    var importService = new FakeImportFilesService();
    var filePicker = new FakeFilePickerService(
        "log-01.txt");

    var viewModel = CreateViewModel(
        importService,
        filePicker);

    // Act
    await viewModel.ImportFilesCommand.ExecuteAsync();

    // Assert
    Assert.Single(viewModel.Items);
    Assert.Equal(
        "1 arquivo importado.",
        viewModel.StatusText);
}
```

Não testar a implementação concreta do banco em teste de ViewModel.

---

# 59. Testes de navegação

Cobrir:

- tela inicial;
- mudança de tela;
- título;
- item ativo;
- preservação de estado;
- inicialização assíncrona;
- cancelamento da tela anterior.

---

# 60. Testes de commands

Confirmar:

- desabilitado sem seleção;
- habilitado com seleção válida;
- desabilitado durante carregamento;
- reativado após conclusão;
- exceções tratadas;
- execução única.

---

# 61. Evitar ViewModels gigantes

Sinais de excesso:

- centenas de propriedades;
- dezenas de comandos;
- múltiplos fluxos;
- importação, fechamento e consulta na mesma classe;
- muitas dependências;
- lógica de relatório;
- lógica de banco.

Dividir por:

- componente;
- painel;
- funcionalidade;
- diálogo.

Exemplo:

```text
OperationViewModel
RollSummaryViewModel
ImportResultViewModel
RollReviewDialogViewModel
```

---

# 62. Evitar dependências excessivas

Uma ViewModel com muitas dependências pode indicar excesso de responsabilidades.

Exemplo problemático:

```text
12 serviços no construtor
```

Possíveis soluções:

- dividir ViewModel;
- criar um caso de uso mais coeso;
- agrupar contratos relacionados com cuidado;
- revisar a responsabilidade.

Não criar um serviço genérico gigante apenas para reduzir o construtor.

---

# 63. Design-time DataContext

Pode ser utilizado para melhorar a experiência no designer.

Exemplo:

```xml
d:DataContext="{d:DesignInstance
    Type=vm:OperationViewModel,
    IsDesignTimeCreatable=False}"
```

Não permitir que dados de design cheguem ao build final como dados reais.

---

# 64. ViewModelLocator

O padrão ViewModelLocator pode ser utilizado, mas não é obrigatório.

Com injeção de dependência e DataTemplates, pode ser desnecessário.

Não adicionar um locator apenas por tradição.

---

# 65. Bibliotecas MVVM

Possíveis opções:

- implementação própria;
- CommunityToolkit.Mvvm;
- ReactiveUI;
- Prism.

Antes de escolher, avaliar:

- complexidade;
- curva de aprendizado;
- tamanho;
- recursos necessários;
- compatibilidade;
- manutenção;
- impacto arquitetural.

Para o escopo inicial, uma solução simples pode ser suficiente.

---

# 66. CommunityToolkit.Mvvm

Pode reduzir código repetitivo com:

```text
ObservableObject
ObservableProperty
RelayCommand
AsyncRelayCommand
Messenger
```

Porém, a adoção deve ser consciente.

Não misturar padrões próprios e toolkit sem consistência.

---

# 67. Prism

Prism oferece:

- navegação;
- regiões;
- DI;
- eventos;
- módulos.

Pode ser excessivo para o escopo inicial.

Só deve ser adotado se a complexidade real justificar.

---

# 68. ReactiveUI

ReactiveUI oferece fluxo reativo avançado.

Também aumenta a curva de aprendizado.

Não deve ser adotado apenas para resolver bindings e commands simples.

---

# 69. Padrão recomendado inicial

Para o Nexor atual:

- `ViewModelBase`;
- `RelayCommand`;
- `AsyncRelayCommand`;
- `INavigationService`;
- `IDialogService`;
- `IThemeService`;
- `IFilePickerService`;
- injeção de dependência;
- DataTemplates;
- ViewModels por tela.

Esse conjunto é suficiente para o núcleo inicial sem excesso de infraestrutura.

---

# 70. Anti-patterns

Evitar:

## ViewModel como service locator

```csharp
ServiceProvider.GetService<IRollRepository>();
```

## ViewModel acessando banco

```csharp
new SqliteConnection(...)
```

## ViewModel criando View

```csharp
new RollReviewDialog().ShowDialog();
```

## View acessando domínio diretamente

```csharp
roll.Close();
```

## Converter com regra de negócio

```csharp
return heightMm / 1000m;
```

## Navegação por múltiplos `Visibility`

```csharp
HomeView.Visibility = ...
OperationView.Visibility = ...
```

espalhada em vários locais.

---

# 71. Fluxo de importação via MVVM

```text
ImportFilesCommand
        ↓
IFilePickerService
        ↓
ImportFilesService
        ↓
resultado
        ↓
OperationViewModel atualiza Items
        ↓
View exibe tabela
```

---

# 72. Fluxo de fechamento via MVVM

```text
ReviewRollCommand
        ↓
Application cria resumo
        ↓
IDialogService abre revisão
        ↓
usuário confirma
        ↓
CloseRollService
        ↓
resultado persistido
        ↓
ViewModel atualiza tela
        ↓
resultado exibido
```

---

# 73. Fluxo de consulta via MVVM

```text
SearchCommand
        ↓
SearchRollsService
        ↓
Repository
        ↓
RollSummaryDto
        ↓
RollsViewModel
        ↓
DataGrid
```

Ao selecionar:

```text
SelectedRoll
        ↓
GetRollDetailsService
        ↓
RollDetailsViewModel
```

---

# 74. Fluxo de tema via MVVM

```text
SettingsViewModel.SelectedTheme
        ↓
IThemeService.ApplyTheme()
        ↓
ResourceDictionary atualizado
        ↓
configuração persistida
        ↓
interface atualizada
```

---

# 75. Estado da sessão

Pode existir um serviço de sessão para dados temporários compartilhados.

Exemplo:

```csharp
public interface IApplicationSession
{
    long? CurrentMachineId { get; set; }

    IReadOnlyCollection<long> SelectedPrintItemIds { get; }

    void ClearCurrentRollSelection();
}
```

Use com cautela.

Não transformar o serviço em estado global sem controle.

---

# 76. Múltiplas instâncias de ViewModel

Se uma tela for criada várias vezes, confirmar:

- eventos são removidos;
- subscriptions são descartadas;
- timers são encerrados;
- CancellationTokenSource é descartado;
- não há vazamento de memória.

---

# 77. IDisposable

ViewModels podem implementar `IDisposable` quando possuírem:

- subscriptions;
- timers;
- watchers;
- CancellationTokenSource;
- recursos visuais indiretos.

Não implementar sem necessidade.

---

# 78. Weak events

Eventos de longa duração podem causar retenção de ViewModels.

Avaliar:

- unsubscribe explícito;
- weak event;
- messenger com ciclo controlado.

Esse cuidado é especialmente importante para serviços singleton.

---

# 79. Threads

Alterações em `ObservableCollection` ligada à UI devem ocorrer na thread da interface.

Operações pesadas podem rodar fora dela, mas a atualização final deve retornar ao Dispatcher quando necessário.

Evite espalhar `Dispatcher.Invoke` por ViewModels.

Pode ser criado um serviço de dispatcher:

```csharp
public interface IUiDispatcher
{
    Task InvokeAsync(Action action);
}
```

Use apenas quando necessário.

---

# 80. Progress

Operações longas podem usar:

```csharp
IProgress<ImportProgress>
```

Exemplo:

```csharp
public sealed record ImportProgress(
    int Processed,
    int Total,
    string CurrentFile);
```

A ViewModel atualiza:

- percentual;
- arquivo atual;
- mensagem.

---

# 81. Estado de progresso

```csharp
public int ProgressValue { get; private set; }

public int ProgressMaximum { get; private set; }

public string ProgressMessage { get; private set; }
```

Não mostrar progresso falso.

Caso não seja possível medir, usar indicador indeterminado.

---

# 82. Validação de CanExecute

Exemplo:

```csharp
private bool CanReviewRoll()
{
    return !IsLoading
        && SelectedItemCount > 0
        && !RollSummary.HasBlockingWarnings;
}
```

Quando dependências mudarem:

```csharp
ReviewRollCommand.RaiseCanExecuteChanged();
```

Não permitir ação visualmente e bloquear somente depois, quando a condição já puder ser conhecida.

---

# 83. Estado selecionado e desabilitado

A ViewModel deve distinguir:

- item selecionado;
- item não selecionado;
- item não elegível;
- item já vinculado;
- item suspeito.

Não use apenas `IsSelected`.

Possíveis propriedades:

```csharp
CanBeSelected
IsSelected
IsAssigned
IsSuspicious
StatusText
```

---

# 84. ViewModels e domínio

ViewModels podem receber DTOs, mas não devem alterar entidades diretamente.

Evite:

```csharp
SelectedRoll.Status = RollStatus.Closed;
```

Prefira chamar:

```csharp
await _closeRollService.CloseAsync(...);
```

e recarregar o estado retornado.

---

# 85. Atualização otimista

A interface não deve mostrar fechamento concluído antes de o banco confirmar.

Fluxo correto:

```text
mostrar loading
→ executar
→ confirmar persistência
→ atualizar UI
```

Não atualizar o status para Fechado e tentar salvar depois sem mecanismo de rollback visual.

---

# 86. Cache de ViewModel

Pode ser útil para:

- manter filtros;
- evitar recarregamento;
- preservar seleção.

Porém, dados operacionais devem poder ser atualizados.

Defina quando:

- recarregar;
- invalidar;
- manter;
- limpar.

---

# 87. Refresh

Toda tela que apresenta dados persistidos deve possuir estratégia de atualização.

Pode ser:

- ao navegar;
- por botão;
- após evento;
- por timer futuro;
- por watcher.

Não recarregar continuamente sem necessidade.

---

# 88. Estado vazio versus erro

Distinguir:

```text
não há dados
```

de:

```text
falha ao carregar dados
```

A ViewModel deve expor estados diferentes.

Exemplo:

```csharp
public bool HasItems { get; }
public bool HasError { get; }
public bool ShowEmptyState { get; }
```

---

# 89. StatusText

Mensagens de status não devem substituir erros estruturados.

Use para:

- confirmação curta;
- última ação;
- progresso discreto.

Exemplo:

```text
18 registros carregados.
```

Para falha crítica, usar painel ou diálogo.

---

# 90. Teste dos temas

Cada tela deve ser validada nos temas:

- Nexor Dark;
- Nexor Light;
- SISBolt.

Verificar:

- seleção;
- hover;
- foco;
- desabilitado;
- erro;
- sucesso;
- tabelas;
- modais;
- empty states.

---

# 91. Atualização de documentação

Mudanças estruturais em MVVM devem atualizar:

- este documento;
- `docs/architecture.md`;
- `docs/Project_Structure.md`;
- `docs/Coding_Standards.md`;
- `docs/UI_UX_Specification.md`, quando visual.

---

# 92. Checklist para nova ViewModel

- [ ] Responsabilidade única.
- [ ] Dependências necessárias.
- [ ] Sem SQL.
- [ ] Sem acesso direto a arquivos.
- [ ] Sem regra central duplicada.
- [ ] Commands nomeados claramente.
- [ ] Loading tratado.
- [ ] Erros tratados.
- [ ] CancellationToken avaliado.
- [ ] Testes adicionados.
- [ ] Navegação registrada.
- [ ] Ciclo de vida definido.

---

# 93. Checklist para nova View

- [ ] DataContext correto.
- [ ] Bindings válidos.
- [ ] Sem regra de negócio.
- [ ] Recursos dos temas.
- [ ] Empty state.
- [ ] Loading.
- [ ] Erro.
- [ ] Foco.
- [ ] Navegação por teclado.
- [ ] Teste nos três temas.
- [ ] Escala do Windows validada.

---

# 94. Checklist de navegação

- [ ] Tela inicial correta.
- [ ] Sidebar atualizada.
- [ ] Título atualizado.
- [ ] ViewModel correta.
- [ ] Estado preservado conforme decisão.
- [ ] Inicialização executada.
- [ ] Operação anterior cancelada quando necessário.
- [ ] Sem múltiplas instâncias acidentais.

---

# 95. Estado atual

Implementado ou parcialmente implementado:

- shell WPF;
- sidebar;
- topbar;
- barra de status;
- navegação;
- ViewModels iniciais;
- temas;
- persistência de tema;
- telas Home, Operação, Rolos, Configurações e Sobre.

Ainda deve ser validado contra o código real:

- serviço de navegação;
- implementação de commands;
- injeção de dependência;
- serviço de diálogo;
- serviço de tema;
- seleção operacional;
- ciclo de vida das ViewModels;
- tratamento assíncrono;
- cancelamento;
- testes de ViewModels.

---

# 96. Regra final

No Nexor, o MVVM deve seguir esta divisão:

```text
A View mostra.
A ViewModel organiza o estado.
A Application executa o caso de uso.
O Domain aplica as regras.
A Infrastructure acessa recursos externos.
O Reporting gera os documentos.
```

A ViewModel não deve se tornar uma nova camada de negócio.

Seu papel é conectar a interface aos casos de uso de forma clara, testável e previsível.