# Changelog

Todas as alterações relevantes do **Nexor** serão documentadas neste arquivo.

O formato segue as recomendações do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto utiliza versionamento semântico.

---

## [Não lançado]

### Adicionado

- Importação de registros diretamente pela interface.
- Importação de pastas completas.
- Suporte a arrastar e soltar arquivos.
- Fluxo completo de montagem e fechamento de rolos.
- Exportação em PDF completo.
- Exportação em PDF resumido.
- Exportação em JPG espelhado.
- Consulta detalhada de rolos.
- Filtros históricos.
- Reexportação de relatórios.

### Alterado

- Refinamento contínuo da interface e da experiência operacional.
- Ajustes na documentação técnica conforme a implementação evoluir.

### Corrigido

- Correções identificadas durante a validação do fluxo principal.

---

## [0.2.6] - 2026-07-16

### Adicionado

- Nova implementação oficial do Nexor em C#.
- Uso do .NET 8.
- Interface desktop desenvolvida com WPF.
- Arquitetura dividida nos projetos:
  - `Nexor.Desktop`;
  - `Nexor.Application`;
  - `Nexor.Domain`;
  - `Nexor.Infrastructure`;
  - `Nexor.Reporting`.
- Navegação inicial entre:
  - Home;
  - Operação;
  - Rolos;
  - Configurações;
  - Sobre.
- Sidebar lateral.
- Topbar.
- Área central de conteúdo.
- Barra inferior de status.
- Navegação estruturada com MVVM.
- Tema Nexor Dark.
- Tema Nexor Light.
- Tema SISBolt.
- Troca de tema em tempo de execução.
- Persistência da preferência de tema.
- Estrutura inicial das entidades de logs, registros de produção, rolos e eventos.
- Parser inicial para arquivos de log no formato utilizado pelo ecossistema PX.
- Leitura dos campos:
  - `EndTime`;
  - documento;
  - `HeightMM`;
  - `VPositionMM`.
- Cálculo da metragem real por `HeightMM / 1000`.
- Ordenação pela última impressão.
- Agrupamento consecutivo por tecido.
- Identificação de arquivos por SHA-256.
- Prevenção inicial de duplicidade.
- Banco local SQLite.
- Criação automática do banco.
- Controle explícito da versão do schema.
- Repositórios iniciais.
- Testes automatizados de:
  - domínio;
  - aplicação;
  - parsing;
  - persistência.
- Estrutura de build por versão.
- Estrutura inicial de instalador.
- Edição oficial.
- Edição Trial local com período de avaliação de 30 dias.
- Preservação temporária da implementação anterior em:
  - `legacy/Nexor-Python-Legacy`.

### Alterado

- O Nexor deixou de utilizar Python como implementação oficial.
- A implementação principal passou a utilizar C#, .NET 8, WPF e SQLite.
- O PXPrintLogs e o PXSearchOrders passaram a servir como referências funcionais para o novo núcleo.
- O ListForge passou a servir somente como referência de organização visual.
- O código Python anterior foi movido para a área de legado.
- A documentação começou a ser atualizada para refletir a reconstrução em C#.
- A seleção visual de itens ativos e inativos foi ajustada para melhorar a legibilidade.

### Corrigido

- Contraste incorreto entre estados selecionados, ativos e inativos na interface.
- Referências quebradas de screenshots no README.
- Links para imagens inexistentes foram removidos temporariamente.
- O README passou a informar de forma explícita que os screenshots serão adicionados somente após a validação visual da interface.

### Segurança

- O banco do Projeto Jocasta não é modificado pelo Nexor.
- A aplicação utiliza banco próprio armazenado em `%LOCALAPPDATA%\Nexor`.
- A identificação de duplicidade utiliza SHA-256.
- O repositório não deve conter tokens, senhas, chaves privadas ou dados reais de produção.

### Limitações conhecidas

- A importação pela interface ainda não está completa.
- O fluxo de fechamento de rolos ainda está em desenvolvimento.
- PDF completo, PDF resumido e JPG espelhado ainda não estão finalizados.
- A consulta histórica ainda está parcialmente implementada.
- A reexportação ainda não está concluída.
- O instalador ainda precisa ser validado em ambiente limpo.
- Ainda não existem screenshots oficiais da nova interface.

---

## Histórico anterior

As versões anteriores à `0.2.6` devem ser recuperadas a partir do histórico real de commits, tags, releases e artefatos do repositório.

Não devem ser adicionadas versões ou alterações retroativas sem evidência no histórico do projeto.

---

## Tipos de alteração

Este changelog utiliza as seguintes categorias:

- **Adicionado** para novas funcionalidades.
- **Alterado** para mudanças em funcionalidades existentes.
- **Obsoleto** para funcionalidades que serão removidas futuramente.
- **Removido** para funcionalidades eliminadas.
- **Corrigido** para correções de falhas.
- **Segurança** para correções ou melhorias relacionadas à segurança.

---

## Versionamento

O Nexor utiliza o formato:

```text
MAJOR.MINOR.PATCH
```

Exemplo:

```text
0.2.6
```

- **MAJOR**: alterações incompatíveis ou grandes mudanças de produto.
- **MINOR**: novas funcionalidades compatíveis.
- **PATCH**: correções e ajustes menores.

Enquanto o projeto permanecer abaixo da versão `1.0.0`, a arquitetura, os fluxos e os contratos internos ainda poderão sofrer mudanças significativas.

---

## Links

- [README](README.md)
- [Licença](LICENSE.md)
- [Arquitetura](docs/architecture.md)
- [Modelo de dados](docs/Data_Model.md)
- [Especificação funcional](docs/Functional_Spec_Operational_Core.md)
- [Roadmap](docs/roadmap.md)
- [Instalação](docs/installation.md)