# Nexor — Guia do Banco de Dados

## 1. Objetivo

Este documento descreve a estratégia oficial de persistência do **Nexor**, incluindo:

- localização do banco;
- criação inicial;
- estrutura do schema;
- versionamento;
- migrations;
- repositórios;
- transações;
- integridade;
- backup;
- restauração;
- testes;
- diagnóstico;
- evolução futura.

O Nexor utiliza **SQLite** como banco de dados local.

A persistência deve sustentar o fluxo operacional:

```text
Importar registros
        ↓
Interpretar e persistir
        ↓
Montar o rolo
        ↓
Fechar em transação
        ↓
Registrar eventos
        ↓
Exportar
        ↓
Consultar
        ↓
Reexportar
```

Este documento deve permanecer alinhado com:

- `docs/architecture.md`;
- `docs/Data_Model.md`;
- `docs/Functional_Spec_Operational_Core.md`;
- `docs/installation.md`;
- `docs/Development_Guide.md`.

---

# 2. Tecnologia

O banco oficial do Nexor utiliza:

```text
SQLite
```

O SQLite foi escolhido porque oferece:

- funcionamento local;
- ausência de servidor;
- instalação simples;
- arquivo único;
- boa confiabilidade transacional;
- desempenho adequado ao escopo inicial;
- backup simplificado;
- compatibilidade com aplicações desktop.

---

# 3. Estratégia local-first

O banco local é a fonte principal de verdade do Nexor.

O fluxo operacional não deve depender de:

- servidor remoto;
- internet;
- API externa;
- banco compartilhado obrigatório;
- autenticação online.

Recursos futuros de sincronização devem trabalhar sobre os dados locais sem substituir a confiabilidade do núcleo.

---

# 4. Localização do banco

O banco deve ser armazenado em:

```text
%LOCALAPPDATA%\Nexor\nexor.db
```

Exemplo:

```text
C:\Users\NOME_DO_USUARIO\AppData\Local\Nexor\nexor.db
```

## Não armazenar em

- `Program Files`;
- pasta de instalação;
- pasta do executável;
- repositório Git;
- pasta `src`;
- pasta `dist`;
- diretório do Projeto Jocasta;
- compartilhamento de rede instável;
- pasta sincronizada sem validação.

---

# 5. Estrutura de dados locais

Estrutura prevista:

```text
%LOCALAPPDATA%\Nexor\
├── nexor.db
├── config.json
├── logs/
├── exports/
├── backups/
├── temp/
└── trial/
```

## Responsabilidades

### `nexor.db`

Contém os dados operacionais.

### `config.json`

Contém preferências locais quando não forem armazenadas no SQLite.

### `logs/`

Contém logs técnicos.

### `exports/`

Contém relatórios e imagens geradas, quando utilizada como pasta padrão.

### `backups/`

Contém cópias de segurança do banco.

### `temp/`

Contém arquivos temporários.

### `trial/`

Contém informações locais da edição Trial, isoladas do domínio operacional.

---

# 6. Criação inicial

Na primeira execução, o Nexor deve:

1. identificar a pasta local;
2. criar o diretório quando ausente;
3. verificar se o banco existe;
4. criar o banco quando necessário;
5. aplicar o schema inicial;
6. registrar a versão do schema;
7. inserir dados padrão quando necessário;
8. validar a estrutura;
9. iniciar a aplicação.

A criação do banco deve ser automática.

O usuário não deve precisar executar scripts SQL manualmente.

---

# 7. Inicialização segura

A inicialização deve distinguir:

## Banco inexistente

Criar banco e schema inicial.

## Banco existente e atualizado

Abrir normalmente.

## Banco existente e desatualizado

Executar migrations pendentes.

## Banco de versão futura

Bloquear a abertura com mensagem clara.

Exemplo:

```text
Este banco foi utilizado por uma versão mais recente do Nexor.
Atualize o aplicativo antes de continuar.
```

## Banco corrompido ou inacessível

Não criar silenciosamente outro banco vazio no lugar.

O sistema deve:

- registrar o erro;
- informar o usuário;
- preservar o arquivo existente;
- orientar recuperação.

---

# 8. Versão do schema

O schema deve possuir versão explícita.

Estrutura sugerida:

