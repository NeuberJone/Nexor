# Nexor — Roadmap

## 1. Objetivo

Este documento organiza a evolução do **Nexor** a partir da implementação oficial em:

- C#;
- .NET 8;
- WPF;
- SQLite;
- Windows x64.

O roadmap deve orientar o desenvolvimento por maturidade funcional, evitando adicionar módulos avançados antes da estabilização do núcleo operacional.

A prioridade central é concluir o ciclo:

```text
Importar
→ revisar
→ montar rolo
→ fechar
→ exportar
→ consultar
→ reexportar
```

---

# 2. Direção do produto

O Nexor é uma plataforma desktop local-first para operação, rastreabilidade e consulta de produção têxtil.

O produto deve crescer nesta ordem:

```text
Base técnica
    ↓
Importação confiável
    ↓
Operação
    ↓
Fechamento de rolos
    ↓
Exportação
    ↓
Consulta e auditoria
    ↓
Cadastros
    ↓
Planejamento
    ↓
Estoque
    ↓
Analytics
    ↓
Evolução híbrida
```

---

# 3. Princípios de priorização

## 3.1 Operação antes de expansão

Nenhum módulo futuro deve ganhar prioridade sobre o fluxo operacional principal enquanto ainda houver falhas em:

- importação;
- fechamento;
- persistência;
- exportação;
- consulta;
- reexportação.

---

## 3.2 Funcionalidade real antes de tela vazia

Não devem ser adicionadas telas apenas para simular avanço.

Uma tela só deve entrar na navegação quando possuir:

- caso de uso definido;
- dados reais;
- comportamento funcional;
- validação;
- tratamento de erro;
- persistência quando necessária.

---

## 3.3 Base local antes de serviços online

O Nexor deve permanecer funcional sem internet.

Sincronização, backup remoto e multiestação são expansões futuras e opcionais.

---

## 3.4 Dados confiáveis antes de métricas

Analytics só deve ser desenvolvido quando os dados operacionais estiverem consistentes.

Métricas sobre uma base incompleta ou contraditória geram decisões erradas.

---

# 4. Estado atual

Versão atual:

```text
0.2.6
```

## Implementado ou parcialmente implementado

- solução em C#;
- .NET 8;
- WPF;
- SQLite;
- arquitetura em camadas;
- projetos Desktop, Application, Domain, Infrastructure e Reporting;
- shell principal;
- sidebar;
- topbar;
- barra de status;
- navegação MVVM;
- Home;
- Operação;
- Rolos;
- Configurações;
- Sobre;
- temas Nexor Dark, Nexor Light e SISBolt;
- persistência de tema;
- entidades iniciais;
- parser inicial;
- leitura de `EndTime`;
- leitura de `Document`;
- leitura de `HeightMM`;
- leitura de `VPositionMM`;
- cálculo de metragem;
- ordenação;
- agrupamento consecutivo por tecido;
- fingerprint SHA-256;
- prevenção inicial de duplicidade;
- criação automática do SQLite;
- versão de schema;
- repositórios iniciais;
- testes iniciais;
- estrutura de build;
- estrutura de instalador;
- edição oficial;
- edição Trial local;
- preservação do legado Python.

## Ainda incompleto

- importação funcional completa pela interface;
- importação de pasta;
- drag and drop;
- seleção operacional;
- revisão do rolo;
- fechamento transacional completo;
- PDF completo;
- PDF resumido;
- JPG espelhado;
- consulta histórica completa;
- filtros;
- eventos;
- reexportação;
- validação do instalador em ambiente limpo.

---

# 5. Visão por fases

| Fase | Nome | Estado |
|---|---|---|
| 0 | Fundação e reconstrução em C# | Em consolidação |
| 1 | Importação operacional | Em andamento |
| 2 | Montagem e fechamento de rolos | Pendente |
| 3 | Exportação | Pendente |
| 4 | Consulta e auditoria | Parcial |
| 5 | MVP operacional | Pendente |
| 6 | Cadastros estruturados | Planejado |
| 7 | Planejamento de produção | Planejado |
| 8 | Estoque | Planejado |
| 9 | Analytics | Planejado |
| 10 | Evolução híbrida | Futuro |

---

# 6. Fase 0 — Fundação e reconstrução em C#

## Objetivo

Substituir a implementação principal anterior por uma base organizada em C# e WPF.

## Entregas

- solução `.sln`;
- projetos separados;
- arquitetura em camadas;
- shell WPF;
- navegação;
- temas;
- configurações;
- SQLite;
- testes;
- documentação inicial;
- build versionado;
- preservação do legado.

