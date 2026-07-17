# Nexor — Arquitetura

## 1. Visão geral

O **Nexor** é uma aplicação desktop local-first voltada para operação, rastreabilidade e consulta de produção têxtil.

A implementação oficial é desenvolvida em:

- C#;
- .NET 8;
- WPF;
- SQLite;
- Windows x64.

A arquitetura foi estruturada para suportar inicialmente o ciclo operacional:

```text
Importar registros
        ↓
Interpretar e validar
        ↓
Organizar itens
        ↓
Montar o rolo
        ↓
Revisar e fechar
        ↓
Persistir
        ↓
Exportar
        ↓
Consultar e reexportar
```

O funcionamento principal deve permanecer disponível sem conexão com a internet.

---

## 2. Objetivos arquiteturais

A arquitetura do Nexor deve favorecer:

- separação clara de responsabilidades;
- regras de negócio independentes da interface;
- persistência local confiável;
- rastreabilidade;
- testabilidade;
- manutenção de longo prazo;
- evolução gradual;
- distribuição como aplicativo Windows;
- recuperação histórica de rolos;
- geração consistente de relatórios;
- expansão futura sem reescrever o núcleo operacional.

---

## 3. Princípios

### 3.1 Local-first

A operação principal deve funcionar localmente.

O Nexor não deve depender de:

- servidor remoto;
- conexão permanente;
- autenticação online;
- serviço externo para fechar rolos;
- serviço externo para consultar registros;
- serviço externo para gerar relatórios.

Recursos online futuros deverão ser opcionais e complementares.

---

### 3.2 Domínio antes da interface

As regras de negócio não devem existir apenas em:

- Views;
- code-behind;
- eventos de botão;
- controles WPF;
- estado visual temporário.

A interface apresenta e coleta informações, mas não define a verdade operacional.

---

### 3.3 Persistência como fonte de verdade

Depois que um rolo for fechado, sua composição deve ser registrada no banco.

Consultas e reexportações devem utilizar dados persistidos.

A interface não deve reconstruir manualmente um rolo histórico usando apenas o conteúdo exibido na tela.

---

### 3.4 Rastreabilidade

A arquitetura deve preservar informações suficientes para responder:

- qual arquivo originou o registro;
- quando ele foi importado;
- de qual máquina veio;
- qual foi sua metragem;
- em qual rolo foi incluído;
- quando o rolo foi fechado;
- quais arquivos foram exportados;
- se houve reexportação;
- se houve erro, correção ou duplicidade.

---

### 3.5 Crescimento controlado

Novos módulos não devem ser adicionados apenas porque aparecem no roadmap.

Planejamento, Estoque, Analytics e sincronização devem entrar somente quando:

- o núcleo operacional estiver estável;
- as regras estiverem definidas;
- houver casos de uso reais;
- a nova camada não prejudicar a operação existente.

---

## 4. Estrutura da solução

A solução oficial é dividida em projetos com responsabilidades distintas.

```text
Nexor.sln
│
├── src/
│   ├── Nexor.Desktop
│   ├── Nexor.Application
│   ├── Nexor.Domain
│   ├── Nexor.Infrastructure
│   └── Nexor.Reporting
│
└── tests/
    ├── Nexor.Domain.Tests
    ├── Nexor.Application.Tests
    └── Nexor.Infrastructure.Tests
```

---

## 5. Dependências entre projetos

A direção principal das dependências deve ser:

```text
Nexor.Desktop
      │
      ▼
Nexor.Application
      │
      ▼
Nexor.Domain
```

A infraestrutura implementa contratos definidos pelas camadas internas:

```text
Nexor.Infrastructure
      │
      ├── implementa persistência
      ├── implementa acesso a arquivos
      ├── implementa parsing
      ├── implementa configurações
      └── implementa logging
```

O projeto de relatórios implementa a geração dos arquivos operacionais:

```text
Nexor.Reporting
      │
      ├── PDF completo
      ├── PDF resumido
      └── JPG espelhado
```

### Regras de dependência

- `Nexor.Domain` não deve depender de nenhum outro projeto da solução.
- `Nexor.Application` pode depender de `Nexor.Domain`.
- `Nexor.Infrastructure` pode depender de `Nexor.Domain` e dos contratos da aplicação.
- `Nexor.Reporting` pode depender do domínio e de modelos próprios de exportação.
- `Nexor.Desktop` pode depender da aplicação e da composição da infraestrutura.
- A camada de domínio não deve conhecer WPF, SQLite, sistema de arquivos ou bibliotecas de relatório.

