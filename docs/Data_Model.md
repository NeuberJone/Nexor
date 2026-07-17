# Nexor — Modelo de Dados

## 1. Objetivo

Este documento define o modelo de dados oficial do **Nexor** para o núcleo operacional da aplicação.

O modelo deve sustentar o fluxo:

```text
Importar registros
        ↓
Interpretar e normalizar
        ↓
Evitar duplicidades
        ↓
Montar um rolo
        ↓
Fechar e persistir
        ↓
Exportar
        ↓
Consultar e reexportar
```

A implementação oficial utiliza:

- C#;
- .NET 8;
- WPF;
- SQLite;
- arquitetura local-first.

Este documento descreve:

- entidades;
- relacionamentos;
- estados;
- regras de integridade;
- persistência;
- auditoria;
- evolução do schema.

---

# 2. Escopo atual

## Incluído

O modelo atual deve suportar:

- importação de arquivos de log;
- preservação da origem;
- interpretação de registros;
- prevenção de duplicidade;
- identificação de máquina;
- identificação de tecido;
- metragem impressa;
- montagem de rolos;
- fechamento de rolos;
- vínculo dos itens com o rolo;
- eventos operacionais;
- exportação;
- consulta histórica;
- reexportação;
- configurações locais.

## Fora do escopo atual

Ainda não devem influenciar o modelo central:

- planejamento avançado;
- estoque;
- analytics avançado;
- sincronização remota;
- multiestação;
- reserva de material;
- integração com sistemas externos;
- controle comercial completo de licenças.

Essas áreas devem ser incorporadas futuramente sem distorcer o núcleo operacional atual.

---

# 3. Vocabulário oficial

Os seguintes termos devem ser utilizados de forma consistente no código, banco e documentação.

## Log importado

Arquivo bruto recebido pelo Nexor.

Representa a origem da informação antes da normalização.

Nome sugerido no código:

```text
ImportedLog
```

---

## Item de impressão

Registro operacional interpretado a partir de um log válido.

Contém informações como:

- nome do documento;
- horário;
- tecido;
- máquina;
- altura impressa;
- deslocamento;
- metragem real.

Nome sugerido no código:

```text
PrintItem
```

O termo técnico `Job` pode aparecer apenas quando necessário internamente, mas deve ser evitado em textos visíveis ao usuário.

---

## Rolo

Unidade operacional consolidada contendo um ou mais itens de impressão.

Nome sugerido no código:

```text
Roll
```

---

## Item do rolo

Representa o vínculo entre um rolo e um item de impressão.

Nome sugerido:

```text
RollItem
```

---

## Evento do rolo

Representa uma ação relevante ocorrida no ciclo de vida do rolo.

Nome sugerido:

```text
RollEvent
```

---

## Máquina

Equipamento responsável pela impressão.

Nome sugerido:

```text
Machine
```

---

## Tecido

Material normalizado utilizado no registro.

Nome sugerido:

```text
Fabric
```

---

## Alias de tecido

Variação textual associada a um tecido oficial.

Nome sugerido:

```text
FabricAlias
```

---

## Registro de exportação

Representa um arquivo formal gerado para um rolo.

Nome sugerido:

```text
ExportRecord
```

---

## Configuração

Valor persistido relacionado ao comportamento da aplicação.

Nome sugerido:

```text
AppSetting
```

---

# 4. Princípios de modelagem

## 4.1 Fonte bruta preservada

O Nexor deve manter referência suficiente ao arquivo original para auditoria.

Dados inválidos não devem ser simplesmente descartados.

---

## 4.2 Estados explícitos

O estado de cada registro deve ser armazenado.

Não deve ser inferido somente pela tela em que aparece.

---

## 4.3 Fechamento congela composição

Depois que um rolo for fechado:

- sua composição não deve mudar silenciosamente;
- os itens vinculados devem permanecer identificáveis;
- totais históricos devem permanecer consistentes;
- alterações futuras devem ser auditáveis.

---

## 4.4 Exportação baseada no banco

PDF e JPG espelhado devem ser gerados a partir de dados persistidos.