## Estado

```text
Avançado
```

## Falta concluir

- alinhar toda a documentação;
- consolidar convenções;
- revisar dependências entre projetos;
- eliminar acoplamentos desnecessários;
- validar migrations;
- estabilizar logging;
- validar build limpo;
- validar instalador.

## Critério de saída

A fase será considerada concluída quando:

- a solução compilar sem erro;
- todos os testes passarem;
- a navegação funcionar;
- o banco for criado corretamente;
- o projeto puder ser executado em ambiente limpo;
- a documentação refletir a arquitetura real.

---

# 7. Fase 1 — Importação operacional

## Objetivo

Permitir que o operador importe registros reais pela interface.

## Entregas

- importar um ou vários arquivos;
- importar pasta;
- arrastar e soltar;
- escolher máquina;
- calcular fingerprint;
- detectar duplicidade;
- interpretar os arquivos;
- persistir logs e itens;
- exibir resumo da importação;
- listar itens disponíveis;
- destacar inválidos e suspeitos;
- manter importação incremental.

## Regras principais

- `HeightMM / 1000`;
- `VPositionMM` não entra na metragem;
- ordenação por `EndTime` decrescente;
- último impresso primeiro;
- tecido extraído do documento;
- arquivo duplicado não gera novo item;
- erro em um arquivo não invalida todo o lote.

## Critério de saída

- arquivos reais são importados pela interface;
- duplicidades são detectadas;
- registros inválidos são explicados;
- itens persistem após reiniciar;
- testes cobrem o fluxo;
- a interface não trava em lotes comuns.

---

# 8. Fase 2 — Montagem e fechamento de rolos

## Objetivo

Transformar os itens importados em um rolo operacional persistido.

## Entregas

- seleção múltipla;
- filtros;
- resumo em tempo real;
- agrupamento consecutivo por tecido;
- quantidade por bloco;
- metragem por bloco;
- metragem total;
- identificação automática do rolo;
- revisão;
- validações;
- fechamento transacional;
- vínculo dos itens;
- evento de fechamento;
- recuperação após reiniciar.

## Regras principais

- rolo vazio não pode ser fechado;
- itens inválidos não podem entrar;
- itens já vinculados não podem ser reutilizados;
- mistura de máquinas deve ser tratada;
- composição é congelada após fechamento;
- totais devem ser recalculados pelo domínio;
- a UI não é fonte de verdade.

## Critério de saída

- um rolo pode ser montado;
- revisado;
- fechado;
- persistido;
- recuperado;
- consultado após reiniciar;
- sem inconsistência parcial em caso de falha.

---

# 9. Fase 3 — Exportação

## Objetivo

Gerar os arquivos operacionais do rolo fechado.

## Entregas

- PDF completo;
- PDF resumido;
- JPG espelhado;
- largura de 17 cm;
- largura de 21 cm;
- largura personalizada;
- DPI configurável;
- nomes versionados;
- prevenção de sobrescrita;
- registro de exportação;
- evento de exportação;
- abertura da pasta final.

## PDF completo

Deve conter:

- código;
- máquina;
- data;
- itens;
- horários;
- documentos;
- tecidos;
- metragens;
- blocos;
- resumo;
- total geral.

## PDF resumido

Deve conter:

- código;
- máquina;
- blocos;
- quantidade;
- metragem por bloco;
- total geral.

## JPG espelhado

Deve:

- ser realmente espelhado;
- preservar proporção;
- respeitar largura;
- respeitar DPI;
- gerar arquivo válido;
- não sobrescrever exportações anteriores.

## Critério de saída

- os três formatos são gerados;
- os relatórios usam dados persistidos;
- os arquivos são registrados;
- reexecuções criam nova versão;
- falhas não alteram o rolo.

---

# 10. Fase 4 — Consulta e auditoria

## Objetivo

Permitir localizar, abrir e conferir rolos históricos.

## Entregas

- lista de rolos;
- filtro por máquina;
- filtro por período;
- busca por código;
- busca por documento;
- busca por tecido;
- limite de resultados;
- resumo;
- itens;
- blocos;
- eventos;
- exportações;
- cópia do código;
- reexportação.

## Critério de saída

- qualquer rolo pode ser localizado rapidamente;
- a composição é reconstruída pelo banco;
- itens e eventos são exibidos;
- relatórios podem ser reexportados;
- os arquivos originais não são necessários para reexportar.

---

