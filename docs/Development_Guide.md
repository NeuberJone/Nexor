# Nexor — Guia de Desenvolvimento

## 1. Objetivo

Este documento orienta a preparação do ambiente, execução, depuração, testes e desenvolvimento diário do **Nexor**.

O projeto utiliza:

- C#;
- .NET 8;
- WPF;
- SQLite;
- MVVM;
- Windows x64.

Este guia é destinado a desenvolvedores que precisam:

- clonar o repositório;
- entender a estrutura inicial;
- executar a aplicação;
- criar funcionalidades;
- trabalhar com o banco;
- executar testes;
- preparar alterações para revisão.

Para geração dos artefatos, consulte:

- `docs/Build_Guide.md`;
- `docs/Release_Process.md`.

---

# 2. Repositório oficial

A pasta oficial de desenvolvimento é:

```text
F:\Projetos\Nexor
```

Essa pasta deve ser considerada a fonte principal do projeto.

Antes de qualquer alteração:

```powershell
cd F:\Projetos\Nexor
git status
```

Verifique:

- branch atual;
- arquivos modificados;
- arquivos não rastreados;
- conflitos;
- mudanças pendentes;
- versão atual.

Não altere cópias externas e depois substitua arquivos sem revisar o histórico.

---

# 3. Requisitos

## Sistema operacional

- Windows 10 x64;
- Windows 11 x64.

## Ferramentas obrigatórias

- Git;
- .NET SDK 8;
- PowerShell;
- editor ou IDE com suporte a C#.

## IDEs recomendadas

- Visual Studio 2022;
- JetBrains Rider;
- Visual Studio Code com extensão C#.

## Ferramentas opcionais

- DB Browser for SQLite;
- SQLite CLI;
- Inno Setup;
- GitHub Desktop;
- ferramentas de inspeção de logs.

---

# 4. Verificar o .NET

Execute:

```powershell
dotnet --info
```

Confirme que existe um SDK da linha:

```text
8.0.x
```

Listar os SDKs disponíveis:

```powershell
dotnet --list-sdks
```

Caso o SDK 8 não esteja disponível, instale-o antes de tentar compilar o projeto.

---

# 5. Clonar o repositório

```powershell
git clone https://github.com/NeuberJone/Nexor.git
cd Nexor
```

Caso o repositório já esteja em `F:\Projetos\Nexor`, não faça um novo clone sobre a pasta existente.

---

# 6. Estrutura principal

A estrutura geral do projeto é:

```text
Nexor/
├── docs/
├── installer/
├── legacy/
├── Nexor.Application/
├── Nexor.Domain/
├── Nexor.Infrastructure/
├── Nexor.Reporting/
├── src/
├── tests/
├── CHANGELOG.md
├── Directory.Build.props
├── LICENSE.md
├── Nexor.sln
├── README.md
└── ROADMAP.md
```

A estrutura real deve ser considerada antes de criar novos diretórios.

Não duplique projetos ou documentos que já existam.

---

# 7. Responsabilidade dos projetos

## Nexor.Domain

Contém:

- entidades;
- value objects;
- enums;
- invariantes;
- cálculos;
- regras de negócio;
- exceções de domínio.

Não deve depender de:

- WPF;
- SQLite;
- sistema de arquivos;
- bibliotecas de relatório;
- ViewModels.

---

## Nexor.Application

Contém:

- casos de uso;
- contratos;
- comandos;
- resultados;
- serviços de aplicação;
- coordenação das operações.

Pode depender de:

```text
Nexor.Domain
```

Não deve conter:

- SQL;
- componentes WPF;
- `MessageBox`;
- acesso direto ao sistema de arquivos;
- detalhes concretos do SQLite.

---

## Nexor.Infrastructure

Contém:

- SQLite;
- schema;
- migrations;
- repositórios;
- parsing;
- leitura de arquivos;
- fingerprint;
- configurações;
- logging;
- caminhos locais.

Implementa contratos definidos pelas camadas internas.

---

## Nexor.Reporting

Contém:

- PDF completo;
- PDF resumido;
- JPG espelhado;
- modelos de relatório;
- templates;
- conversões necessárias.