A interface não deve ser utilizada como fonte direta de dados históricos.

---

## 4.5 Duplicidade determinística

Cada arquivo importado deve possuir um fingerprint estável.

A implementação inicial utiliza SHA-256.

---

## 4.6 Evolução controlada

O schema deve evoluir por versões explícitas.

Não devem ocorrer mudanças destrutivas silenciosas.

---

# 5. Visão geral das entidades

```text
ImportedLog
     │
     │ 0..1
     ▼
PrintItem
     │
     │ muitos
     ▼
RollItem
     │
     │ muitos para 1
     ▼
Roll
     │
     ├── RollEvent
     └── ExportRecord
```

Entidades auxiliares:

```text
Machine
Fabric
FabricAlias
AppSetting
SchemaVersion
```

---

# 6. Entidade ImportedLog

## 6.1 Finalidade

Representa o arquivo bruto importado pelo Nexor.

Seu objetivo é preservar:

- origem;
- conteúdo;
- identificação;
- resultado do parsing;
- erros;
- data de importação;
- vínculo com o item normalizado.

---

## 6.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador interno |
| `SourcePath` | `string` | sim | Caminho original do arquivo |
| `SourceName` | `string` | sim | Nome do arquivo |
| `Fingerprint` | `string` | sim | SHA-256 do arquivo |
| `RawContent` | `string` | não | Conteúdo bruto preservado |
| `FileSizeBytes` | `long` | não | Tamanho do arquivo |
| `SourceCreatedAt` | `DateTimeOffset?` | não | Data original do arquivo |
| `ImportedAt` | `DateTimeOffset` | sim | Data de importação |
| `Status` | `ImportedLogStatus` | sim | Estado do log |
| `ParseError` | `string?` | não | Erro de interpretação |
| `MachineCodeRaw` | `string?` | não | Identificação bruta da máquina |
| `PrintItemId` | referência opcional | não | Item gerado a partir do log |
| `CreatedAt` | `DateTimeOffset` | sim | Data de criação no banco |
| `UpdatedAt` | `DateTimeOffset` | sim | Última alteração |

---

## 6.3 Regras

- `Fingerprint` deve ser único.
- `SourcePath` não deve ser usado sozinho como chave de duplicidade.
- Arquivos movidos podem possuir outro caminho, mas o mesmo fingerprint.
- Um log pode gerar no máximo um item de impressão no fluxo atual.
- Um log inválido deve preservar o motivo da falha.
- Um log duplicado não deve gerar novo item.
- O conteúdo bruto só pode ser omitido quando existir outra forma confiável de auditoria.

---

# 7. Entidade PrintItem

## 7.1 Finalidade

Representa um registro de impressão normalizado.

É a unidade operacional usada para:

- cálculo;
- seleção;
- agrupamento;
- montagem de rolo;
- consulta;
- auditoria.

---

## 7.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador interno |
| `ImportedLogId` | referência | sim | Log de origem |
| `DocumentName` | `string` | sim | Nome original do documento |
| `NormalizedName` | `string` | não | Nome tratado para pesquisa |
| `PrintedAt` | `DateTimeOffset` | sim | Horário final da impressão |
| `MachineId` | referência opcional | não | Máquina normalizada |
| `MachineCodeRaw` | `string?` | não | Máquina identificada no arquivo |
| `FabricId` | referência opcional | não | Tecido normalizado |
| `FabricNameRaw` | `string?` | não | Nome bruto extraído |
| `HeightMm` | `decimal` | sim | Altura impressa |
| `VPositionMm` | `decimal` | sim | Deslocamento vertical |
| `PrintedLengthM` | `decimal` | sim | Metragem real |
| `Status` | `PrintItemStatus` | sim | Estado operacional |
| `ReviewNote` | `string?` | não | Observação de revisão |
| `RollId` | referência opcional | não | Rolo associado |
| `CreatedAt` | `DateTimeOffset` | sim | Data de criação |
| `UpdatedAt` | `DateTimeOffset` | sim | Última alteração |

---

## 7.3 Regra de metragem