---

# 6. Nexor.Domain

## 6.1 Responsabilidade

O projeto `Nexor.Domain` representa as regras centrais do produto.

Ele deve conter:

- entidades;
- value objects;
- enums;
- regras de negócio;
- invariantes;
- exceções de domínio;
- interfaces estritamente relacionadas ao domínio;
- cálculos puros.

---

## 6.2 Entidades principais

### ImportedLog

Representa o arquivo bruto importado.

Responsabilidades:

- preservar origem;
- armazenar fingerprint;
- manter conteúdo bruto quando necessário;
- registrar estado de processamento;
- permitir auditoria;
- identificar duplicidade.

---

### PrintItem

Representa um registro de produção interpretado a partir de um arquivo válido.

O nome interno pode variar conforme a implementação, mas textos visíveis ao usuário devem evitar o termo `Job`.

Responsabilidades:

- manter nome original;
- manter documento;
- armazenar data e hora;
- armazenar máquina;
- armazenar tecido;
- armazenar `HeightMM`;
- armazenar `VPositionMM`;
- calcular metragem real;
- representar estado de revisão;
- permitir vínculo com um rolo.

---

### Roll

Representa um rolo operacional.

Responsabilidades:

- agrupar itens;
- armazenar identificação;
- armazenar máquina;
- armazenar datas;
- armazenar estado;
- manter totais;
- congelar composição após fechamento;
- permitir consulta e exportação.

---

### RollItem

Representa o vínculo entre um rolo e um item de produção.

Responsabilidades:

- preservar a composição histórica;
- manter a ordem operacional;
- permitir reconstrução do rolo;
- evitar que um item seja vinculado silenciosamente a vários rolos.

---

### RollEvent

Representa eventos relevantes do ciclo de vida do rolo.

Exemplos:

- criação;
- fechamento;
- exportação;
- reexportação;
- revisão;
- reabertura futura;
- correção futura.

---

### Machine

Representa uma máquina de produção.

Exemplos iniciais:

- M1;
- M2.

---

### Fabric

Representa um tecido normalizado.

---

### FabricAlias

Representa uma variação textual que deve ser associada a um tecido oficial.

---

## 6.3 Regras centrais

### Cálculo de metragem

```text
Metragem real = HeightMM / 1000
```

`VPositionMM` representa deslocamento e não entra no cálculo da metragem impressa.

---

### Ordenação operacional

Os registros devem ser ordenados por `EndTime` em ordem decrescente.

```text
Último impresso → primeiro da lista
```

---

### Agrupamento por tecido

O agrupamento considera sequências consecutivas.

Exemplo:

```text
Dryfit
Dryfit
Elastano
Dryfit
```

Resultado:

```text
Bloco 1 — Dryfit
Bloco 2 — Elastano
Bloco 3 — Dryfit
```

O segundo conjunto Dryfit não deve ser unido ao primeiro, porque outro tecido apareceu entre eles.

---

### Duplicidade

Cada arquivo importado deve possuir um fingerprint determinístico.

A implementação atual utiliza SHA-256.

Registros duplicados:

- não devem ser reprocessados silenciosamente;
- devem permanecer identificáveis;
- não devem apagar registros anteriores;
- devem gerar retorno compreensível para o usuário.

---

### Fechamento

Um rolo não pode ser fechado sem itens.

Depois do fechamento:

- a composição fica congelada;
- os itens ficam vinculados;
- os totais ficam persistidos;
- relatórios devem ser gerados a partir do registro salvo.

---

# 7. Nexor.Application

## 7.1 Responsabilidade

O projeto `Nexor.Application` coordena os casos de uso.

Ele não deve conter:

- SQL;
- controles WPF;
- caminhos físicos fixos;
- detalhes de PDF;
- chamadas diretas a caixas de diálogo;
- manipulação de elementos visuais.

---

## 7.2 Casos de uso iniciais

### Importar arquivos

Responsável por:

- receber caminhos;
- validar extensões;
- calcular fingerprint;
- detectar duplicidade;
- solicitar parsing;
- persistir os registros;
- retornar resumo da operação.

---

### Importar pasta

Responsável por:

- localizar arquivos compatíveis;
- organizar o lote;
- aplicar as mesmas regras da importação individual;
- preservar importações anteriores;
- retornar quantidade de itens importados, inválidos e duplicados.