Relatórios devem ser gerados a partir de dados estruturados e persistidos.

---

## Aplicação WPF

A aplicação desktop contém:

- Views;
- ViewModels;
- navegação;
- temas;
- dialogs;
- controles;
- recursos;
- conversores visuais.

A localização exata deve seguir a solução atual, normalmente em `src`.

---

## Tests

Contém testes de:

- domínio;
- aplicação;
- infraestrutura;
- integração;
- parsing;
- persistência.

Os testes não devem acessar o banco real do usuário.

---

# 8. Restaurar dependências

Na raiz:

```powershell
dotnet restore Nexor.sln
```

O comando deve concluir sem erros.

Caso falhe, verifique:

- SDK;
- internet;
- fontes NuGet;
- versões dos pacotes;
- caminhos dos projetos;
- referências da solução.

---

# 9. Compilar

Build de desenvolvimento:

```powershell
dotnet build Nexor.sln
```

Build Release:

```powershell
dotnet build Nexor.sln -c Release
```

Não ignore erros de analyzers ou nullable sem compreender a causa.

---

# 10. Executar

Use o caminho real do projeto WPF existente na solução.

Exemplo:

```powershell
dotnet run --project src/Nexor.Desktop/Nexor.Desktop.csproj
```

Caso o projeto possua outro nome ou localização, use o caminho real encontrado no repositório.

Também é possível abrir `Nexor.sln` na IDE e executar o projeto desktop como startup project.

---

# 11. Executar testes

```powershell
dotnet test Nexor.sln
```

Release:

```powershell
dotnet test Nexor.sln -c Release
```

Executar um projeto específico:

```powershell
dotnet test tests/Nexor.Domain.Tests/Nexor.Domain.Tests.csproj
```

Executar por filtro:

```powershell
dotnet test --filter "FullyQualifiedName~Roll"
```

Os caminhos devem ser ajustados à estrutura real.

---

# 12. Ambiente local

O Nexor armazena dados em:

```text
%LOCALAPPDATA%\Nexor
```

Caminho equivalente:

```text
C:\Users\NOME\AppData\Local\Nexor
```

Conteúdo possível:

```text
Nexor/
├── nexor.db
├── config.json
├── logs/
├── exports/
├── backups/
├── temp/
└── trial/
```

Nunca use dados operacionais reais como massa padrão de desenvolvimento.

---

# 13. Banco de desenvolvimento

Durante testes manuais, o banco pode ser criado no diretório local padrão.

Antes de apagar ou substituir:

1. feche o aplicativo;
2. verifique se há dados importantes;
3. faça uma cópia;
4. registre o motivo;
5. evite confundir banco de teste e banco real.

Para testes automatizados, use:

- arquivo temporário;
- diretório temporário;
- banco exclusivo por teste;
- transação isolada.

Não use:

```text
%LOCALAPPDATA%\Nexor\nexor.db
```

em testes automatizados.

---

# 14. Reiniciar o ambiente local

Para testar a primeira execução:

1. feche o Nexor;
2. localize `%LOCALAPPDATA%\Nexor`;
3. faça backup;
4. renomeie a pasta, por exemplo:

```text
Nexor-backup
```

5. execute novamente;
6. confirme criação do banco e configurações.

Não exclua dados sem backup.

---

# 15. Logs

Os logs técnicos devem ficar em:

```text
%LOCALAPPDATA%\Nexor\logs
```

Ao investigar uma falha, procure:

- horário;
- categoria;
- exceção;
- operação;
- versão;
- caminho relacionado;
- migration em execução.

Evite adicionar logs contendo dados sensíveis.

---

# 16. Fluxo de desenvolvimento

Fluxo recomendado:

```text
Entender a solicitação
        ↓
Inspecionar o código existente
        ↓
Identificar a camada correta
        ↓
Implementar
        ↓
Adicionar ou atualizar testes
        ↓
Executar build
        ↓
Executar testes
        ↓
Validar manualmente
        ↓
Atualizar documentação
        ↓
Revisar diff
        ↓
Commit
```