```text
PrintedLengthM = HeightMm / 1000
```

Exemplo:

```text
HeightMm = 6361
PrintedLengthM = 6,361 m
```

`VPositionMm` representa deslocamento e não deve ser somado à metragem real.

---

## 7.4 Regras

- `HeightMm` deve ser maior que zero.
- `PrintedLengthM` deve ser recalculado pelo domínio.
- O valor persistido deve permanecer coerente com `HeightMm`.
- `DocumentName` deve preservar o texto original.
- `FabricNameRaw` deve ser mantido mesmo quando houver normalização.
- Um item não pode pertencer silenciosamente a mais de um rolo.
- O vínculo com um rolo fechado não deve ser alterado sem processo auditável.
- Um item suspeito pode existir, mas sua inclusão em um rolo pode exigir confirmação.

---

# 8. Entidade Roll

## 8.1 Finalidade

Representa um rolo operacional consolidado.

O rolo é a principal entidade histórica do Nexor.

---

## 8.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador interno |
| `Code` | `string` | sim | Identificação operacional |
| `MachineId` | referência opcional | não | Máquina associada |
| `Status` | `RollStatus` | sim | Estado do rolo |
| `OpenedAt` | `DateTimeOffset` | sim | Data de início |
| `ClosedAt` | `DateTimeOffset?` | não | Data do fechamento |
| `TotalItems` | `int` | sim | Quantidade de itens |
| `TotalPrintedLengthM` | `decimal` | sim | Metragem total |
| `Notes` | `string?` | não | Observações |
| `CreatedAt` | `DateTimeOffset` | sim | Data de criação |
| `UpdatedAt` | `DateTimeOffset` | sim | Última alteração |
| `ReviewedAt` | `DateTimeOffset?` | não | Data de revisão |
| `ReopenedAt` | `DateTimeOffset?` | não | Última reabertura |

---

## 8.3 Código do rolo

O código deve ser:

- legível;
- único;
- seguro para nome de arquivo;
- previsível;
- passível de busca.

Exemplo:

```text
M1_16-07-2026_153045
```

Uma alternativa futura pode usar:

```text
2026-07-16_M1_153045
```

A regra definitiva deve ser centralizada em um serviço próprio.

---

## 8.4 Regras

- um rolo deve conter pelo menos um item;
- o código deve ser único;
- os totais devem ser calculados pelo domínio;
- um rolo fechado deve possuir `ClosedAt`;
- um rolo em rascunho não deve ser exportado como documento final;
- o fechamento deve ocorrer em transação;
- a composição de um rolo fechado deve ficar congelada;
- uma reabertura futura deve gerar evento;
- reexportação não deve alterar a composição;
- relatórios devem utilizar os itens persistidos.

---

# 9. Entidade RollItem

## 9.1 Finalidade

Representa a composição do rolo.

Essa entidade evita depender apenas do campo `RollId` no item de impressão e permite registrar:

- ordem;
- agrupamento;
- dados históricos;
- posição;
- eventuais informações congeladas.

---

## 9.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador |
| `RollId` | referência | sim | Rolo |
| `PrintItemId` | referência | sim | Item de impressão |
| `Sequence` | `int` | sim | Ordem dentro do rolo |
| `BlockSequence` | `int` | sim | Número do bloco |
| `FabricNameSnapshot` | `string?` | não | Tecido no fechamento |
| `DocumentNameSnapshot` | `string` | sim | Documento no fechamento |
| `PrintedAtSnapshot` | `DateTimeOffset` | sim | Horário no fechamento |
| `PrintedLengthMSnapshot` | `decimal` | sim | Metragem congelada |
| `CreatedAt` | `DateTimeOffset` | sim | Data do vínculo |

---

## 9.3 Por que usar snapshots

Dados históricos não devem mudar caso um cadastro seja alterado depois.

Exemplo:

- um alias de tecido é corrigido;
- o nome oficial do tecido muda;
- o documento original é normalizado de outra forma.

O rolo fechado deve continuar representando aquilo que foi confirmado naquele momento.

