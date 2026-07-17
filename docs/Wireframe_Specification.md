# Nexor — Especificação de Wireframes

## 1. Objetivo

Este documento define a estrutura visual das principais telas do **Nexor** antes do refinamento gráfico final.

Os wireframes devem orientar:

- distribuição dos blocos;
- hierarquia das informações;
- posição das ações;
- relação entre listas e painéis;
- comportamento de navegação;
- estados vazios;
- carregamento;
- erros;
- responsividade em desktop.

O objetivo não é definir cores, ícones ou identidade visual final.

A identidade e os estilos devem seguir a documentação de UI/UX e os temas da aplicação.

---

# 2. Escopo atual

Os wireframes desta etapa cobrem:

- estrutura principal da aplicação;
- Home;
- Operação;
- importação;
- revisão do rolo;
- resultado do fechamento;
- Rolos;
- detalhes do rolo;
- Configurações;
- Sobre;
- mensagens e estados comuns.

Não entram como telas funcionais nesta etapa:

- Cadastros;
- Planejamento;
- Estoque;
- Analytics;
- sincronização;
- administração multiestação.

Esses módulos podem ser representados futuramente em documentos próprios.

---

# 3. Estrutura principal

O Nexor utiliza uma estrutura desktop com quatro áreas principais:

```text
┌──────────────────┬──────────────────────────────────────────┐
│                  │ Topbar                                   │
│                  ├──────────────────────────────────────────┤
│ Sidebar          │                                          │
│                  │ Conteúdo principal                       │
│                  │                                          │
│                  │                                          │
│                  ├──────────────────────────────────────────┤
│                  │ Barra de status                          │
└──────────────────┴──────────────────────────────────────────┘
```

## Dimensões iniciais sugeridas

```text
Largura mínima da janela: 1320 px
Altura mínima da janela: 780 px
Sidebar: 210 px
Topbar: 58 px
Barra de status: 28 px
```

As medidas podem ser ajustadas após testes reais.

---

# 4. Sidebar

## Estrutura

```text
┌────────────────────┐
│ Logo Nexor         │
│ Produção têxtil    │
│                    │
│ Home               │
│ Operação           │
│ Rolos              │
│                    │
│ Configurações      │
│ Sobre              │
│                    │
│                    │
│ Versão X.Y.Z       │
└────────────────────┘
```

## Regras

- o item ativo deve ser claramente destacado;
- o texto deve permanecer legível;
- itens futuros não devem aparecer como funcionais;
- Configurações e Sobre podem ficar separados visualmente das telas operacionais;
- a versão pode aparecer na parte inferior;
- a navegação deve permanecer disponível em todas as telas principais.

---

# 5. Topbar

## Estrutura padrão

```text
┌─────────────────────────────────────────────────────────────┐
│ Título da tela                  Ações contextuais           │
│ Subtítulo ou contexto breve                                │
└─────────────────────────────────────────────────────────────┘
```

## Exemplos

### Home

```text
Home
Visão geral da operação
```

### Operação

```text
Operação
18 registros disponíveis

[Importar arquivos] [Importar pasta] [Atualizar]
```

### Rolos

```text
Rolos
Consulta histórica

[Atualizar] [Limpar filtros]
```

---

# 6. Barra de status

## Estrutura

```text
┌─────────────────────────────────────────────────────────────┐
│ Mensagem recente                                  Estado DB │
└─────────────────────────────────────────────────────────────┘
```

## Conteúdo possível

- arquivos importados;
- tema alterado;
- rolo fechado;
- caminho de exportação;
- erro de configuração;
- banco conectado;
- versão do schema.

A barra não deve substituir mensagens de erro importantes.

---

# 7. Wireframe da Home

## Objetivo

Permitir que o usuário entenda rapidamente o estado atual do Nexor.

## Estrutura

```text
┌──────────────────────────────────────────────────────────────┐
│ Home                                                         │
│ Visão geral da operação                                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐     │
│ │ Registros      │ │ Rolos fechados │ │ Alertas        │     │
│ │ disponíveis    │ │ hoje           │ │                │     │
│ │      18        │ │       3        │ │       1        │     │
│ └────────────────┘ └────────────────┘ └────────────────┘     │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Último rolo                                             │ │
│ │ M1_16-07-2026_153045                                    │ │
│ │ 24 itens · 48,35 m                                      │ │
│ │                                      [Abrir detalhes]   │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Ações rápidas                                           │ │
│ │ [Ir para Operação] [Importar arquivos] [Consultar rolos]│ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Atividade recente                                       │ │
│ │ • 12 arquivos importados                                │ │
│ │ • Rolo M1_... fechado                                   │ │
│ │ • PDF exportado                                         │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Hierarquia

1. ação principal;
2. registros disponíveis;
3. alertas;
4. último rolo;
5. atividade recente.

## Estado vazio

```text
Nenhum registro foi importado ainda.