---

### Montar rolo

Responsável por:

- receber itens selecionados;
- validar elegibilidade;
- calcular totais;
- ordenar;
- agrupar;
- gerar resumo do rascunho.

---

### Fechar rolo

Responsável por:

- validar composição;
- validar identificação;
- validar máquina;
- recalcular totais;
- persistir o rolo;
- persistir vínculos;
- registrar evento;
- retornar resultado do fechamento.

---

### Consultar rolos

Responsável por:

- aplicar filtros;
- retornar lista paginada ou limitada;
- carregar resumo;
- carregar itens;
- carregar eventos.

---

### Exportar rolo

Responsável por:

- carregar dados persistidos;
- construir modelo de relatório;
- solicitar geração ao projeto de Reporting;
- registrar caminhos;
- registrar evento de exportação.

---

### Reexportar rolo

Responsável por:

- localizar rolo existente;
- usar composição histórica;
- gerar novo arquivo;
- preservar exportações anteriores;
- registrar novo evento.

---

# 8. Nexor.Infrastructure

## 8.1 Responsabilidade

O projeto `Nexor.Infrastructure` contém as implementações concretas.

Ele deve cuidar de:

- SQLite;
- repositórios;
- migrations;
- leitura de arquivos;
- parsing;
- fingerprint;
- configurações;
- logs técnicos;
- caminhos locais;
- sistema de arquivos.

---

## 8.2 Banco SQLite

O banco local é armazenado por padrão em:

```text
%LOCALAPPDATA%\Nexor\nexor.db
```

A pasta local poderá conter também:

```text
%LOCALAPPDATA%\Nexor\
├── nexor.db
├── config.json
├── logs\
├── trial\
└── temp\
```

A estrutura real deve ser documentada conforme os arquivos forem implementados.

---

## 8.3 Criação do banco

Na primeira execução:

1. a pasta local é criada;
2. o banco é criado;
3. o schema inicial é aplicado;
4. a versão do schema é registrada;
5. dados básicos podem ser inseridos quando necessário.

---

## 8.4 Evolução do schema

O schema não deve ser alterado de forma implícita.

Cada mudança deve possuir:

- número de versão;
- instrução de migração;
- teste;
- tratamento de erro;
- preservação dos dados existentes.

Exemplo:

```text
Schema 1 → estrutura inicial
Schema 2 → novos eventos de exportação
Schema 3 → novos campos de consulta
```

---

## 8.5 Repositórios

Repositórios devem abstrair persistência.

Exemplos:

- `ImportedLogRepository`;
- `PrintItemRepository`;
- `RollRepository`;
- `RollEventRepository`;
- `SettingsRepository`.

As Views e ViewModels não devem executar SQL diretamente.

---

## 8.6 Parsing de logs

O parser inicial é baseado no formato de registros utilizado pelo ecossistema PX.

Campos principais:

```text
[General]
EndTime=
Document=

[1]
HeightMM=
VPositionMM=
```

O parser deve:

- aceitar formatos conhecidos de data;
- aceitar decimal com ponto ou vírgula quando necessário;
- preservar o arquivo de origem;
- retornar erro estruturado;
- não apagar conteúdo inválido;
- diferenciar falha de leitura e falha de validação.

---

## 8.7 Sistema de arquivos

O acesso ao sistema de arquivos deve ficar isolado.

Responsabilidades:

- abrir arquivos;
- enumerar diretórios;
- validar extensões;
- calcular hash;
- criar pastas;
- gerar caminhos;
- evitar sobrescrita;
- abrir pastas no Explorer;
- criar nomes versionados.

---

## 8.8 Configurações

As configurações devem ser persistidas por usuário.

Exemplos:

- tema;
- pasta de importação;
- pasta de PDF;
- pasta de JPG;
- máquina padrão;
- limites de consulta;
- tamanho do JPG espelhado;
- comportamento de abertura de pastas.

Configurações inválidas devem ser tratadas sem impedir a inicialização completa quando houver um padrão seguro.

---

## 8.9 Logging

O Nexor deve produzir logs técnicos para diagnóstico.

Os logs devem registrar:

- inicialização;
- versão;
- criação do banco;
- migrations;
- erros de parsing;
- erros de persistência;
- falhas de exportação;
- exceções não tratadas;
- informações de ambiente não sensíveis.

Não devem registrar:

- senhas;
- tokens;
- chaves;
- dados confidenciais desnecessários;
- conteúdo integral de produção sem justificativa.

---

# 9. Nexor.Reporting

## 9.1 Responsabilidade

O projeto `Nexor.Reporting` gera os artefatos formais.

Saídas previstas:

- PDF completo;
- PDF resumido;
- JPG espelhado.

---

## 9.2 Regra de origem dos dados

Relatórios devem ser gerados a partir de um modelo estruturado proveniente do banco.

Fluxo correto:

```text
Roll persistido
      ↓
Application carrega dados
      ↓
Modelo de relatório
      ↓
Reporting gera arquivo
```

Fluxo incorreto:

```text
DataGrid
      ↓
captura de textos visíveis
      ↓
gera relatório
```

---

## 9.3 PDF completo

Deve conter:

- identificação do rolo;
- máquina;
- data;
- itens;
- horário;
- documento;
- tecido;
- metragem;
- separação entre blocos;
- resumo;
- total geral.

---

## 9.4 PDF resumido

Deve conter:

- identificação;
- máquina;
- blocos de tecido;
- quantidade de itens;
- metragem por bloco;
- total geral.

---

## 9.5 JPG espelhado

Deve ser gerado a partir do relatório correspondente.

Requisitos:

- espelhamento horizontal;
- largura física configurável;
- resolução adequada;
- proporção preservada;
- nome versionado;
- ausência de sobrescrita silenciosa.

---

# 10. Nexor.Desktop

## 10.1 Responsabilidade

O projeto `Nexor.Desktop` contém a aplicação WPF.

Ele deve cuidar de:

- Views;
- ViewModels;
- navegação;
- temas;
- controles;
- dialogs;
- comandos;
- mensagens ao usuário;
- apresentação de estados.

---

## 10.2 Estrutura visual

O layout é baseado na organização visual do ListForge:

```text
┌───────────────┬────────────────────────────────────┐
│               │ Topbar                             │
│ Sidebar       ├────────────────────────────────────┤
│               │                                    │
│               │ Conteúdo                           │
│               │                                    │
│               ├────────────────────────────────────┤
│               │ Barra de status                    │
└───────────────┴────────────────────────────────────┘
```

O ListForge é apenas referência visual.

A lógica de negócio do ListForge não compõe o Nexor.

---

## 10.3 Navegação inicial

Telas iniciais:

- Home;
- Operação;
- Rolos;
- Configurações;
- Sobre.

Telas futuras:

- Cadastros;
- Planejamento;
- Estoque;
- Analytics.

Telas futuras não devem ser apresentadas como funcionais antes da implementação real.

---

## 10.4 MVVM

A aplicação deve adotar MVVM.

### View

Responsável por:

- layout;
- binding;
- apresentação;
- comportamento estritamente visual.

### ViewModel

Responsável por:

- estado;
- comandos;
- validações de interface;
- chamada de casos de uso;
- mensagens preparadas para apresentação.

### Model e Domain

Responsáveis pelo significado dos dados e regras.

---

## 10.5 Code-behind

Code-behind é permitido apenas para comportamento visual específico.

Exemplos aceitáveis:

- foco;
- drag and drop;
- atalhos;
- interação visual difícil de representar via binding;
- integração específica com a janela.

Não deve conter:

- regras de metragem;
- SQL;
- montagem de rolo;
- fechamento;
- consulta;
- lógica de duplicidade;
- geração de relatório.

---

## 10.6 Navegação

A navegação deve ser centralizada.

Evitar:

- múltiplos blocos manuais de `Visibility`;
- criação direta de telas em vários lugares;
- regras de navegação espalhadas;
- dependência circular entre ViewModels.

Uma opção recomendada:

```text
INavigationService
NavigationService
MainViewModel
CurrentViewModel
```

---

## 10.7 Temas

Temas iniciais:

- Nexor Dark;
- Nexor Light;
- SISBolt.

Os temas usam `ResourceDictionary`.

Recursos devem utilizar chaves semânticas, como:

```text
AppBackgroundBrush
SidebarBackgroundBrush
PrimaryBrush
TextPrimaryBrush
TextMutedBrush
BorderBrush
SuccessBrush
WarningBrush
DangerBrush
```

Evitar cores fixas diretamente em cada View.

---

## 10.8 Vocabulário

O termo `Job` deve ser evitado em textos visíveis.

Usar conforme o contexto:

- item;
- registro;
- impressão;
- arquivo;
- pedido;
- processamento;
- tarefa.

O termo técnico pode existir internamente quando fizer sentido.

---

# 11. Estados e mensagens

A interface deve representar claramente:

- carregando;
- vazio;
- sucesso;
- alerta;
- erro;
- inválido;
- duplicado;
- selecionado;
- já vinculado;
- exportado;
- fechado.

Estados não devem depender somente de cor.

Usar também:

- texto;
- ícone;
- badge;
- tooltip;
- mensagem de apoio.

---

# 12. Fluxos arquiteturais

## 12.1 Importação

```text
Usuário seleciona arquivo
        ↓
Desktop envia comando
        ↓
Application valida solicitação
        ↓
Infrastructure lê arquivo
        ↓
Fingerprint é calculado
        ↓
Repositório consulta duplicidade
        ↓
Parser interpreta conteúdo
        ↓
Domain valida valores
        ↓
Repositório persiste
        ↓
Desktop exibe resultado
```

---

## 12.2 Montagem do rolo

```text
Usuário seleciona itens
        ↓
ViewModel mantém seleção
        ↓
Application monta resumo
        ↓
Domain calcula totais
        ↓
Desktop exibe composição
```

---

## 12.3 Fechamento

```text
Usuário confirma fechamento
        ↓
Application valida metadados
        ↓
Domain valida invariantes
        ↓
Infrastructure inicia transação
        ↓
Rolo é persistido
        ↓
Itens são vinculados
        ↓
Evento é registrado
        ↓
Transação é confirmada
```

---

## 12.4 Exportação

```text
Usuário solicita exportação
        ↓
Application recupera rolo persistido
        ↓
Reporting gera PDF/JPG
        ↓
Infrastructure registra caminho
        ↓
Evento de exportação é salvo
        ↓
Desktop mostra resultado
```

---

## 12.5 Consulta

```text
Usuário aplica filtros
        ↓
Application prepara consulta
        ↓
Repository executa busca
        ↓
Resultados são mapeados
        ↓
Desktop exibe lista
        ↓
Usuário seleciona rolo
        ↓
Detalhes, itens e eventos são carregados
```

---

# 13. Transações

Operações críticas devem ser transacionais.

Especialmente:

- fechamento do rolo;
- vínculo dos itens;
- registro de evento;
- atualização do estado;
- armazenamento dos dados de exportação.

Se uma parte falhar, o sistema deve evitar salvar um estado parcial inconsistente.

---

# 14. Tratamento de erros

Erros devem ser divididos em categorias.

### Erro de validação

Exemplo:

```text
Nenhum item foi selecionado.
```

### Erro de entrada

Exemplo:

```text
O arquivo não possui HeightMM válido.
```

### Erro de duplicidade

Exemplo:

```text
Este arquivo já foi importado.
```

### Erro técnico

Exemplo:

```text
Não foi possível acessar o banco de dados.
```

### Erro de configuração

Exemplo:

```text
A pasta de exportação não está disponível.
```

Mensagens para o usuário devem ser simples.

Detalhes técnicos devem ficar nos logs.

---

# 15. Testes

## 15.1 Testes de domínio

Devem cobrir:

- metragem;
- validações;
- estados;
- fechamento;
- agrupamento;
- ordenação;
- invariantes.

---

## 15.2 Testes de aplicação

Devem cobrir:

- importação;
- duplicidade;
- montagem;
- fechamento;
- consulta;
- exportação;
- reexportação.

---

## 15.3 Testes de infraestrutura

Devem cobrir:

- parser;
- SQLite;
- migrations;
- repositórios;
- arquivos;
- fingerprint;
- configurações.

---

## 15.4 Testes de integração

Devem validar o ciclo:

```text
Importar
→ persistir
→ montar
→ fechar
→ consultar
→ recuperar
```

Quando Reporting estiver concluído:

```text
Importar
→ fechar
→ gerar PDF
→ gerar JPG
→ consultar
→ reexportar
```

---

# 16. Build e distribuição

A aplicação deve ser publicada para:

```text
win-x64
```

Modalidades previstas:

- one-file oficial;
- Trial;
- publicação instalável;
- instalador.

Os artefatos devem ser organizados por versão:

```text
dist/
└── X.Y.Z/
    ├── onefile/
    ├── trial/
    ├── installable/
    └── installer/
```