---

## 9.4 Regras

- o par `RollId + PrintItemId` deve ser único;
- `Sequence` deve ser única dentro do rolo;
- a sequência deve refletir a ordem operacional;
- `BlockSequence` deve refletir agrupamento consecutivo;
- snapshots devem ser gravados no fechamento;
- um item não deve estar em dois rolos fechados simultaneamente.

---

# 10. Entidade Machine

## 10.1 Finalidade

Representa uma máquina cadastrada.

---

## 10.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador |
| `Code` | `string` | sim | Código operacional |
| `Name` | `string` | sim | Nome exibido |
| `Active` | `bool` | sim | Disponibilidade |
| `Notes` | `string?` | não | Observações |
| `CreatedAt` | `DateTimeOffset` | sim | Criação |
| `UpdatedAt` | `DateTimeOffset` | sim | Alteração |

---

## 10.3 Registros iniciais sugeridos

```text
M1
M2
```

Esses registros não devem ser duplicados a cada inicialização.

---

# 11. Entidade Fabric

## 11.1 Finalidade

Representa o tecido oficial.

---

## 11.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador |
| `Name` | `string` | sim | Nome oficial |
| `NormalizedName` | `string` | sim | Chave de busca |
| `Active` | `bool` | sim | Estado |
| `Notes` | `string?` | não | Observações |
| `CreatedAt` | `DateTimeOffset` | sim | Criação |
| `UpdatedAt` | `DateTimeOffset` | sim | Alteração |

---

## 11.3 Regras

- `NormalizedName` deve ser único;
- nomes desativados não devem desaparecer do histórico;
- alterações futuras não devem modificar snapshots de rolos fechados;
- comparações devem considerar normalização consistente.

---

# 12. Entidade FabricAlias

## 12.1 Finalidade

Representa uma variação textual vinculada a um tecido.

Exemplo:

```text
Dryfit
dry fit
dry-fit
drifit
```

---

## 12.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador |
| `FabricId` | referência | sim | Tecido oficial |
| `Alias` | `string` | sim | Texto original |
| `NormalizedAlias` | `string` | sim | Texto normalizado |
| `Active` | `bool` | sim | Estado |
| `CreatedAt` | `DateTimeOffset` | sim | Criação |
| `UpdatedAt` | `DateTimeOffset` | sim | Alteração |

---

## 12.3 Regras

- `NormalizedAlias` deve ser único;
- um alias deve apontar para apenas um tecido ativo;
- aliases desativados devem continuar disponíveis para auditoria;
- conflito de aliases deve gerar validação explícita.

---

# 13. Entidade RollEvent

## 13.1 Finalidade

Registra acontecimentos importantes do rolo.

---

## 13.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador |
| `RollId` | referência | sim | Rolo |
| `EventType` | `RollEventType` | sim | Tipo |
| `OccurredAt` | `DateTimeOffset` | sim | Data |
| `Summary` | `string` | sim | Resumo legível |
| `PayloadJson` | `string?` | não | Dados complementares |
| `CreatedBy` | `string?` | não | Usuário ou origem |
| `AppVersion` | `string?` | não | Versão do Nexor |

---

## 13.3 Tipos iniciais

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

Nem todos precisam ser implementados imediatamente.

---

## 13.4 Payload

O payload pode armazenar dados complementares.

Exemplo:

```json
{
  "exportType": "pdf",
  "path": "C:\\Nexor\\Exports\\arquivo.pdf",
  "mode": "full"
}
```

O payload não deve substituir campos estruturados importantes.

---

# 14. Entidade ExportRecord

## 14.1 Finalidade

Representa cada arquivo exportado.

Essa entidade é preferível a manter apenas um caminho de PDF diretamente no rolo, pois permite:

- múltiplas exportações;
- reexportações;
- versões;
- tipos diferentes;
- histórico.

---