Importe os primeiros arquivos para iniciar a operação.

[Importar arquivos]
```

---

# 8. Wireframe da Operação

## Objetivo

Importar, visualizar, filtrar e selecionar os registros que compõem o rolo atual.

## Estrutura principal

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Operação                                                            │
│ 18 registros disponíveis                                            │
│                                  [Importar arquivos] [Importar pasta]│
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌──────────────────────────────────────┬────────────────────────────┐ │
│ │ Filtros                              │ Rolo atual                 │ │
│ │                                      │                            │ │
│ │ Máquina [Todas ▼]                    │ Código                     │ │
│ │ Tecido  [Todos ▼]                    │ M1_16-07-2026_153045       │ │
│ │ Status  [Disponíveis ▼]              │                            │ │
│ │ Busca   [________________________]    │ Máquina: M1                │ │
│ │                                      │ Itens: 12                  │ │
│ │ [Limpar filtros]                     │ Blocos: 3                  │ │
│ ├──────────────────────────────────────┤ Metragem: 28,42 m          │ │
│ │                                      │                            │ │
│ │ Tabela de registros                  │ Tecidos                    │ │
│ │                                      │ Dryfit                     │ │
│ │ □ Hora | Documento | Tecido | Metro  │ Elastano                   │ │
│ │ □ ...                                │                            │ │
│ │ ☑ ...                                │ Alertas                    │ │
│ │ ☑ ...                                │ Nenhum alerta bloqueante   │ │
│ │ □ ...                                │                            │ │
│ │                                      │ [Limpar seleção]           │ │
│ │                                      │ [Revisar rolo]             │ │
│ └──────────────────────────────────────┴────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

## Proporção sugerida

```text
Área principal: 72%
Painel lateral: 28%
```

O painel lateral deve manter largura mínima suficiente para leitura.

---

# 9. Barra de filtros da Operação

## Estrutura

```text
┌─────────────────────────────────────────────────────────────┐
│ Máquina        Tecido         Status         Período         │
│ [Todas ▼]      [Todos ▼]      [Prontos ▼]    [Hoje ▼]       │
│                                                             │
│ Buscar [__________________________________________]          │
│                                           [Limpar filtros]   │
└─────────────────────────────────────────────────────────────┘
```

## Regras

- filtros simples;
- aplicação rápida;
- botão para limpeza;
- busca textual com debounce;
- filtros não devem ocupar altura excessiva;
- estados aplicados devem permanecer visíveis.

---

# 10. Tabela da Operação

## Estrutura sugerida

```text
┌───┬──────────┬──────────────────────────────┬─────────┬──────┬──────────┐
│   │ Horário  │ Documento                    │ Tecido  │ Metr.│ Status   │
├───┼──────────┼──────────────────────────────┼─────────┼──────┼──────────┤
│ □ │ 15:30:45 │ 16-07 - Dryfit - Pedido A   │ Dryfit  │ 6,37 │ Pronto   │
│ ☑ │ 15:21:12 │ 16-07 - Dryfit - Pedido B   │ Dryfit  │ 4,25 │ Selecion.│
│ □ │ 15:11:03 │ 16-07 - Elastano - Pedido C │ Elastano│ 3,94 │ Suspeito │
└───┴──────────┴──────────────────────────────┴─────────┴──────┴──────────┘
```

## Comportamentos

- checkbox independente da seleção visual da linha;
- cabeçalho fixo;
- documento com tooltip;
- linha inválida desabilitada;
- linha suspeita destacada;
- duplo clique abre detalhes;
- seleção atualiza painel lateral;
- ordenação padrão por horário decrescente.

---

# 11. Estado vazio da Operação

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  Nenhum registro disponível                 │
│                                                             │
│      Importe arquivos ou uma pasta para começar.            │
│                                                             │
│             [Importar arquivos] [Importar pasta]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 12. Estado de carregamento da Operação

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  Importando arquivos...                     │
│                                                             │
│                     [ Indicador ]                           │
│                                                             │
│                 12 de 48 processados                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A tabela pode permanecer visível com bloqueio parcial.

---

# 13. Resultado da importação

## Modal sugerido

```text
┌───────────────────────────────────────────────┐
│ Importação concluída                         │
├───────────────────────────────────────────────┤
│                                               │
│ Importados                         18         │
│ Duplicados                         3          │
│ Inválidos                          1          │
│ Ignorados                          0          │
│                                               │
│ [Ver inválidos]                    [Fechar]   │
└───────────────────────────────────────────────┘
```

## Regras

- não exigir modal quando todos forem importados sem problema, caso a barra de status seja suficiente;
- mostrar detalhes quando houver inválidos;
- permitir copiar o resumo;
- não expor stack trace.

---

# 14. Detalhes de um registro

## Painel ou modal

```text
┌──────────────────────────────────────────────────────┐
│ Detalhes do registro                                │
├──────────────────────────────────────────────────────┤
│ Documento                                           │
│ 16-07 - Dryfit - Pedido A.jpeg                      │
│                                                     │
│ Arquivo                                             │
│ C:\...\arquivo.txt                                  │
│                                                     │
│ EndTime                 16/07/2026 15:30:45         │
│ Máquina                 M1                          │
│ Tecido                  Dryfit                      │
│ HeightMM                6361                        │
│ VPositionMM             1000                        │
│ Metragem                6,361 m                     │
│ Status                  Pronto                      │
│                                                     │
│ [Copiar caminho]                         [Fechar]   │
└──────────────────────────────────────────────────────┘
```

---

# 15. Wireframe de revisão do rolo

## Objetivo

Apresentar uma confirmação clara antes do fechamento.

## Estrutura

```text
┌────────────────────────────────────────────────────────────────┐
│ Revisar rolo                                                   │
│ 12 itens · 28,42 m                                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌────────────────────────────┬────────────────────────────────┐ │
│ │ Dados do rolo              │ Resumo                         │ │
│ │                            │                                │ │
│ │ Código                     │ Itens              12          │ │
│ │ [M1_16-07-2026_153045___]  │ Blocos             3          │ │
│ │                            │ Metragem            28,42 m    │ │
│ │ Máquina                    │ Primeiro horário    14:42:10   │ │
│ │ [M1 ▼]                     │ Último horário      15:30:45   │ │
│ │                            │                                │ │
│ │ Observações                │ Tecidos                        │ │
│ │ [_______________________]  │ Dryfit                         │ │
│ │ [_______________________]  │ Elastano                       │ │
│ └────────────────────────────┴────────────────────────────────┘ │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Blocos                                                     │ │
│ │                                                            │ │
│ │ Bloco 1 · Dryfit    5 itens     12,30 m                    │ │
│ │ Bloco 2 · Elastano  4 itens      9,42 m                    │ │
│ │ Bloco 3 · Dryfit    3 itens      6,70 m                    │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Itens resumidos                                            │ │
│ │ Hora | Documento | Tecido | Metragem                       │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                │
│ [Voltar] [Cancelar]               [Confirmar fechamento]      │
└────────────────────────────────────────────────────────────────┘
```

---

# 16. Confirmação de fechamento

```text
┌───────────────────────────────────────────────┐
│ Confirmar fechamento?                        │
├───────────────────────────────────────────────┤
│                                               │
│ A composição deste rolo será preservada no   │
│ histórico após a confirmação.                │
│                                               │
│ Código: M1_16-07-2026_153045                 │
│ Itens: 12                                    │
│ Metragem: 28,42 m                            │
│                                               │
│ [Cancelar]                [Confirmar]         │
└───────────────────────────────────────────────┘
```

A ação principal deve ser visualmente evidente, mas não perigosa.

---

# 17. Resultado do fechamento

```text
┌──────────────────────────────────────────────────────┐
│ Rolo fechado com sucesso                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ M1_16-07-2026_153045                                 │
│                                                      │
│ Máquina                  M1                          │
│ Itens                    12                          │
│ Metragem                 28,42 m                     │
│ Fechado em               16/07/2026 15:35           │
│                                                      │
│ Exportações                                          │
│ □ PDF completo                                       │
│ □ PDF resumido                                       │
│ □ JPG espelhado                                      │
│                                                      │
│ [Ir para Rolos] [Novo rolo] [Exportar selecionados] │
└──────────────────────────────────────────────────────┘
```

---

# 18. Wireframe da tela Rolos

## Objetivo

Pesquisar e consultar rolos registrados.

## Estrutura

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Rolos                                                               │
│ Consulta histórica                                                  │
│                                         [Atualizar] [Limpar filtros] │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌──────────────────────────────────────┬────────────────────────────┐ │
│ │ Filtros                              │ Detalhes                   │ │
│ │                                      │                            │ │
│ │ Período  [Últimos 30 dias ▼]         │ Selecione um rolo          │ │
│ │ Máquina  [Todas ▼]                   │ para ver os detalhes.      │ │
│ │ Tecido   [Todos ▼]                   │                            │ │
│ │ Status   [Todos ▼]                   │                            │ │
│ │ Código   [____________________]       │                            │ │
│ │ Pedido   [____________________]       │                            │ │
│ │ Limite   [300]                       │                            │ │
│ ├──────────────────────────────────────┤                            │ │
│ │ Lista de rolos                       │                            │ │
│ │                                      │                            │ │
│ │ Código | Data | Máquina | Itens | m  │                            │ │
│ │ ...                                  │                            │ │
│ └──────────────────────────────────────┴────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

# 19. Tabela de rolos

```text
┌──────────────────────────┬────────────┬─────────┬───────┬──────────┬──────────┐
│ Código                   │ Data       │ Máquina │ Itens │ Metragem │ Status   │
├──────────────────────────┼────────────┼─────────┼───────┼──────────┼──────────┤
│ M1_16-07-2026_153045     │ 16/07/2026 │ M1      │ 12    │ 28,42 m  │ Exportado│
│ M2_16-07-2026_142050     │ 16/07/2026 │ M2      │ 18    │ 45,17 m  │ Fechado  │
└──────────────────────────┴────────────┴─────────┴───────┴──────────┴──────────┘
```

## Regras

- seleção única;
- painel de detalhes atualizado ao selecionar;
- código copiável;
- status com badge;
- ordenação por data decrescente;
- carregamento progressivo quando necessário.

---

# 20. Painel de detalhes do rolo

## Estrutura

```text
┌──────────────────────────────────────────┐
│ M1_16-07-2026_153045                    │
│ Exportado                               │
├──────────────────────────────────────────┤
│ Máquina              M1                 │
│ Data                 16/07/2026         │
│ Itens                12                 │
│ Metragem             28,42 m            │
│ Blocos               3                  │
│                                          │
│ [Copiar código] [Abrir pasta]            │
├──────────────────────────────────────────┤
│ [Resumo] [Itens] [Eventos] [Exportações] │
├──────────────────────────────────────────┤
│ Conteúdo da aba                           │
│                                          │
│                                          │
├──────────────────────────────────────────┤
│ [Reexportar ▼]                            │
└──────────────────────────────────────────┘
```

---

# 21. Aba Resumo

```text
┌───────────────────────────────────────┐
│ Resumo                                │
│                                       │
│ Código        M1_16-07-2026_153045    │
│ Máquina       M1                      │
│ Fechado em    16/07/2026 15:35        │
│ Itens         12                      │
│ Metragem      28,42 m                 │
│                                       │
│ Blocos                                │
│ 1. Dryfit — 5 itens — 12,30 m         │
│ 2. Elastano — 4 itens — 9,42 m        │
│ 3. Dryfit — 3 itens — 6,70 m          │
└───────────────────────────────────────┘
```

---

# 22. Aba Itens

```text
┌──────────┬──────────────────────────────┬──────────┬─────────┐
│ Horário  │ Documento                    │ Tecido   │ Metragem│
├──────────┼──────────────────────────────┼──────────┼─────────┤
│ 15:30:45 │ Pedido A                     │ Dryfit   │ 6,37 m  │
│ 15:21:12 │ Pedido B                     │ Dryfit   │ 4,25 m  │
└──────────┴──────────────────────────────┴──────────┴─────────┘
```

---

# 23. Aba Eventos

```text
┌──────────────────┬───────────────────┬──────────────────────────────┐
│ Data             │ Tipo              │ Descrição                    │
├──────────────────┼───────────────────┼──────────────────────────────┤
│ 16/07 15:35      │ Fechamento        │ Rolo fechado                │
│ 16/07 15:36      │ PDF exportado     │ PDF completo gerado         │
│ 16/07 15:37      │ JPG exportado     │ JPG espelhado gerado        │
└──────────────────┴───────────────────┴──────────────────────────────┘
```

---

# 24. Aba Exportações

```text
┌──────────────┬──────────┬───────────────┬────────────────────────────┐
│ Tipo         │ Modo     │ Data          │ Arquivo                    │
├──────────────┼──────────┼───────────────┼────────────────────────────┤
│ PDF          │ Completo │ 16/07 15:36   │ arquivo_FULL.pdf           │
│ PDF          │ Resumo   │ 16/07 15:36   │ arquivo_SUMMARY.pdf        │
│ JPG espelho  │ Completo │ 16/07 15:37   │ arquivo_FULL.jpg           │
└──────────────┴──────────┴───────────────┴────────────────────────────┘
```

Ações por linha:

- abrir arquivo;
- abrir pasta;
- copiar caminho;
- reexportar.

---

# 25. Reexportação

## Modal

```text
┌───────────────────────────────────────────────┐
│ Reexportar rolo                              │
├───────────────────────────────────────────────┤
│                                               │
│ Formato                                       │
│ ○ PDF completo                                │
│ ○ PDF resumido                                │
│ ○ JPG espelhado                               │
│                                               │
│ Largura do JPG                                │
│ [21 cm ▼]                                     │
│                                               │
│ DPI                                           │
│ [300]                                         │
│                                               │
│ Pasta                                         │
│ [C:\...\exports___________________] [Procurar]│
│                                               │
│ [Cancelar]                    [Reexportar]     │
└───────────────────────────────────────────────┘
```

Campos de JPG devem aparecer apenas quando esse formato estiver selecionado.

---

# 26. Estado vazio da tela Rolos

```text
Nenhum rolo encontrado.