# 11. Fase 5 — MVP operacional

## Objetivo

Entregar a primeira versão realmente utilizável no ambiente de produção.

## Escopo obrigatório

```text
Importar
→ montar
→ revisar
→ fechar
→ exportar
→ consultar
→ reexportar
```

## Requisitos adicionais

- instalador;
- atualização preservando dados;
- tratamento de erros;
- logs técnicos;
- configurações;
- manual;
- screenshots;
- testes;
- build oficial;
- Trial validada;
- validação em computador limpo;
- validação com registros reais.

## Critério de saída

O MVP será considerado pronto quando um operador conseguir:

1. instalar;
2. abrir;
3. configurar;
4. importar registros;
5. montar um rolo;
6. fechar;
7. gerar os arquivos;
8. fechar o aplicativo;
9. abrir novamente;
10. localizar o rolo;
11. reexportar;
12. concluir tudo sem utilizar scripts externos.

---

# 12. Fase 6 — Cadastros estruturados

## Objetivo

Reduzir dependência de textos soltos.

## Entregas

- máquinas;
- operadores;
- tecidos;
- aliases;
- status ativo e inativo;
- busca;
- criação;
- edição;
- validação;
- integração com a operação.

## Critério de saída

- tecidos são normalizados por cadastro;
- aliases funcionam;
- máquinas são mantidas na aplicação;
- operadores podem ser associados;
- alterações não corrompem registros históricos.

---

# 13. Fase 7 — Planejamento de produção

## Objetivo

Organizar a produção antes da execução.

## Entregas

- fila;
- agrupamento por tecido;
- ordenação;
- capacidade por rolo;
- gaps;
- estimativa de metragem;
- estimativa de tempo;
- blocos previstos;
- plano salvo;
- integração futura com operação.

## Dependências

Essa fase depende de:

- operação estável;
- tecidos normalizados;
- histórico confiável;
- métricas corretas.

## Critério de saída

- uma fila pode ser criada;
- reorganizada;
- salva;
- calculada;
- usada como referência para a operação.

---

# 14. Fase 8 — Estoque

## Objetivo

Controlar disponibilidade de tecido.

## Entregas

- cadastro de rolos;
- cadastro de pedaços;
- metragem disponível;
- status;
- ajustes;
- consumo;
- histórico;
- vínculo com planejamento;
- vínculo com produção confirmada.

## Dependências

- cadastro de tecidos;
- planejamento;
- regras de consumo;
- operação estável.

## Critério de saída

- saldo pode ser consultado;
- consumo pode ser registrado;
- disponibilidade pode apoiar planejamento;
- histórico permanece auditável.

---

# 15. Fase 9 — Analytics

## Objetivo

Transformar dados operacionais em indicadores confiáveis.

## Entregas

- produção por máquina;
- metros por período;
- duração média por metro;
- quantidade de rolos;
- quantidade de registros;
- comparação entre períodos;
- eficiência;
- padrões de tecido;
- alertas;
- exportação de indicadores.

## Dependências

- histórico consistente;
- datas corretas;
- máquinas corretas;
- metragens confiáveis;
- volume suficiente de dados.

## Critério de saída

- indicadores refletem dados reais;
- filtros funcionam;
- métricas são explicáveis;
- valores podem ser auditados.

---

# 16. Fase 10 — Evolução híbrida

## Objetivo

Adicionar recursos online sem comprometer o funcionamento local.

## Possibilidades

- backup remoto;
- sincronização opcional;
- consolidação entre estações;
- painel central;
- diagnóstico remoto;
- atualização assistida;
- controle de licença;
- compartilhamento de métricas.

## Regras

- o banco local continua sendo a base operacional;
- internet não pode ser obrigatória para fechar rolos;
- falha online não pode bloquear a produção;
- sincronização deve ser auditável;
- conflitos devem ser tratados explicitamente.

---

# 17. Roadmap por versões sugeridas

As versões abaixo são metas sugeridas e podem ser ajustadas conforme a implementação real.

## 0.2.x — Fundação

- arquitetura;
- shell;
- temas;
- parser;
- banco;
- testes;
- documentação.

## 0.3.0 — Importação pela interface

- arquivos;
- pasta;
- drag and drop;
- duplicidade;
- tabela;
- resumo.

## 0.4.0 — Montagem do rolo

- seleção;
- filtros;
- blocos;
- totais;
- revisão.

## 0.5.0 — Fechamento persistido

- transação;
- vínculos;
- eventos;
- recuperação histórica.

## 0.6.0 — Exportação