```text
SchemaVersions
```

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `Version` | INTEGER | Número da migration |
| `AppliedAt` | TEXT | Data ISO 8601 |
| `Description` | TEXT | Resumo |
| `AppVersion` | TEXT | Versão do Nexor |

Exemplo:

```text
1 — Schema inicial
2 — Registros de exportação
3 — Eventos do rolo
```

---

# 9. Migrations

## 9.1 Objetivo

Migrations controlam mudanças na estrutura do banco.

Cada alteração deve ser:

- explícita;
- numerada;
- ordenada;
- testável;
- executada uma única vez;
- registrada;
- segura para dados existentes.

---

## 9.2 Estrutura sugerida

```text
Nexor.Infrastructure/
└── Migrations/
    ├── Migration001InitialSchema.cs
    ├── Migration002AddExportRecords.cs
    └── Migration003AddRollEvents.cs
```

Outra organização pode ser utilizada desde que mantenha os mesmos princípios.

---

## 9.3 Contrato sugerido

```csharp
public interface IDatabaseMigration
{
    int Version { get; }

    string Description { get; }

    Task ApplyAsync(
        DbConnection connection,
        DbTransaction transaction,
        CancellationToken cancellationToken);
}
```

---

## 9.4 Ordem

As migrations devem ser executadas em ordem crescente.

Exemplo:

```text
Banco atual: 1
Migrations disponíveis: 1, 2, 3

Executar:
2
3
```

Uma migration já aplicada não deve ser repetida.

---

## 9.5 Transação

Cada migration deve ser executada dentro de transação quando o SQLite e a operação permitirem.

```text
BEGIN
    aplicar alterações
    registrar versão
COMMIT
```

Em caso de erro:

```text
ROLLBACK
```

---

## 9.6 Falhas

Quando uma migration falhar:

- interromper a inicialização;
- não registrar a migration como aplicada;
- realizar rollback;
- preservar o banco;
- registrar detalhes;
- orientar restauração.

Não continuar a aplicação com schema parcialmente atualizado.

---

# 10. Backup antes de migrations

Antes de migrations potencialmente destrutivas, criar backup.

Exemplo:

```text
%LOCALAPPDATA%\Nexor\backups\
nexor-before-schema-003-20260716-183500.db
```

## Uma migration é potencialmente destrutiva quando

- remove coluna;
- remove tabela;
- altera sem compatibilidade;
- transforma dados;
- muda identificadores;
- recria tabela;
- altera relacionamentos;
- apaga registros;
- modifica valores históricos.

---

# 11. Tabelas principais

O núcleo operacional deve utilizar tabelas equivalentes a:

```text
ImportedLogs
PrintItems
Machines
Fabrics
FabricAliases
Rolls
RollItems
RollEvents
ExportRecords
AppSettings
SchemaVersions
```

A estrutura real deve ser documentada em `Data_Model.md`.

---

# 12. `ImportedLogs`

## Finalidade

Preservar a origem dos arquivos importados.

Campos principais sugeridos:

```text
Id
SourcePath
SourceName
Fingerprint
RawContent
FileSizeBytes
SourceCreatedAt
ImportedAt
Status
ParseError
MachineCodeRaw
PrintItemId
CreatedAt
UpdatedAt
```

## Restrições

```text
Fingerprint UNIQUE
```

O caminho não deve ser usado como único identificador de duplicidade.

---

# 13. `PrintItems`

## Finalidade

Armazenar o registro operacional interpretado.

Campos principais:

```text
Id
ImportedLogId
DocumentName
NormalizedName
PrintedAt
MachineId
MachineCodeRaw
FabricId
FabricNameRaw
HeightMm
VPositionMm
PrintedLengthM
Status
ReviewNote
RollId
CreatedAt
UpdatedAt
```

## Regra crítica

```text
PrintedLengthM = HeightMm / 1000
```

`VPositionMm` não deve ser somado à metragem.

---

# 14. `Machines`

## Finalidade

Armazenar as máquinas disponíveis.

Campos:

```text
Id
Code
Name
Active
Notes
CreatedAt
UpdatedAt
```

Valores iniciais esperados:

```text
M1
M2
```

Os registros padrão não devem ser duplicados a cada inicialização.

---

# 15. `Fabrics`

## Finalidade

Armazenar tecidos normalizados.

Campos:

```text
Id
Name
NormalizedName
Active
Notes
CreatedAt
UpdatedAt
```