## 14.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Id` | `Guid` ou `long` | sim | Identificador |
| `RollId` | referência | sim | Rolo |
| `Type` | `ExportType` | sim | Tipo de arquivo |
| `Mode` | `ExportMode` | não | Completo ou resumido |
| `FilePath` | `string` | sim | Caminho |
| `FileName` | `string` | sim | Nome |
| `FileSizeBytes` | `long?` | não | Tamanho |
| `CreatedAt` | `DateTimeOffset` | sim | Data |
| `AppVersion` | `string` | sim | Versão |
| `IsReexport` | `bool` | sim | Reexportação |
| `WidthCm` | `decimal?` | não | Largura do JPG |
| `Dpi` | `int?` | não | Resolução |

---

## 14.3 Tipos

```text
Pdf
MirrorJpg
```

Modos:

```text
Full
Summary
```

---

# 15. Entidade AppSetting

## 15.1 Finalidade

Armazena configurações simples por chave.

---

## 15.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Key` | `string` | sim | Chave única |
| `Value` | `string` | sim | Valor serializado |
| `UpdatedAt` | `DateTimeOffset` | sim | Alteração |

---

## 15.3 Configurações previstas

```text
Theme
DefaultMachine
DefaultImportFolder
PdfExportFolder
MirrorExportFolder
MirrorWidthMode
MirrorCustomWidthCm
MirrorDpi
SearchResultLimit
OpenFolderAfterExport
```

Configurações mais complexas podem permanecer em arquivo JSON, desde que a estratégia seja definida e documentada.

---

# 16. Entidade SchemaVersion

## 16.1 Finalidade

Controla a versão do banco.

---

## 16.2 Campos

| Campo | Tipo sugerido | Obrigatório | Descrição |
|---|---|---:|---|
| `Version` | `int` | sim | Número do schema |
| `AppliedAt` | `DateTimeOffset` | sim | Data de aplicação |
| `Description` | `string?` | não | Resumo da migração |

---

## 16.3 Regras

- migrações devem ser sequenciais;
- uma migração aplicada não deve ser executada novamente;
- falhas devem interromper a atualização;
- alterações destrutivas devem exigir backup;
- cada migração deve possuir teste.

---

# 17. Estados

## 17.1 ImportedLogStatus

```text
New
Parsed
Invalid
Duplicate
Ignored
Converted
```

### Transições esperadas

```text
New → Parsed
New → Invalid
New → Duplicate
Parsed → Converted
Parsed → Ignored
```

---

## 17.2 PrintItemStatus

```text
PendingReview
Ready
Suspicious
AssignedToRoll
Ignored
Corrected
```

### Transições esperadas

```text
PendingReview → Ready
PendingReview → Suspicious
Suspicious → Corrected
Ready → AssignedToRoll
Suspicious → AssignedToRoll, com confirmação
```

---

## 17.3 RollStatus

```text
Draft
Closed
Exported
Reviewed
Reopened
```

### Transições esperadas

```text
Draft → Closed
Closed → Exported
Exported → Reviewed
Closed → Reopened
Exported → Reopened
Reopened → Closed
```

A reabertura ainda é funcionalidade futura.

---

## 17.4 RollEventType

```text
Created
Closed
Exported
Reexported
Reviewed
Reopened
Corrected
```

---

## 17.5 ExportType

```text
Pdf
MirrorJpg
```

---

## 17.6 ExportMode

```text
Full
Summary
```

---

# 18. Relacionamentos

## ImportedLog e PrintItem

```text
ImportedLog 1 ───── 0..1 PrintItem
```

Um arquivo pode:

- ser inválido;
- ser duplicado;
- ser ignorado;
- gerar um item.

---

## PrintItem e Roll

```text
PrintItem 1 ───── 0..1 RollItem
RollItem muitos ───── 1 Roll
```

O vínculo histórico deve ocorrer por `RollItem`.

---

## Roll e RollEvent

```text
Roll 1 ───── muitos RollEvent
```

---

## Roll e ExportRecord

```text
Roll 1 ───── muitos ExportRecord
```

---

## Machine

```text
Machine 1 ───── muitos PrintItem
Machine 1 ───── muitos Roll
```

---

## Fabric

```text
Fabric 1 ───── muitos PrintItem
Fabric 1 ───── muitos FabricAlias
```