---

# 17. Antes de implementar

Antes de criar classes ou arquivos:

- pesquise se já existe algo equivalente;
- revise o domínio;
- revise os contratos;
- revise o schema;
- revise os documentos;
- identifique dependências;
- evite criar uma segunda solução para o mesmo problema.

Perguntas obrigatórias:

- isso é regra de domínio?
- isso é um caso de uso?
- isso é infraestrutura?
- isso pertence à UI?
- já existe um serviço equivalente?
- precisa realmente de nova dependência?

---

# 18. Criando uma funcionalidade

Exemplo: importação de pasta.

## Domain

Somente regras puras necessárias.

Exemplos:

- validação de metragem;
- estado do item;
- fingerprint como conceito.

## Application

Caso de uso:

```text
ImportFolder
```

Responsável por:

- receber a solicitação;
- coordenar serviços;
- retornar resultado.

## Infrastructure

Responsável por:

- enumerar arquivos;
- ler conteúdo;
- calcular hash;
- persistir;
- executar parser concreto.

## Desktop

Responsável por:

- selecionar pasta;
- mostrar progresso;
- disparar comando;
- mostrar resultado.

## Tests

Cobrir:

- pasta vazia;
- arquivos válidos;
- duplicados;
- inválidos;
- cancelamento;
- falha de acesso.

---

# 19. Criando uma nova tela

Antes de criar uma View:

1. confirme que a tela faz parte do escopo;
2. defina o caso de uso;
3. identifique os dados;
4. crie o ViewModel;
5. registre a navegação;
6. use os recursos dos temas;
7. evite lógica no code-behind;
8. adicione estado vazio;
9. adicione loading;
10. adicione erros.

Não adicione telas vazias apenas para mostrar módulos futuros.

---

# 20. ViewModels

Um ViewModel deve cuidar de:

- estado;
- propriedades observáveis;
- comandos;
- carregamento;
- mensagens;
- chamada dos casos de uso.

Não deve:

- executar SQL;
- calcular regras centrais;
- gerar PDF diretamente;
- ler arquivos diretamente;
- construir Views;
- acessar controles por nome.

Exemplo de responsabilidades:

```csharp
public sealed class OperationViewModel
{
    public bool IsLoading { get; }
    public string SearchText { get; set; }
    public IReadOnlyList<PrintItemViewModel> Items { get; }
    public IAsyncCommand ImportFilesCommand { get; }
    public IAsyncCommand ReviewRollCommand { get; }
}
```

---

# 21. Code-behind

Pode ser usado para:

- drag and drop;
- foco;
- atalhos;
- comportamento visual;
- integração específica da janela.

Não pode conter:

- persistência;
- cálculo;
- fechamento;
- geração de relatórios;
- busca histórica;
- regra de duplicidade.

---

# 22. Temas

Os temas utilizam `ResourceDictionary`.

Temas iniciais:

- Nexor Dark;
- Nexor Light;
- SISBolt.

Ao criar um componente:

- use recursos semânticos;
- teste nos três temas;
- evite cor fixa;
- verifique hover;
- verifique seleção;
- verifique desabilitado;
- verifique contraste.

Exemplo:

```xml
<Border Background="{DynamicResource SurfaceBrush}"
        BorderBrush="{DynamicResource BorderBrush}">
```

---

# 23. Parsing

O parser deve ser independente da UI.

Campos iniciais:

```text
EndTime
Document
HeightMM
VPositionMM
```

Ao alterar o parser:

- preserve casos anteriores;
- adicione testes;
- documente formatos aceitos;
- trate ponto e vírgula;
- preserve erro estruturado;
- não descarte origem;
- não altere a fórmula de metragem.

Regra:

```text
PrintedLengthM = HeightMM / 1000
```

`VPositionMM` não entra na metragem.

---

# 24. Persistência

Ao alterar o banco:

- crie migration;
- atualize a versão do schema;
- teste banco vazio;
- teste banco anterior;
- atualize `Data_Model.md`;
- atualize `Database_Guide.md`;
- revise rollback;
- avalie backup.

Não faça mudanças silenciosas no schema.