## Restrições

```text
NormalizedName UNIQUE
```

Tecidos históricos devem ser desativados, não apagados, quando já tiverem vínculos.

---

# 16. `FabricAliases`

## Finalidade

Associar variações de nome a um tecido oficial.

Campos:

```text
Id
FabricId
Alias
NormalizedAlias
Active
CreatedAt
UpdatedAt
```

## Restrição

```text
NormalizedAlias UNIQUE
```

Um alias ativo deve apontar para apenas um tecido.

---

# 17. `Rolls`

## Finalidade

Representar rolos operacionais.

Campos principais:

```text
Id
Code
MachineId
Status
OpenedAt
ClosedAt
TotalItems
TotalPrintedLengthM
Notes
CreatedAt
UpdatedAt
ReviewedAt
ReopenedAt
```

## Restrições

```text
Code UNIQUE
TotalItems >= 0
TotalPrintedLengthM >= 0
```

---

# 18. `RollItems`

## Finalidade

Preservar a composição do rolo.

Campos:

```text
Id
RollId
PrintItemId
Sequence
BlockSequence
FabricNameSnapshot
DocumentNameSnapshot
PrintedAtSnapshot
PrintedLengthMSnapshot
CreatedAt
```

## Restrições

```text
UNIQUE RollId + PrintItemId
UNIQUE RollId + Sequence
```

Os snapshots preservam a composição histórica.

---

# 19. `RollEvents`

## Finalidade

Registrar o ciclo de vida do rolo.

Campos:

```text
Id
RollId
EventType
OccurredAt
Summary
PayloadJson
CreatedBy
AppVersion
```

Eventos possíveis:

```text
Created
Closed
ExportedPdf
ExportedMirror
ReexportedPdf
ReexportedMirror
Reviewed
Reopened
Corrected
```

---

# 20. `ExportRecords`

## Finalidade

Registrar cada arquivo gerado.

Campos:

```text
Id
RollId
Type
Mode
FilePath
FileName
FileSizeBytes
CreatedAt
AppVersion
IsReexport
WidthCm
Dpi
```

Uma reexportação deve gerar novo registro.

Exportações antigas não devem ser sobrescritas silenciosamente.

---

# 21. `AppSettings`

## Finalidade

Armazenar configurações simples por chave.

Campos:

```text
Key
Value
UpdatedAt
```

Exemplos:

```text
Theme
DefaultMachine
SearchResultLimit
PdfExportFolder
MirrorExportFolder
MirrorDpi
```

Configurações complexas podem permanecer em JSON quando isso for mais apropriado.

A estratégia não deve ser duplicada sem necessidade entre banco e arquivo.

---

# 22. Identificadores

O projeto deve adotar um padrão consistente.

Opções:

- `INTEGER PRIMARY KEY`;
- `Guid` armazenado como texto ou blob.

A decisão deve considerar:

- simplicidade;
- desempenho;
- sincronização futura;
- legibilidade;
- migração;
- tamanho do banco.

## Recomendação inicial

Para uma aplicação local SQLite:

```text
INTEGER PRIMARY KEY
```

é suficiente e simples.

Caso a sincronização multiestação se torne requisito real, identificadores globais podem ser adicionados de forma planejada.

Não misturar estratégias sem justificativa.

---

# 23. Tipos SQLite

Mapeamento recomendado:

| C# | SQLite |
|---|---|
| `long` | `INTEGER` |
| `int` | `INTEGER` |
| `bool` | `INTEGER` |
| `decimal` | `TEXT`, `REAL` controlado ou inteiro escalado |
| `string` | `TEXT` |
| `DateTimeOffset` | `TEXT` ISO 8601 |
| `byte[]` | `BLOB` |

---

# 24. Persistência de `decimal`

O SQLite não possui um tipo decimal nativo com as mesmas garantias do C#.

A estratégia deve ser explícita.

## Opção A — Texto com formato invariável

Exemplo:

```text
6.361
```

Vantagens:

- preserva precisão;
- conversão controlada.

Desvantagens:

- consultas matemáticas mais difíceis.

## Opção B — Inteiro escalado

Armazenar em milímetros:

```text
6361
```

Vantagens:

- precisão;
- somas simples;
- sem erro de ponto flutuante.

Desvantagens:

- exige conversão.

## Recomendação para metragem