Ajuste os filtros ou realize um fechamento na tela Operação.

[Limpar filtros] [Ir para Operação]
```

---

# 27. Wireframe de Configurações

## Estrutura

```text
┌─────────────────────────────────────────────────────────────┐
│ Configurações                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌───────────────┬─────────────────────────────────────────┐ │
│ │ Geral         │ Conteúdo da seção                       │ │
│ │ Pastas        │                                         │ │
│ │ Relatórios    │                                         │ │
│ │ Aparência     │                                         │ │
│ │ Diagnóstico   │                                         │ │
│ └───────────────┴─────────────────────────────────────────┘ │
│                                                             │
│                             [Restaurar] [Salvar alterações] │
└─────────────────────────────────────────────────────────────┘
```

---

# 28. Configurações — Geral

```text
Máquina padrão

[M1 ▼]

Limite de resultados

[300]

Após exportar

☑ Abrir a pasta automaticamente

Confirmações

☑ Confirmar fechamento
☑ Confirmar limpeza da seleção
```

---

# 29. Configurações — Pastas

```text
Pasta de importação

[C:\Produção\Logs__________________] [Procurar] [Testar] [Abrir]

Exportação de PDF

[C:\Nexor\PDF______________________] [Procurar] [Testar] [Abrir]

Exportação de JPG