---

# 25. Transações

Fluxos críticos devem ser transacionais.

Exemplo: fechamento do rolo.

```text
Criar rolo
→ inserir vínculos
→ atualizar itens
→ registrar evento
→ confirmar
```

Se qualquer etapa falhar:

```text
rollback
```

Teste explicitamente falhas intermediárias.

---

# 26. Dependências externas

Antes de adicionar um pacote NuGet:

- confirme necessidade;
- confira licença;
- confira manutenção;
- confira compatibilidade com .NET 8;
- confira WPF;
- confira one-file;
- confira tamanho;
- confira impacto no instalador.

Depois:

- adicione somente ao projeto necessário;
- atualize documentação;
- execute testes;
- verifique publicação.

---

# 27. Dados de demonstração

Use dados fictícios.

Exemplo:

```text
16-07 - Dryfit - PEDIDO DEMONSTRACAO.jpeg
```

Não versionar:

- pedidos reais;
- clientes reais;
- bancos reais;
- logs de produção;
- caminhos internos sensíveis;
- documentos confidenciais.

---

# 28. Testes unitários

Devem cobrir regras isoladas.

Exemplos:

- cálculo de metragem;
- código do rolo;
- transição de estado;
- ordenação;
- agrupamento consecutivo;
- validação de fechamento.

Os testes devem ser rápidos e determinísticos.

---

# 29. Testes de integração

Devem validar interação entre componentes.

Exemplos:

```text
arquivo
→ parser
→ aplicação
→ SQLite
```

```text
itens
→ fechamento
→ banco
→ consulta
```

Use ambiente isolado.

---

# 30. Testes manuais

Depois de alterar UI ou fluxo:

- abrir;
- navegar;
- executar ação principal;
- provocar erro;
- reiniciar;
- confirmar persistência;
- testar temas;
- testar escala do Windows;
- verificar logs.

Não declarar teste manual concluído sem realmente executá-lo.

---

# 31. Depuração

Na IDE:

- defina o projeto WPF como inicial;
- use configuração Debug;
- adicione breakpoints;
- inspecione logs;
- verifique exceções;
- não dependa somente de `MessageBox`.

Para problemas de banco:

- copie o banco;
- abra em ferramenta SQLite;
- não edite o banco real sem backup.

---

# 32. Erros comuns

## SDK incompatível

Sintoma:

```text
The current .NET SDK does not support targeting .NET 8
```

Solução:

- instalar SDK 8;
- verificar `global.json`, se existir;
- reiniciar terminal e IDE.

---

## Projeto WPF não abre

Verifique:

- Windows;
- `TargetFramework`;
- `UseWPF`;
- SDK;
- recursos XAML;
- referências.

---

## ResourceDictionary não encontrado

Verifique:

- caminho;
- Build Action;
- URI;
- capitalização;
- inclusão no projeto.

---

## Banco bloqueado

Verifique:

- outra instância;
- ferramenta SQLite aberta;
- processo encerrado incorretamente;
- antivírus;
- pasta sincronizada.

---

## Testes afetam dados reais

Interrompa os testes e corrija o caminho.

Testes devem usar banco temporário.

---

# 33. Git

Antes de criar branch:

```powershell
git status
git pull
```

Exemplos de branches:

```text
feat/import-folder
feat/roll-closure
fix/duplicate-detection
refactor/navigation-service
docs/update-development-guide
```

Evite desenvolver funcionalidades grandes diretamente na `main`, salvo decisão explícita do projeto.

---

# 34. Commits

Use Conventional Commits.

Exemplos:

```text
feat: add folder log import
fix: preserve selected records after refresh
refactor: isolate roll closure transaction
docs: add development workflow
test: cover duplicate fingerprint detection
```

Um commit deve representar uma alteração coerente.

---

# 35. Revisar o diff

Antes do commit:

```powershell
git diff
git status
```

Verifique:

- arquivos esperados;
- alterações acidentais;
- versão;
- formatação;
- dados sensíveis;
- arquivos binários;
- banco;
- logs;
- `bin`;
- `obj`;
- `dist`.