Preservar:

```text
HeightMm como INTEGER ou decimal controlado
```

e calcular metros no domínio.

Totais históricos podem ser armazenados em milímetros ou em representação decimal invariável.

A estratégia definitiva deve ser única em todas as tabelas.

---

# 25. Datas e horários

Persistir em ISO 8601.

Exemplo:

```text
2026-07-16T18:35:42-03:00
```

Utilizar `DateTimeOffset` no C#.

Não persistir como formato visual:

```text
16/07/2026 18:35
```

Esse formato pertence à apresentação.

---

# 26. Booleans

Persistir como:

```text
0 = false
1 = true
```

Usar constraints quando apropriado:

```sql
CHECK (Active IN (0, 1))
```

---

# 27. Enums

Enums podem ser armazenados como:

- texto;
- inteiro.

## Texto

Exemplo:

```text
Closed
Exported
```

Vantagens:

- legibilidade;
- diagnóstico;
- menor risco ao reordenar enum.

## Inteiro

Vantagens:

- menor tamanho;
- consulta rápida.

Desvantagens:

- menos legível;
- exige estabilidade numérica.

## Recomendação

Para estados operacionais:

```text
TEXT
```

é mais seguro durante a fase inicial.

---

# 28. Chaves estrangeiras

Ativar chaves estrangeiras em cada conexão:

```sql
PRAGMA foreign_keys = ON;
```

Não assumir que estarão sempre ativas automaticamente.

Relacionamentos devem proteger:

- rolo e itens;
- log e item;
- tecido e alias;
- rolo e eventos;
- rolo e exportações.

---

# 29. Regras de exclusão

Usar `ON DELETE` de forma consciente.

## Histórico

Para dados históricos, evitar cascata destrutiva.

Exemplo:

```text
Roll
RollItem
RollEvent
ExportRecord
```

não devem desaparecer por uma exclusão acidental.

## Cadastros

Máquinas e tecidos vinculados devem ser desativados, não apagados.

## Configurações

Podem ser substituídas ou removidas quando não afetarem histórico.

---

# 30. Índices

Índices recomendados:

## `ImportedLogs`

```sql
UNIQUE INDEX Fingerprint
INDEX ImportedAt
INDEX Status
```

## `PrintItems`

```sql
INDEX PrintedAt
INDEX MachineId
INDEX FabricId
INDEX Status
INDEX RollId
INDEX NormalizedName
```

## `Rolls`

```sql
UNIQUE INDEX Code
INDEX ClosedAt
INDEX MachineId
INDEX Status
```

## `RollItems`

```sql
UNIQUE INDEX RollId, PrintItemId
UNIQUE INDEX RollId, Sequence
INDEX PrintItemId
```

## `RollEvents`

```sql
INDEX RollId
INDEX OccurredAt
INDEX EventType
```

## `ExportRecords`

```sql
INDEX RollId
INDEX CreatedAt
INDEX Type
```

## `FabricAliases`

```sql
UNIQUE INDEX NormalizedAlias
INDEX FabricId
```

---

# 31. Consultas principais

O banco deve suportar eficientemente:

- localizar fingerprint;
- listar itens disponíveis;
- ordenar por `PrintedAt`;
- filtrar por máquina;
- filtrar por tecido;
- buscar texto no documento;
- listar rolos por período;
- buscar rolo por código;
- buscar rolos contendo determinado pedido;
- carregar detalhes;
- carregar eventos;
- carregar exportações.

---

# 32. Busca textual

A busca inicial pode utilizar:

```sql
LIKE
```

com valor normalizado.

Exemplo:

```sql
WHERE NormalizedName LIKE '%' || @SearchText || '%'
```

Para volumes maiores, avaliar:

- FTS5;
- colunas auxiliares;
- índices específicos.

Não adicionar FTS antes de medir necessidade real.

---

# 33. Repositórios

Repositórios devem abstrair o SQL.

Exemplos:

```text
ImportedLogRepository
PrintItemRepository
RollRepository
RollEventRepository
ExportRecordRepository
SettingsRepository
```

## Regras

- usar parâmetros;
- não concatenar entradas;
- não expor conexão à UI;
- não retornar tipos da biblioteca de banco;
- mapear para modelos internos;
- aceitar `CancellationToken`;
- não conter regras visuais.

---

# 34. Contratos