- PDF completo;
- PDF resumido;
- JPG espelhado;
- registro de exportações.

## 0.7.0 — Consulta

- filtros;
- detalhes;
- itens;
- eventos;
- exportações.

## 0.8.0 — Reexportação e auditoria

- reexportação;
- histórico;
- revisão;
- melhorias de consulta.

## 0.9.0 — Validação operacional

- testes reais;
- correções;
- desempenho;
- instalador;
- atualização;
- documentação;
- screenshots.

## 1.0.0 — Primeira versão estável

- fluxo completo;
- instalação validada;
- dados preservados;
- relatórios confiáveis;
- consulta funcional;
- documentação completa.

---

# 18. Critérios para a versão 1.0.0

A versão 1.0.0 exige:

- importação funcional;
- duplicidade correta;
- parsing confiável;
- montagem;
- fechamento transacional;
- persistência;
- PDF completo;
- PDF resumido;
- JPG espelhado;
- consulta;
- eventos;
- reexportação;
- configurações;
- logs;
- instalador;
- atualização;
- testes;
- manual;
- screenshots;
- validação em ambiente real.

Não é necessário para a versão 1.0.0:

- Planejamento;
- Estoque;
- Analytics;
- sincronização;
- multiestação.

Esses módulos não devem atrasar o primeiro produto operacional estável.

---

# 19. Backlog técnico

Itens técnicos que devem acompanhar as fases:

- logging estruturado;
- tratamento global de exceções;
- navegação centralizada;
- async e cancelamento;
- migrations;
- backup antes de migrations;
- testes de integração;
- acessibilidade;
- contraste;
- mensagens claras;
- desempenho de DataGrid;
- paginação ou limite;
- validação de caminhos;
- prevenção de múltiplas instâncias, se necessário;
- integridade dos arquivos exportados;
- assinatura digital futura.

---

# 20. Backlog de documentação

- README;
- LICENSE;
- CHANGELOG;
- arquitetura;
- modelo de dados;
- especificação funcional;
- instalação;
- UI/UX;
- wireframes;
- screenshots;
- manual;
- processo de build;
- processo de release;
- estrutura do projeto;
- referências e legado.

---

# 21. Riscos atuais

## Risco 1 — Avançar a UI antes do núcleo

Uma interface visualmente completa pode esconder fluxos ainda frágeis.

## Risco 2 — Copiar arquitetura do legado

O código Python deve ser referência funcional, não modelo estrutural.

## Risco 3 — Copiar demais o ListForge

O ListForge deve ser referência visual, não base de domínio.

## Risco 4 — Documentação divergente

Documentos devem refletir o código atual, não apenas a visão futura.

## Risco 5 — Trial misturada ao núcleo

A Trial deve permanecer isolada da operação e do banco principal.

## Risco 6 — Expandir cedo demais

Planejamento e Estoque não devem competir com o fechamento de rolos.

---

# 22. Regra de conclusão de fase

Uma fase não deve ser marcada como concluída apenas porque:

- uma tela existe;
- um botão existe;
- uma classe foi criada;
- um método retorna dados simulados.

Uma fase só é concluída quando:

- o fluxo funciona;
- os dados são reais;
- há validações;
- erros são tratados;
- testes cobrem regras;
- documentação está atualizada;
- o comportamento foi validado.

---

# 23. Atualização deste roadmap

Este documento deve ser atualizado quando:

- uma fase mudar de status;
- uma nova versão for lançada;
- um marco for concluído;
- uma dependência mudar;
- o escopo da versão 1.0.0 mudar;
- um módulo futuro entrar em desenvolvimento.

Cada release deve atualizar:

- `README.md`;
- `CHANGELOG.md`;
- este roadmap;
- versão;
- manual, quando aplicável.

---

# 24. Próxima prioridade

A prioridade imediata é concluir:

```text
Fase 1 — Importação operacional
```

Em seguida:

```text
Fase 2 — Montagem e fechamento
```

Depois:

```text
Fase 3 — Exportação
```

E então:

```text
Fase 4 — Consulta e reexportação
```

---

# 25. Síntese

O Nexor não deve ser medido pela quantidade de telas ou módulos.

O progresso real deve ser medido pela confiabilidade do ciclo operacional:

```text
Importar corretamente.
Fechar corretamente.
Persistir corretamente.
Exportar corretamente.
Consultar corretamente.
Reexportar corretamente.
```

Somente depois disso o projeto deve avançar para Planejamento, Estoque, Analytics e recursos híbridos.