---

# 36. Arquivos que não devem ser versionados

- `bin/`;
- `obj/`;
- bancos locais;
- configurações pessoais;
- logs;
- temporários;
- cache;
- segredos;
- arquivos reais de produção;
- artefatos não aprovados.

A política de versionamento de `dist` deve seguir a decisão oficial do projeto.

---

# 37. Documentação

Atualize documentação quando alterar:

- arquitetura;
- schema;
- fluxo;
- UI;
- instalação;
- build;
- release;
- versão;
- comportamento Trial;
- requisitos.

Não atualize todos os documentos sem necessidade, mas elimine contradições.

---

# 38. Legado

O código Python está em:

```text
legacy/
```

Ele pode ser consultado para:

- regras;
- comportamento;
- comparação;
- histórico.

Não deve ser:

- importado pelo C#;
- executado em runtime;
- usado como dependência;
- copiado linha por linha sem revisão;
- tratado como arquitetura atual.

---

# 39. Projeto Jocasta

Referências funcionais:

- PXPrintLogs;
- PXSearchOrders.

Não altere o Jocasta durante o desenvolvimento do Nexor, salvo solicitação explícita separada.

Use o comportamento como referência, não a arquitetura Tkinter.

---

# 40. ListForge

O ListForge serve como referência visual.

Pode orientar:

- shell;
- sidebar;
- topbar;
- status bar;
- temas;
- distribuição.

Não copie:

- domínio;
- Trial sem revisão;
- processamento de listas;
- textos;
- nomes;
- lógica específica.

---

# 41. Trial

A Trial deve permanecer isolada.

Ao alterar licenciamento:

- teste a edição oficial;
- teste a Trial;
- confirme identificação;
- confirme expiração;
- preserve dados operacionais;
- atualize documentação.

O domínio não deve depender diretamente da Trial.

---

# 42. Desempenho

Operações demoradas não devem bloquear a UI.

Use assíncrono para:

- importação em lote;
- leitura de pasta;
- hashing;
- consulta;
- exportação.

Exiba:

- loading;
- progresso;
- cancelamento quando possível.

Não introduza paralelismo sem testes.

---

# 43. Segurança

Nunca inclua:

- credenciais;
- tokens;
- chaves privadas;
- senhas;
- dados reais;
- banco operacional;
- informações de cliente.

Configurações sensíveis futuras devem usar mecanismos apropriados e não arquivos versionados.

---

# 44. Checklist antes do desenvolvimento

- [ ] Repositório correto.
- [ ] Branch correta.
- [ ] `git status` revisado.
- [ ] Documentação relevante lida.
- [ ] Código existente analisado.
- [ ] Camada correta identificada.
- [ ] Dependências avaliadas.
- [ ] Escopo compreendido.

---

# 45. Checklist antes do commit

- [ ] Build executado.
- [ ] Testes aprovados.
- [ ] Fluxo manual validado.
- [ ] Diff revisado.
- [ ] Sem segredos.
- [ ] Sem dados reais.
- [ ] Sem banco local.
- [ ] Sem `bin` ou `obj`.
- [ ] Documentação atualizada.
- [ ] Mensagem de commit preparada.

---

# 46. Definição de concluído

Uma alteração só está concluída quando:

- funciona;
- está na camada correta;
- possui tratamento de erro;
- possui testes proporcionais;
- não quebra fluxos existentes;
- foi validada manualmente quando necessário;
- está documentada;
- não contém dados sensíveis;
- o diff foi revisado.

---

# 47. Fluxo resumido

```text
Atualizar o repositório
        ↓
Criar branch
        ↓
Analisar arquitetura
        ↓
Implementar
        ↓
Testar
        ↓
Validar manualmente
        ↓
Atualizar documentação
        ↓
Revisar diff
        ↓
Commit
```

---

# 48. Regra final

O desenvolvimento do Nexor deve preservar três prioridades:

```text
Confiabilidade operacional
Clareza arquitetural
Rastreabilidade
```

Uma funcionalidade rápida, mas acoplada, sem testes ou sem persistência confiável, não deve ser considerada concluída.