[C:\Nexor\Mirror___________________] [Procurar] [Testar] [Abrir]
```

Mensagens de validação devem aparecer abaixo de cada caminho.

---

# 30. Configurações — Relatórios

```text
Modo padrão do PDF

[Completo ▼]

Largura do JPG

[21 cm ▼]

Largura personalizada

[________] cm

Resolução

[300] DPI
```

---

# 31. Configurações — Aparência

```text
Tema

○ Nexor Dark
○ Nexor Light
○ SISBolt

Prévia

┌────────────────────────────┐
│ Exemplo de card e botão    │
└────────────────────────────┘
```

A troca pode ser imediata.

---

# 32. Configurações — Diagnóstico

```text
Versão da aplicação        0.2.6
Versão do banco            1
Pasta de dados             C:\Users\...\Nexor
Arquivo do banco           ...\nexor.db
Pasta de logs              ...\logs

[Abrir pasta de dados]
[Abrir logs]
[Copiar informações de suporte]
```

---

# 33. Wireframe da tela Sobre

```text
┌────────────────────────────────────────────────────┐
│                                                    │
│                    Logo Nexor                      │
│                                                    │
│                      Nexor                         │
│                    Versão 0.2.6                    │
│                                                    │
│ Plataforma operacional de produção têxtil         │
│                                                    │
│ C# · .NET 8 · WPF · SQLite                        │
│                                                    │
│ Edição: Oficial                                    │
│                                                    │
│ Autor                                              │
│ Neuber Jone Avelar Queiroz                         │
│                                                    │
│ [Abrir repositório] [Ver licença]                  │
│                                                    │
└────────────────────────────────────────────────────┘
```

Para Trial:

```text
Edição: Trial
Período restante: X dias
```

---

# 34. Mensagem de erro bloqueante

```text
┌───────────────────────────────────────────────┐
│ Não foi possível concluir a operação         │
├───────────────────────────────────────────────┤
│                                               │
│ O banco de dados não pôde ser acessado.       │
│                                               │
│ Verifique se outra instância está utilizando  │
│ o arquivo e tente novamente.                  │
│                                               │
│ [Copiar detalhes]                  [Fechar]   │
└───────────────────────────────────────────────┘
```

---

# 35. Alerta não bloqueante

```text
┌────────────────────────────────────────────────────┐
│ ⚠ 2 registros possuem tecido não identificado.   │
│                                                    │
│ Eles podem ser revisados antes do fechamento.      │
│                                      [Ver itens]   │
└────────────────────────────────────────────────────┘
```

---

# 36. Confirmação para limpar seleção

```text
┌───────────────────────────────────────────────┐
│ Limpar seleção?                              │
├───────────────────────────────────────────────┤
│                                               │
│ Os 12 itens selecionados serão removidos do   │
│ rolo atual.                                   │
│                                               │
│ Nenhum registro será apagado do banco.        │
│                                               │
│ [Cancelar]                  [Limpar seleção]  │
└───────────────────────────────────────────────┘
```

---

# 37. Estados visuais obrigatórios

Os wireframes e componentes devem prever:

- padrão;
- hover;
- foco;
- pressionado;
- selecionado;
- desabilitado;
- carregando;
- erro;
- sucesso;
- alerta;
- vazio.

Todos devem ser testados nos temas:

- Nexor Dark;
- Nexor Light;
- SISBolt.

---

# 38. Responsividade

## Janela larga

- tabela e painel lado a lado;
- filtros em uma linha;
- cards distribuídos.

## Janela próxima ao mínimo

- filtros podem quebrar para duas linhas;
- painel lateral mantém largura mínima;
- conteúdo interno usa scroll;
- botões podem reorganizar;
- tabela preserva as colunas essenciais.

## Regra

O painel lateral não deve ficar estreito a ponto de esconder totais ou ações.

---

# 39. Ordem de tabulação

A navegação por teclado deve seguir:

1. navegação;
2. ações da topbar;
3. filtros;
4. tabela;
5. painel lateral;
6. ação principal.

Em modais:

1. primeiro campo;
2. campos seguintes;
3. ação secundária;
4. ação principal.

---

# 40. Critérios de aceite dos wireframes

Os wireframes estarão aprovados quando responderem claramente:

- onde o usuário começa;
- como importa;
- onde vê os registros;
- como seleciona;
- onde acompanha totais;
- como revisa;
- como fecha;
- onde exporta;
- como consulta;
- como reexporta;
- onde configura;
- como recebe erros;
- como identifica estados.

---

# 41. Estado de implementação

## Implementado ou parcialmente implementado

- estrutura geral da janela;
- sidebar;
- topbar;
- barra de status;
- navegação;
- Home;
- Operação;
- Rolos;
- Configurações;
- Sobre;
- temas.

## Ainda precisa ser alinhado aos wireframes

- tabela definitiva da Operação;
- painel do rolo atual;
- importação;
- revisão;
- fechamento;
- resultado;
- filtros de Rolos;
- painel de detalhes;
- eventos;
- exportações;
- reexportação;
- validações completas;
- estados vazios;
- loading;
- erros.

---

# 42. Screenshots futuros

Após a implementação, registrar imagens reais em:

```text
docs/screenshots/
```

Arquivos recomendados:

```text
01-home.png
02-operacao.png
03-operacao-selecao.png
04-revisao-rolo.png
05-rolos.png
06-detalhes-rolo.png
07-configuracoes.png
08-sobre.png
```

Os screenshots devem refletir a versão atual.

---

# 43. Regra final

O wireframe deve reduzir dúvidas antes da implementação.

O usuário deve conseguir identificar visualmente:

```text
onde importar;
o que foi importado;
o que está selecionado;
qual será o total;
como revisar;
como fechar;
onde encontrar depois;
como gerar novamente.
```

A interface não deve exigir que o operador conheça a estrutura interna do sistema para concluir a operação.