Exemplo:

```csharp
public interface IRollRepository
{
    Task<Roll?> FindByIdAsync(
        long id,
        CancellationToken cancellationToken);

    Task<Roll?> FindByCodeAsync(
        string code,
        CancellationToken cancellationToken);

    Task<IReadOnlyList<RollSummary>> SearchAsync(
        RollSearchFilter filter,
        CancellationToken cancellationToken);

    Task AddAsync(
        Roll roll,
        CancellationToken cancellationToken);
}
```

Os contratos devem refletir casos de uso reais.

Evite criar um repositório genérico com operações que não fazem sentido para todas as entidades.

---

# 35. Acesso ao banco

O acesso pode utilizar:

- `Microsoft.Data.Sqlite`;
- Dapper;
- EF Core;
- outra biblioteca aprovada.

A escolha deve ser documentada.

## Critérios

- compatibilidade com .NET 8;
- suporte SQLite;
- migrations;
- controle de SQL;
- tamanho da aplicação;
- publicação one-file;
- manutenção;
- testes.

Não misturar múltiplas estratégias de acesso sem necessidade.

---

# 36. Conexões

As conexões devem ser abertas pelo menor tempo necessário.

Fluxo recomendado:

```text
abrir
→ executar operação
→ confirmar transação
→ fechar
```

Não manter uma única conexão global aberta indefinidamente sem justificativa.

---

# 37. Connection string

Exemplo:

```text
Data Source=C:\Users\...\AppData\Local\Nexor\nexor.db;
Foreign Keys=True;
```

O caminho deve ser criado por um serviço.

Não usar caminho absoluto de desenvolvimento.

---

# 38. Journaling

O SQLite pode utilizar:

```sql
PRAGMA journal_mode = WAL;
```

O modo WAL pode melhorar:

- concorrência de leitura;
- confiabilidade;
- responsividade.

Antes de adotar, validar:

- criação dos arquivos auxiliares;
- backup;
- instalador;
- antivírus;
- comportamento em encerramento inesperado.

---

# 39. Busy timeout

Configurar tempo de espera para bloqueios curtos:

```sql
PRAGMA busy_timeout = 5000;
```

O valor deve ser ajustado conforme testes.

O sistema não deve travar indefinidamente quando o banco estiver bloqueado.

---

# 40. Transação de importação

Uma importação em lote pode usar transação.

Fluxo:

```text
BEGIN
    verificar fingerprints
    inserir logs novos
    inserir itens válidos
    registrar estados
COMMIT
```

## Falha por arquivo

Dependendo da estratégia, arquivos inválidos podem ser registrados dentro do mesmo lote.

Um erro de parsing esperado não deve necessariamente cancelar todos os outros arquivos.

## Falha técnica

Falhas de banco devem cancelar a transação afetada.

---

# 41. Transação de fechamento

O fechamento do rolo deve ser atômico.

```text
BEGIN

1. validar itens;
2. criar Roll;
3. inserir RollItems;
4. atualizar PrintItems;
5. registrar RollEvent;
6. persistir totais;
7. definir ClosedAt;

COMMIT
```

Em caso de falha:

```text
ROLLBACK
```

Não pode existir:

- rolo sem itens;
- itens vinculados sem rolo;
- fechamento sem evento;
- metade da composição salva.

---

# 42. Concorrência de fechamento

Antes de fechar, o sistema deve confirmar novamente que os itens:

- continuam disponíveis;
- não foram vinculados;
- pertencem à máquina esperada;
- não foram alterados.

A validação não deve depender apenas do estado carregado anteriormente na interface.

---

# 43. Transação de exportação

A geração do arquivo ocorre fora do banco.

Fluxo recomendado:

1. recuperar rolo;
2. gerar arquivo;
3. validar que o arquivo existe;
4. abrir transação;
5. inserir `ExportRecord`;
6. inserir `RollEvent`;
7. atualizar status quando aplicável;
8. confirmar.

Se a geração falhar:

- não registrar exportação concluída;
- manter o rolo fechado;
- registrar erro técnico.

---

# 44. Reexportação

Cada reexportação deve:

- criar novo arquivo;
- criar novo `ExportRecord`;
- marcar `IsReexport`;
- registrar evento;
- preservar registros anteriores.

Não atualizar apenas o caminho da exportação original.

---

# 45. Integridade