Builds anteriores não devem ser sobrescritos.

---

# 17. Trial

Quando ativa, a edição Trial deve permanecer separada da edição oficial.

A identificação deve aparecer em:

- título;
- tela Sobre;
- executável;
- instalador;
- documentação;
- metadados.

A Trial atual utiliza avaliação local de 30 dias.

A edição oficial:

- não deve expirar;
- não deve depender do estado da Trial;
- não deve sofrer bloqueio por regras de avaliação.

A arquitetura de Trial deve permanecer isolada das regras operacionais.

---

# 18. Segurança

O Nexor não deve armazenar no repositório:

- tokens;
- credenciais;
- chaves privadas;
- senhas;
- dados reais de clientes;
- registros confidenciais de produção.

Os arquivos locais devem utilizar pastas apropriadas do usuário.

O banco do Projeto Jocasta não deve ser modificado.

Qualquer migração futura deve:

- ser explícita;
- possuir backup;
- ser testada;
- não ocorrer silenciosamente.

---

# 19. Legado

A implementação Python anterior está preservada em:

```text
legacy/Nexor-Python-Legacy
```

Ela serve para:

- histórico;
- comparação;
- consulta de regras anteriores;
- recuperação de conhecimento.

Ela não deve:

- ser importada pela solução C#;
- ser usada em runtime;
- exigir Python para executar o Nexor atual;
- definir a arquitetura nova.

---

# 20. Referências externas do projeto

## PXPrintLogs

Referência funcional para:

- importação;
- parsing;
- blocos;
- metragem;
- fechamento;
- PDF;
- JPG espelhado;
- persistência de exportações.

## PXSearchOrders

Referência funcional para:

- consulta;
- filtros;
- detalhes;
- itens;
- eventos;
- reexportação.

## ListForge

Referência visual para:

- WPF;
- sidebar;
- topbar;
- barra de status;
- temas;
- organização da janela;
- padrão de distribuição.

Os três projetos permanecem independentes.

---

# 21. Escopo atual

## Implementado ou parcialmente implementado

- solução em camadas;
- shell WPF;
- navegação;
- temas;
- domínio inicial;
- parser inicial;
- fingerprint;
- SQLite;
- repositórios;
- testes iniciais.

## Em desenvolvimento

- importação pela interface;
- montagem;
- fechamento;
- consulta detalhada;
- exportações;
- reexportação.

## Futuro

- cadastros;
- planejamento;
- estoque;
- analytics;
- backup;
- sincronização;
- multiestação.

---

# 22. Decisões arquiteturais atuais

1. A aplicação oficial será escrita em C#.
2. A interface será WPF.
3. O banco principal será SQLite.
4. A aplicação será local-first.
5. O domínio não dependerá da UI.
6. Relatórios serão gerados a partir de dados persistidos.
7. O ListForge será apenas referência visual.
8. O Jocasta será apenas referência funcional.
9. O legado Python será preservado temporariamente.
10. Planejamento, Estoque e Analytics não serão priorizados antes do núcleo operacional.

---

# 23. Critérios de maturidade

A arquitetura estará pronta para a primeira versão estável quando:

- arquivos puderem ser importados pela interface;
- duplicidades forem tratadas;
- um rolo puder ser montado;
- o rolo puder ser fechado;
- a composição for persistida;
- PDF e JPG puderem ser gerados;
- o rolo puder ser consultado;
- os arquivos puderem ser reexportados;
- erros forem registrados;
- testes cobrirem o fluxo principal;
- o instalador funcionar em ambiente limpo.

---

# 24. Próximas decisões

As próximas decisões arquiteturais devem tratar:

- contratos definitivos dos serviços de importação;
- schema SQLite real;
- estratégia de migrations;
- biblioteca de PDF;
- biblioteca de conversão para JPG;
- navegação definitiva;
- logging;
- configurações;
- estratégia de Trial;
- fluxo de reabertura;
- política de backup local;
- tratamento de arquivos ainda sendo gravados.

---

# 25. Síntese

A arquitetura do Nexor deve proteger o núcleo operacional contra acoplamento excessivo.

A regra principal é:

```text
A interface solicita.
A aplicação coordena.
O domínio decide.
A infraestrutura executa.
O banco preserva.
O Reporting apresenta.
```

Essa separação permite que o Nexor evolua de um aplicativo operacional local para uma plataforma mais ampla sem comprometer a confiabilidade do fluxo principal.