---

# 19. Modelo relacional sugerido

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

---

# 20. Índices recomendados

## ImportedLogs

```text
UNIQUE Fingerprint
INDEX ImportedAt
INDEX Status
```

## PrintItems

```text
INDEX PrintedAt
INDEX MachineId
INDEX FabricId
INDEX Status
INDEX RollId
INDEX NormalizedName
```

## Rolls

```text
UNIQUE Code
INDEX ClosedAt
INDEX MachineId
INDEX Status
```

## RollItems

```text
UNIQUE RollId + PrintItemId
UNIQUE RollId + Sequence
INDEX PrintItemId
```

## RollEvents

```text
INDEX RollId
INDEX OccurredAt
INDEX EventType
```

## ExportRecords

```text
INDEX RollId
INDEX CreatedAt
INDEX Type
```

## FabricAliases

```text
UNIQUE NormalizedAlias
INDEX FabricId
```

---

# 21. Constraints recomendadas

- `HeightMm > 0`;
- `PrintedLengthM >= 0`;
- `TotalItems >= 0`;
- `TotalPrintedLengthM >= 0`;
- `Sequence > 0`;
- `BlockSequence > 0`;
- código do rolo não vazio;
- fingerprint não vazio;
- documento não vazio;
- chave de configuração não vazia.

Quando o SQLite não garantir sozinho uma regra, ela deve ser validada pelo domínio e pelos serviços de aplicação.

---

# 22. Transação de fechamento

O fechamento deve ocorrer dentro de uma única transação.

```text
BEGIN TRANSACTION

1. criar ou atualizar Roll;
2. validar composição;
3. inserir RollItems;
4. atualizar PrintItems;
5. registrar RollEvent;
6. recalcular totais;
7. confirmar fechamento;

COMMIT
```

Em caso de falha:

```text
ROLLBACK
```

Não deve existir situação em que:

- o rolo foi salvo;
- mas os itens não foram vinculados;
- ou os itens foram vinculados;
- mas o evento não foi registrado.

---

# 23. Transação de exportação

A geração do arquivo ocorre no sistema de arquivos.

Depois do sucesso:

```text
1. inserir ExportRecord;
2. inserir RollEvent;
3. atualizar status do Roll, quando aplicável.
```

Se a geração falhar:

- não registrar exportação como concluída;
- registrar erro técnico em log;
- informar o usuário;
- preservar o rolo fechado.

---

# 24. Consultas principais

## Listar rolos

Filtros previstos:

- código;
- máquina;
- tecido;
- período;
- status;
- texto contido no documento;
- limite de resultados.

---

## Detalhar rolo

Carregar:

- dados gerais;
- totais;
- itens;
- blocos;
- eventos;
- exportações.

---

## Buscar por pedido ou arquivo

A consulta deve localizar rolos que contenham itens cujo documento corresponda ao texto informado.

---

## Detectar duplicidade

Consulta exata pelo fingerprint.

---

## Itens disponíveis para montagem

Critérios:

- status elegível;
- sem vínculo com rolo fechado;
- máquina compatível, quando o filtro for aplicado;
- não ignorado;
- não inválido.

---

# 25. Auditoria

O modelo deve preservar:

- arquivo de origem;
- fingerprint;
- data de importação;
- erro de parsing;
- nome bruto;
- tecido bruto;
- máquina bruta;
- correções;
- vínculo com rolo;
- data de fechamento;
- eventos;
- exportações;
- versão da aplicação.

---

# 26. Datas e horários

Usar preferencialmente:

```text
DateTimeOffset
```

Persistência sugerida:

```text
ISO 8601
```

Exemplo:

```text
2026-07-16T18:35:42-03:00
```

Evitar armazenar datas em formato visual brasileiro como valor principal.

A apresentação pode usar:

```text
16/07/2026 18:35:42
```

---

# 27. Valores decimais

Metragens devem usar `decimal` no domínio.

Evitar `double` para valores operacionais exibidos e persistidos.

Persistência SQLite deve manter precisão suficiente para:

- milímetros;
- metros;
- arredondamento em centímetros;
- totais.

O arredondamento para exibição não deve alterar o valor bruto persistido.

---

# 28. Exclusão de dados

## Registros históricos

Não devem ser excluídos silenciosamente.

Preferir:

- status;
- inativação;
- auditoria;
- remoção controlada.

## Máquinas e tecidos

Preferir desativação em vez de exclusão física.

## Logs inválidos

Devem permanecer para auditoria, salvo política explícita de retenção futura.

---

# 29. Dados locais

Caminho padrão:

```text
%LOCALAPPDATA%\Nexor\nexor.db
```

O banco não deve ser salvo:

- dentro da pasta de instalação;
- dentro de `Program Files`;
- dentro do repositório;
- dentro da pasta `dist`.

---

# 30. Backup e atualização

Antes de migration destrutiva:

1. localizar o banco;
2. criar backup;
3. validar o arquivo;
4. executar migração;
5. confirmar versão;
6. manter log.

Estrutura sugerida:

```text
%LOCALAPPDATA%\Nexor\backups\
```

Backup automático ainda não é uma funcionalidade obrigatória da versão atual, mas a arquitetura deve permitir sua inclusão.

---

# 31. Integração com o legado

O banco antigo do Jocasta não deve ser modificado.

Uma futura migração deve usar:

- leitor separado;
- mapeamento explícito;
- validação;
- relatório de importação;
- backup;
- operação reversível quando possível.

O Nexor não deve apontar diretamente para o banco do Jocasta como banco principal.

---

# 32. Dados da Trial

Caso a Trial utilize persistência local, seus dados devem permanecer isolados do domínio operacional.

Exemplo de separação:

```text
%LOCALAPPDATA%\Nexor\trial\
```

A lógica de Trial:

- não deve alterar rolos;
- não deve alterar logs;
- não deve alterar relatórios;
- não deve afetar a edição oficial;
- não deve ficar misturada às tabelas operacionais, salvo justificativa forte.

---

# 33. Implementação atual e planejada

## Implementado ou parcialmente implementado

- entidades iniciais;
- parser;
- fingerprint;
- SQLite;
- criação do banco;
- versão de schema;
- repositórios iniciais;
- testes de persistência.

## Pendente de conferência com o código

- nomes definitivos das tabelas;
- campos definitivos;
- uso de `Guid` ou `long`;
- snapshots do rolo;
- eventos completos;
- registros de exportação;
- migrations futuras;
- normalização de tecidos;
- cadastros.

Este documento deve ser atualizado sempre que o schema real mudar.

---

# 34. Critérios de aceite do modelo

O modelo estará adequado ao núcleo operacional quando for possível:

- importar um arquivo;
- identificar duplicidade;
- preservar o conteúdo bruto;
- gerar um item;
- calcular metragem;
- montar um rolo;
- salvar sua composição;
- fechar o rolo;
- recuperar o rolo após reiniciar;
- listar seus itens;
- listar seus eventos;
- registrar exportações;
- reexportar usando os dados históricos.

---

# 35. Decisões pendentes

Ainda precisam ser confirmadas:

- identificadores `Guid` ou inteiros;
- biblioteca de acesso ao SQLite;
- uso de Dapper, EF Core ou implementação própria;
- mecanismo oficial de migration;
- armazenamento integral do conteúdo bruto;
- política de retenção;
- snapshots definitivos;
- estratégia de reabertura;
- auditoria de correções;
- tratamento de arquivos removidos da origem;
- normalização definitiva de tecidos;
- política de backup.

---

# 36. Síntese

O modelo de dados do Nexor deve permitir que cada rolo seja reconstruído de forma confiável.

A regra central é:

```text
O arquivo preserva a origem.
O item representa a impressão.
O vínculo preserva a composição.
O rolo representa o fechamento.
O evento preserva a história.
A exportação registra o documento gerado.
```

O banco local deve ser suficiente para responder o que foi importado, o que foi impresso, como o rolo foi montado, quando foi fechado e quais arquivos foram gerados.