O banco deve aplicar integridade em três níveis.

## Domínio

Validações e invariantes.

## Aplicação

Coordenação do fluxo e transações.

## Banco

Constraints, índices únicos e chaves estrangeiras.

Nenhuma camada isolada deve ser a única defesa.

---

# 46. Constraints

Exemplos:

```sql
CHECK (HeightMm > 0)
CHECK (PrintedLengthM >= 0)
CHECK (TotalItems >= 0)
CHECK (TotalPrintedLengthM >= 0)
CHECK (Sequence > 0)
CHECK (BlockSequence > 0)
```

O uso depende da estratégia de armazenamento adotada.

---

# 47. Duplicidade

A duplicidade principal deve ser controlada por:

```text
Fingerprint UNIQUE
```

Fluxo:

1. calcular SHA-256;
2. consultar;
3. se existir, retornar duplicado;
4. se não existir, persistir.

Também deve existir índice único no banco para proteger contra condição de corrida.

---

# 48. Histórico imutável

Após fechamento, os dados históricos devem permanecer estáveis.

Por isso, `RollItems` pode conter snapshots de:

- documento;
- tecido;
- horário;
- metragem;
- ordem;
- bloco.

Uma alteração futura no cadastro não deve reescrever o passado.

---

# 49. Soft delete

Quando necessário, utilizar:

```text
Active
Status
DeletedAt
```

em vez de exclusão física.

Adequado para:

- máquinas;
- tecidos;
- aliases;
- configurações históricas.

Não adicionar soft delete automaticamente a todas as tabelas.

---

# 50. Auditoria

O banco deve permitir responder:

- qual arquivo originou o item;
- quando foi importado;
- por qual versão;
- por que foi inválido;
- em qual rolo entrou;
- qual posição ocupou;
- quando o rolo foi fechado;
- quais arquivos foram exportados;
- quando ocorreu reexportação.

---

# 51. Versão da aplicação

Eventos e exportações devem registrar, quando útil:

```text
AppVersion
```

Isso facilita investigar diferenças entre versões.

---

# 52. Logs de erro

Erros técnicos de banco devem ser registrados no sistema de logs.

Exemplos:

- falha de conexão;
- migration;
- constraint;
- timeout;
- banco bloqueado;
- corrupção;
- rollback.

Não registrar dados sensíveis completos sem necessidade.

---

# 53. Backup manual

Para backup manual:

1. fechar o Nexor;
2. copiar:

```text
%LOCALAPPDATA%\Nexor\nexor.db
```

3. salvar em local seguro;
4. registrar a versão do aplicativo.

Quando WAL estiver ativo, garantir checkpoint ou usar mecanismo de backup apropriado.

Não copiar apenas o `.db` enquanto houver escrita ativa sem validar consistência.

---

# 54. Backup automático

Estrutura sugerida:

```text
%LOCALAPPDATA%\Nexor\backups\
```

Nomes:

```text
nexor-20260716-183500.db
nexor-before-schema-003.db
nexor-before-update-0.3.0.db
```

Backup automático pode ocorrer:

- antes de migration;
- antes de restauração;
- antes de operação administrativa destrutiva;
- em intervalo configurável futuro.

---

# 55. Retenção

Uma política futura poderá manter:

- últimos 10 backups;
- backups dos últimos 30 dias;
- backups de migrations;
- backups manuais preservados.

Não apagar backups sem política explícita.

---

# 56. Restauração

Procedimento manual:

1. fechar o Nexor;
2. preservar o banco atual;
3. copiar o backup;
4. confirmar nome esperado;
5. abrir o aplicativo;
6. validar schema;
7. verificar logs;
8. conferir registros.

Não restaurar banco de versão futura em aplicativo antigo.

---

# 57. Banco incompatível

Quando o banco possuir schema mais recente que o aplicativo:

- bloquear escrita;
- não tentar downgrade automático;
- informar versão necessária;
- preservar arquivo;
- registrar diagnóstico.

---

# 58. Banco corrompido

Sinais:

- erro ao abrir;
- páginas inválidas;
- falha de integridade;
- consultas inconsistentes.

Ações:

1. fechar aplicação;
2. criar cópia do arquivo;
3. executar diagnóstico;
4. verificar backups;
5. restaurar quando necessário;
6. não sobrescrever o original.

---

# 59. Verificação de integridade

Comando SQLite:

```sql
PRAGMA integrity_check;
```

Resultado esperado:

```text
ok
```

Também pode ser utilizado:

```sql
PRAGMA foreign_key_check;
```

Essas verificações podem integrar uma ferramenta de diagnóstico futura.

---

# 60. Ferramentas externas

Ferramentas como DB Browser for SQLite podem ser utilizadas para diagnóstico.

Cuidados:

- fechar a aplicação;
- trabalhar em cópia;
- não editar banco real sem backup;
- não alterar versão do schema manualmente;
- não apagar registros vinculados.

---

# 61. Testes de banco

Os testes devem utilizar banco temporário.

Exemplo:

```text
%TEMP%\Nexor.Tests\<guid>\nexor-test.db
```

Cada teste ou conjunto deve ter isolamento.

Não utilizar o banco real do usuário.

---

# 62. Testes de criação

Cobrir:

- diretório inexistente;
- banco inexistente;
- criação do schema;
- inserção de dados iniciais;
- versão do schema;
- reinicialização sem duplicar registros.

---

# 63. Testes de migration

Cobrir:

- banco na versão anterior;
- aplicação da próxima migration;
- dados preservados;
- versão atualizada;
- repetição não executada;
- falha com rollback;
- banco de versão futura.

---

# 64. Testes de repositórios

Cobrir:

- inserção;
- leitura;
- atualização;
- busca;
- filtros;
- duplicidade;
- índices únicos;
- relacionamentos;
- cancelamento.

---

# 65. Teste de fechamento

Cenário:

```text
itens disponíveis
→ fechar rolo
→ recuperar rolo
→ recuperar itens
→ recuperar evento
```

Confirmar:

- totais;
- ordem;
- blocos;
- vínculos;
- status;
- data;
- snapshots.

---

# 66. Teste de rollback

Simular falha após inserir o rolo e antes de vincular todos os itens.

Resultado esperado:

- nenhum rolo parcial;
- nenhum item vinculado;
- nenhum evento falso.

---

# 67. Teste de duplicidade

Importar o mesmo conteúdo por caminhos diferentes.

Resultado esperado:

```text
primeira importação: novo
segunda importação: duplicado
```

---

# 68. Teste de consulta

Criar múltiplos rolos e verificar filtros por:

- máquina;
- período;
- código;
- documento;
- tecido;
- status;
- limite.

---

# 69. Desempenho

O banco inicial deve suportar com fluidez:

- milhares de logs;
- milhares de itens;
- centenas ou milhares de rolos;
- eventos;
- exportações.

Antes de otimizar:

- medir;
- analisar consulta;
- conferir índices;
- evitar carregar tudo;
- utilizar limite.

---

# 70. Paginação e limite

A consulta histórica deve possuir limite inicial.

Valor sugerido:

```text
300
```

Para volumes maiores, implementar paginação ou carregamento incremental.

Não carregar indefinidamente todos os registros na UI.

---

# 71. Consultas N+1

Evitar consultas individuais para cada linha exibida.

Exemplo inadequado:

```text
listar 300 rolos
→ executar outra consulta para cada rolo
```

Preferir consultas agregadas ou carregamento sob demanda do detalhe.

---

# 72. Dados grandes

Não carregar `RawContent` em listagens quando ele não for necessário.

Utilizar consultas específicas:

- resumo;
- detalhes;
- conteúdo bruto.

Isso reduz memória e tráfego interno.

---

# 73. Vacuum

O SQLite oferece:

```sql
VACUUM;
```

Essa operação pode reduzir o arquivo após grandes remoções.

Não executar automaticamente com frequência.

Ela pode:

- bloquear;
- consumir tempo;
- exigir espaço adicional.

Deve ser uma ação de manutenção controlada.

---

# 74. Analyze

Após alterações relevantes de volume ou índices, pode ser utilizado:

```sql
ANALYZE;
```

Somente quando houver benefício medido.

---

# 75. Projeto Jocasta

O banco do Projeto Jocasta:

- não deve ser alterado;
- não deve ser usado como banco principal;
- não deve receber migrations do Nexor;
- não deve ser aberto em modo de escrita pelo Nexor sem fluxo explícito.

---

# 76. Migração futura do Jocasta

Caso seja criada:

1. selecionar fonte;
2. abrir em modo leitura;
3. validar versão;
4. mapear registros;
5. importar para banco Nexor;
6. gerar relatório;
7. preservar origem;
8. não alterar banco original.

Esse fluxo deve ficar isolado em ferramenta ou serviço específico.

---

# 77. Trial

Dados da Trial não devem ficar misturados com:

- rolos;
- registros;
- eventos;
- exportações.

Preferir armazenamento isolado:

```text
%LOCALAPPDATA%\Nexor\trial\
```

A edição oficial não deve consultar estado da Trial para decidir acesso ao domínio operacional.

---

# 78. Segurança

O banco local não deve conter:

- tokens em texto simples;
- chaves privadas;
- senhas;
- segredos de build;
- credenciais de serviços.

Caso dados sensíveis futuros precisem ser armazenados, utilizar proteção apropriada do Windows.

---

# 79. Dados pessoais e operacionais

O banco poderá conter:

- nomes de pedidos;
- caminhos;
- registros de produção;
- operadores futuramente.

A aplicação deve:

- evitar exposição desnecessária;
- não enviar dados externamente sem autorização;
- orientar backup seguro;
- limitar logs de conteúdo.

---

# 80. Alterações no schema

Toda alteração deve incluir:

- migration;
- teste;
- atualização deste documento;
- atualização de `Data_Model.md`;
- nota no `CHANGELOG.md`, quando relevante;
- avaliação de backup;
- validação com banco anterior.

---

# 81. Checklist para migration

- [ ] Número definido.
- [ ] Descrição definida.
- [ ] Ordem correta.
- [ ] SQL parametrizado quando aplicável.
- [ ] Transação.
- [ ] Rollback testado.
- [ ] Dados preservados.
- [ ] Banco vazio testado.
- [ ] Banco anterior testado.
- [ ] Versão futura tratada.
- [ ] Documentação atualizada.
- [ ] Backup avaliado.

---

# 82. Checklist de persistência

- [ ] Chaves estrangeiras ativadas.
- [ ] Índices necessários criados.
- [ ] Constraints configuradas.
- [ ] Datas em ISO 8601.
- [ ] Decimais tratados consistentemente.
- [ ] Enums persistidos de forma estável.
- [ ] SQL parametrizado.
- [ ] CancellationToken propagado.
- [ ] Conexões fechadas corretamente.
- [ ] Transações críticas implementadas.

---

# 83. Checklist de release

Antes de publicar uma versão:

- [ ] Schema definido.
- [ ] Migrations testadas.
- [ ] Banco novo testado.
- [ ] Atualização testada.
- [ ] Backup testado.
- [ ] Dados preservados.
- [ ] Instalação limpa testada.
- [ ] Banco de versão futura tratado.
- [ ] `Data_Model.md` atualizado.
- [ ] `CHANGELOG.md` atualizado.

---

# 84. Decisões pendentes

Ainda devem ser confirmados contra a implementação real:

- biblioteca oficial de acesso ao SQLite;
- uso de Dapper, EF Core ou acesso direto;
- tipo definitivo dos identificadores;
- forma de persistir decimais;
- estratégia de WAL;
- política de backup;
- retenção;
- armazenamento integral do conteúdo bruto;
- estrutura definitiva de migrations;
- eventual criptografia;
- mecanismo de diagnóstico.

Não documentar uma decisão pendente como se já estivesse implementada.

---

# 85. Estado atual

Implementado ou parcialmente implementado:

- SQLite;
- criação automática;
- versão explícita de schema;
- repositórios iniciais;
- persistência de logs e rolos;
- testes iniciais;
- fingerprint SHA-256.

Ainda precisa ser conferido e documentado conforme o código real:

- nomes definitivos das tabelas;
- colunas;
- índices;
- constraints;
- migrations disponíveis;
- estratégia de transação;
- registros de exportação;
- eventos completos;
- backups;
- WAL;
- tratamento de corrupção.

---

# 86. Regra final

O banco do Nexor deve preservar a história da produção.

```text
O log preserva a origem.
O item preserva a impressão.
O rolo preserva a composição.
O evento preserva o acontecimento.
A exportação preserva o arquivo gerado.
A migration preserva a evolução.
O backup preserva a recuperação.
```

Nenhuma atualização, fechamento ou exportação deve deixar o banco em estado parcial ou contraditório.