# Nexor — Especificação de UI/UX

## 1. Objetivo

Este documento define os princípios, padrões visuais, fluxos e comportamentos da interface do **Nexor**.

A aplicação é desenvolvida em:

- C#;
- .NET 8;
- WPF;
- Windows x64;
- arquitetura MVVM.

A interface deve priorizar:

- rapidez operacional;
- clareza;
- baixa chance de erro;
- rastreabilidade;
- consistência visual;
- uso recorrente durante a produção.

O layout utiliza o **ListForge apenas como referência visual**, sem copiar suas regras de negócio, textos ou funcionalidades.

---

# 2. Direção da experiência

O Nexor deve transmitir:

- confiabilidade;
- organização;
- estabilidade;
- controle;
- clareza;
- sensação de ferramenta profissional.

A interface não deve parecer:

- excessivamente decorativa;
- um painel genérico;
- um conjunto de scripts;
- um sistema ERP complexo;
- uma cópia visual literal do ListForge.

---

# 3. Princípios de UI/UX

## 3.1 Operação primeiro

As tarefas mais frequentes devem exigir poucos passos.

A interface deve favorecer o fluxo:

```text
Importar
→ selecionar
→ revisar
→ fechar
→ exportar
```

---

## 3.2 Uma ação principal por tela

Cada tela deve possuir uma função dominante.

Exemplos:

- Home: mostrar a situação atual;
- Operação: montar o rolo;
- Rolos: localizar e consultar;
- Configurações: ajustar o sistema;
- Sobre: informar versão e suporte.

---

## 3.3 Estados visíveis

O usuário deve perceber claramente quando um item está:

- disponível;
- selecionado;
- inválido;
- duplicado;
- suspeito;
- já vinculado;
- fechado;
- exportado.

Nenhum estado importante deve depender somente de cor.

Também devem ser usados:

- textos;
- badges;
- ícones;
- tooltips;
- mensagens;
- contraste.

---

## 3.4 Redução de erros

A interface deve impedir ou dificultar:

- fechar rolo vazio;
- misturar máquinas sem aviso;
- selecionar item inválido;
- reutilizar item já vinculado;
- sobrescrever exportações;
- perder seleção sem confirmação;
- fechar sem revisar dados essenciais.

---

## 3.5 Linguagem operacional

Evitar termos excessivamente técnicos.

O termo `Job` não deve aparecer em textos visíveis.

Usar:

- item;
- registro;
- impressão;
- arquivo;
- pedido;
- processamento;
- rolo.

---

## 3.6 Local-first

A interface não deve aparentar dependência de internet.

Falhas de rede não devem impedir o fluxo principal.

Recursos online futuros deverão ser apresentados como complementares.

---

# 4. Perfis de usuário

## 4.1 Operador

### Objetivos

- importar registros;
- identificar itens;
- selecionar o rolo atual;
- revisar;
- fechar;
- exportar.

### Necessidades

- ações rápidas;
- poucos filtros;
- totais visíveis;
- mensagens simples;
- baixa chance de erro.

### Evitar

- opções administrativas em excesso;
- linguagem técnica;
- muitos níveis de navegação;
- informações históricas desnecessárias durante a operação.

---

## 4.2 Conferente

### Objetivos

- localizar um rolo;
- conferir composição;
- consultar eventos;
- verificar exportações;
- reexportar.

### Necessidades

- busca rápida;
- filtros;
- detalhes completos;
- histórico;
- acesso ao caminho dos arquivos.

---

## 4.3 Administrador

### Objetivos

- configurar pastas;
- definir preferências;
- conferir versão;
- manter parâmetros;
- diagnosticar problemas.

### Necessidades

- formulários claros;
- validação;
- informações técnicas acessíveis;
- restauração de padrões.

---

# 5. Estrutura visual principal

O layout da aplicação deve seguir esta composição:

```text
┌─────────────────┬────────────────────────────────────┐
│                 │ Topbar                             │
│                 ├────────────────────────────────────┤
│ Sidebar         │                                    │
│                 │ Conteúdo principal                 │
│                 │                                    │
│                 ├────────────────────────────────────┤
│                 │ Barra de status                    │
└─────────────────┴────────────────────────────────────┘
```

---

# 6. Sidebar

## 6.1 Objetivo

Oferecer navegação principal previsível.

## 6.2 Itens iniciais

- Home;
- Operação;
- Rolos;
- Configurações;
- Sobre.

## 6.3 Itens futuros

- Cadastros;
- Planejamento;
- Estoque;
- Analytics.

Itens futuros não devem aparecer como ativos antes de possuírem funcionalidade real.

## 6.4 Comportamento

- item atual deve ficar claramente destacado;
- hover deve ser visível;
- ícone e texto devem permanecer alinhados;
- navegação não deve recarregar dados desnecessariamente;
- mudança de tela deve preservar contexto quando apropriado.

## 6.5 Largura

Referência inicial:

```text
210 px
```

Pode ser ajustada conforme testes de legibilidade.

---

# 7. Topbar

## 7.1 Conteúdo

A topbar deve apresentar:

- título da tela;
- subtítulo ou contexto curto, quando necessário;
- ações secundárias;
- indicadores de carregamento;
- botão contextual quando fizer sentido.

## 7.2 Exemplos

### Operação

```text
Operação
18 registros disponíveis
```

Ações:

- Atualizar;
- Importar;
- Limpar filtros.

### Rolos

```text
Rolos
Consulta histórica
```

Ações:

- Atualizar;
- Limpar filtros.

---

# 8. Barra de status

## 8.1 Objetivo

Exibir retorno discreto sobre ações recentes.

Exemplos:

```text
12 arquivos importados.
```

```text
Tema alterado para Nexor Dark.
```

```text
Rolo M1_16-07-2026_153045 fechado com sucesso.
```

## 8.2 Regras

- mensagens curtas;
- sem excesso de detalhes técnicos;
- erros graves devem usar modal ou painel próprio;
- mensagens temporárias podem desaparecer após alguns segundos;
- informações importantes devem permanecer acessíveis em logs ou detalhes.

---

# 9. Home

## 9.1 Objetivo

Mostrar rapidamente o que exige atenção.

## 9.2 Conteúdo recomendado

### Cards principais

- Registros disponíveis;
- Rolos fechados hoje;
- Último rolo;
- Alertas;
- Importações recentes.

### Ação principal

```text
Ir para Operação
```

### Ações rápidas

- Importar arquivos;
- Consultar rolos;
- Abrir configurações.

## 9.3 Regras

- usar dados reais;
- não exibir métricas fictícias;
- empty states devem orientar;
- cards não devem competir visualmente;
- alertas devem receber destaque proporcional à gravidade.

---

# 10. Tela Operação

## 10.1 Objetivo

Permitir importação, seleção e montagem do rolo.

## 10.2 Estrutura

```text
┌──────────────────────────────────┬──────────────────────┐
│ Filtros                          │ Rolo atual           │
├──────────────────────────────────┤                      │
│                                  │ Quantidade           │
│ Lista de registros               │ Metragem             │
│                                  │ Máquina              │
│                                  │ Blocos               │
│                                  │ Alertas              │
│                                  │                      │
│                                  │ Revisar rolo         │
└──────────────────────────────────┴──────────────────────┘
```

## 10.3 Barra de ações

- Importar arquivos;
- Importar pasta;
- Atualizar;
- Limpar filtros;
- Limpar seleção.

## 10.4 Filtros

- máquina;
- tecido;
- status;
- período;
- busca textual.

Os filtros devem ser compactos e próximos da tabela.

---

# 11. Tabela da Operação

## 11.1 Colunas

- seleção;
- horário;
- documento;
- tecido;
- máquina;
- metragem;
- status.

Campos técnicos adicionais podem ficar em:

- painel de detalhes;
- tooltip;
- coluna opcional;
- modal.

## 11.2 Regras visuais

- seleção clara;
- linhas alternadas apenas se melhorarem a leitura;
- cabeçalho fixo;
- colunas redimensionáveis;
- texto longo com ellipsis e tooltip;
- status com badge;
- suspeitas destacadas sem prejudicar legibilidade;
- inválidos não selecionáveis;
- itens já vinculados visualmente diferenciados.

## 11.3 Seleção

- checkbox na primeira coluna;
- seleção múltipla;
- clique na linha pode abrir detalhes;
- checkbox e seleção da linha não devem gerar estados contraditórios;
- seleção deve atualizar o resumo imediatamente.

---

# 12. Painel do rolo atual

## 12.1 Conteúdo

- código provisório;
- máquina;
- quantidade de itens;
- metragem total;
- quantidade de blocos;
- tecidos;
- intervalo de horários;
- alertas;
- observações curtas.

## 12.2 Ações

- Revisar rolo;
- Limpar seleção;
- Atualizar código;
- Fechar e exportar, após revisão.

## 12.3 Estados

### Sem seleção

```text
Nenhum item selecionado.
Selecione os registros que pertencem ao rolo atual.
```

### Seleção válida

Mostrar totais e liberar revisão.

### Seleção com alerta

Mostrar mensagem e orientar correção.

---

# 13. Importação

## 13.1 Modal ou painel de resultado

Após importar, exibir:

- arquivos encontrados;
- importados;
- duplicados;
- inválidos;
- ignorados.

Exemplo:

```text
Importação concluída

Importados: 18
Duplicados: 3
Inválidos: 1
```

## 13.2 Drag and drop

Durante o arraste:

- realçar área;
- exibir texto de orientação;
- indicar tipos aceitos;
- restaurar visual ao sair.

Exemplo:

```text
Solte os arquivos para importar
```

---

# 14. Revisão e fechamento

## 14.1 Objetivo

Dar segurança antes da confirmação.

## 14.2 Estrutura

### Dados principais

- código;
- máquina;
- observações.

### Resumo

- quantidade;
- metragem;
- blocos;
- tecidos;
- intervalo de horários.

### Lista resumida

- horário;
- documento;
- tecido;
- metragem.

## 14.3 Ações

- Voltar;
- Cancelar;
- Confirmar fechamento;
- Fechar e exportar.

## 14.4 Confirmação

A confirmação deve informar claramente que a composição será congelada.

Exemplo:

```text
Confirmar fechamento?

Após o fechamento, a composição do rolo será preservada no histórico.
```

---

# 15. Resultado do fechamento

Após sucesso, apresentar:

- código;
- quantidade;
- metragem;
- máquina;
- horário;
- status;
- arquivos gerados, quando aplicável.

Ações:

- Abrir pasta;
- Abrir Rolos;
- Exportar;
- Iniciar novo rolo.

---

# 16. Tela Rolos

## 16.1 Objetivo

Localizar e consultar registros históricos.

## 16.2 Estrutura

```text
┌──────────────────────────────────┬──────────────────────┐
│ Filtros                          │ Detalhes             │
├──────────────────────────────────┤                      │
│ Lista de rolos                   │ Resumo               │
│                                  │ Itens                │
│                                  │ Eventos              │
│                                  │ Exportações          │
└──────────────────────────────────┴──────────────────────┘
```

## 16.3 Filtros

- período;
- máquina;
- tecido;
- status;
- código;
- pedido ou arquivo;
- limite.

## 16.4 Lista

Colunas:

- código;
- data;
- máquina;
- quantidade;
- metragem;
- status.

---

# 17. Painel de detalhes do rolo

## 17.1 Abas ou seções

- Resumo;
- Itens;
- Eventos;
- Exportações.

## 17.2 Resumo

- código;
- máquina;
- data;
- quantidade;
- metragem;
- tecidos;
- blocos;
- status;
- observações.

## 17.3 Itens

- horário;
- documento;
- tecido;
- metragem;
- arquivo de origem.

## 17.4 Eventos

- data;
- tipo;
- descrição;
- versão.

## 17.5 Exportações

- tipo;
- modo;
- data;
- nome;
- caminho;
- reexportação.

---

# 18. Ações da tela Rolos

- copiar código;
- abrir pasta;
- reexportar PDF completo;
- reexportar PDF resumido;
- reexportar JPG espelhado;
- atualizar;
- revisar, futuramente;
- reabrir, futuramente.

Ações indisponíveis devem ser desabilitadas com explicação.

---

# 19. Configurações

## 19.1 Estrutura

Organizar por seções ou abas:

- Geral;
- Pastas;
- Relatórios;
- Aparência;
- Diagnóstico.

## 19.2 Geral

- máquina padrão;
- limite de resultados;
- comportamento após exportação;
- confirmações.

## 19.3 Pastas

- origem dos logs;
- PDF;
- JPG;
- pasta temporária.

Cada caminho deve possuir:

- campo;
- botão Procurar;
- botão Testar;
- botão Abrir pasta.

## 19.4 Relatórios

- modo padrão;
- largura;
- DPI;
- padrão de nome.

## 19.5 Aparência

- tema;
- densidade futura;
- tamanho de fonte futuro.

## 19.6 Diagnóstico

- versão;
- banco;
- logs;
- pasta local;
- abrir diretório;
- copiar informações de suporte.

---

# 20. Tela Sobre

Deve apresentar:

- nome;
- versão;
- edição;
- tecnologia;
- autor;
- caminho dos dados;
- caminho dos logs;
- licença;
- link do repositório, quando apropriado;
- informações da Trial, quando aplicável.

A tela Sobre não deve conter informações falsas ou placeholder de suporte.

---

# 21. Temas

## 21.1 Temas iniciais

- Nexor Dark;
- Nexor Light;
- SISBolt.

## 21.2 Recursos semânticos

Usar chaves como:

```text
AppBackgroundBrush
SurfaceBrush
SidebarBackgroundBrush
TopbarBackgroundBrush
BorderBrush
PrimaryBrush
PrimaryHoverBrush
TextPrimaryBrush
TextSecondaryBrush
TextMutedBrush
SuccessBrush
WarningBrush
DangerBrush
SelectionBrush
DisabledBrush
```

## 21.3 Regras

- evitar cores diretas nas Views;
- manter contraste;
- testar todos os estados nos três temas;
- seleção deve permanecer legível;
- item inativo não pode parecer selecionado;
- texto desabilitado deve continuar compreensível.

---

# 22. Tipografia

Fonte preferencial:

```text
Segoe UI
```

Escala sugerida:

| Uso | Tamanho |
|---|---:|
| Título principal | 20–24 px |
| Título da tela | 16–18 px |
| Título de card | 13–15 px |
| Texto padrão | 12–14 px |
| Texto secundário | 11–12 px |
| Badge | 10–11 px |

Evitar:

- fontes decorativas;
- excesso de negrito;
- texto muito pequeno;
- títulos com peso visual exagerado.

---

# 23. Espaçamentos

Escala sugerida:

```text
4
8
12
16
20
24
32
```

Usar espaçamentos consistentes entre:

- cards;
- labels;
- campos;
- botões;
- tabelas;
- grupos;
- seções.

Evitar margens arbitrárias diferentes em cada tela.

---

# 24. Botões

## 24.1 Primário

Usado para a principal ação da tela.

Exemplos:

- Revisar rolo;
- Confirmar fechamento;
- Salvar configurações.

## 24.2 Secundário

Exemplos:

- Cancelar;
- Voltar;
- Atualizar;
- Abrir pasta.

## 24.3 Perigo

Exemplos:

- Limpar seleção;
- Excluir, se existir futuramente;
- Reabrir com impacto.

## 24.4 Regras

- texto direto;
- verbo no início;
- não usar textos genéricos como “OK” quando houver alternativa;
- botão desabilitado deve indicar motivo;
- ícone não deve substituir texto em ações críticas.

---

# 25. Campos

## Regras

- label sempre visível;
- placeholder não substitui label;
- erro próximo ao campo;
- validação após interação;
- máscaras somente quando ajudarem;
- caminho longo deve permitir copiar;
- campos somente leitura devem parecer diferentes de campos editáveis.

---

# 26. Badges de status

Exemplos:

```text
Disponível
Suspeito
Inválido
Duplicado
Selecionado
Fechado
Exportado
Revisado
```

Badges devem possuir:

- cor;
- texto;
- contraste;
- significado consistente.

---

# 27. Empty states

## Operação sem registros

```text
Nenhum registro disponível.

Importe arquivos ou selecione uma pasta para começar.
```

Ação:

```text
Importar arquivos
```

## Rolos sem resultado

```text
Nenhum rolo encontrado para os filtros atuais.
```

Ação:

```text
Limpar filtros
```

## Sem exportações

```text
Este rolo ainda não possui arquivos exportados.
```

---

# 28. Loading

Operações demoradas devem apresentar:

- indicador;
- texto;
- bloqueio somente da área necessária;
- possibilidade de cancelamento, quando suportada.

Exemplos:

```text
Importando arquivos...
```

```text
Gerando PDF...
```

```text
Carregando rolos...
```

Não deixar a interface parecer travada.

---

# 29. Mensagens de erro

## Validação

```text
Selecione pelo menos um item.
```

## Duplicidade

```text
O arquivo já foi importado anteriormente.
```

## Falha técnica

```text
Não foi possível concluir a operação.

Consulte os logs para obter mais detalhes.
```

## Regra

Detalhes técnicos devem ir para o log, não para a mensagem principal.

Pode haver botão:

```text
Copiar detalhes técnicos
```

quando apropriado.

---

# 30. Modais

Usar modais somente para:

- confirmação sensível;
- revisão;
- resultado importante;
- erro bloqueante;
- formulário curto.

Evitar modal para:

- toda mensagem de sucesso;
- filtros;
- navegação;
- informações que cabem em painel.

---

# 31. Atalhos de teclado

Sugestões futuras:

```text
Ctrl + O       Importar arquivos
Ctrl + Shift + O  Importar pasta
Ctrl + F       Focar busca
Ctrl + R       Atualizar
Esc            Fechar modal ou cancelar
Enter          Confirmar ação principal
```

Atalhos não devem conflitar com edição de campos.

---

# 32. Acessibilidade

A interface deve:

- manter contraste adequado;
- não depender somente de cor;
- permitir navegação por teclado;
- exibir foco visível;
- usar labels;
- fornecer tooltips;
- evitar textos minúsculos;
- permitir leitura clara em Full HD;
- considerar escalas do Windows acima de 100%.

---

# 33. Responsividade desktop

O Nexor é desktop, mas deve funcionar em diferentes tamanhos de janela.

## Mínimo sugerido

```text
1320 × 780
```

## Comportamento

- sidebar fixa ou recolhível futuramente;
- tabelas ocupam espaço restante;
- painel lateral possui largura mínima;
- scroll somente onde necessário;
- botões críticos não devem desaparecer;
- modal deve respeitar janela menor.

---

# 34. Persistência de estado

Pode ser persistido:

- tema;
- tamanho da janela;
- posição da janela;
- filtros recentes, quando útil;
- pasta selecionada;
- máquina padrão;
- largura de colunas, futuramente.

Não persistir estados temporários que possam confundir o operador, como uma seleção antiga de rolo, sem decisão explícita.

---

# 35. Critérios de aceite da Home

- ação principal clara;
- dados reais;
- cards legíveis;
- empty state útil;
- acesso rápido à Operação;
- alertas visíveis;
- funcionamento nos três temas.

---

# 36. Critérios de aceite da Operação

- importar pela UI;
- listar registros;
- filtrar;
- selecionar;
- atualizar resumo;
- destacar estados;
- impedir inválidos;
- revisar;
- fechar;
- manter desempenho adequado.

---

# 37. Critérios de aceite da tela Rolos

- listar;
- filtrar;
- buscar;
- selecionar;
- abrir detalhes;
- listar itens;
- listar eventos;
- listar exportações;
- copiar código;
- reexportar.

---

# 38. Critérios de aceite das Configurações

- validar caminhos;
- salvar;
- restaurar após reiniciar;
- testar pastas;
- trocar tema;
- informar erro;
- não perder banco;
- não exigir edição manual de arquivo.

---

# 39. Screenshots

As imagens oficiais devem ser armazenadas em:

```text
docs/screenshots/
```

Nomes recomendados:

```text
01-home.png
02-operacao.png
03-rolos.png
04-configuracoes.png
05-sobre.png
```

Regras:

- usar a interface real;
- não usar mockup como screenshot final;
- não reutilizar ListForge;
- não usar caminhos locais no README;
- manter imagens atualizadas;
- remover screenshots antigos quando deixarem de representar a versão.

---

# 40. Implementado e planejado

## Implementado ou parcialmente implementado

- shell principal;
- sidebar;
- topbar;
- status bar;
- navegação;
- Home;
- Operação;
- Rolos;
- Configurações;
- Sobre;
- temas;
- persistência de tema;
- estados visuais iniciais.

## Em desenvolvimento

- importação completa;
- tabela operacional definitiva;
- painel de rolo;
- revisão;
- fechamento;
- detalhes históricos;
- exportações;
- reexportação.

## Futuro

- Cadastros;
- Planejamento;
- Estoque;
- Analytics;
- experiência multiestação.

---

# 41. Decisões pendentes

- conjunto definitivo de ícones;
- biblioteca de ícones;
- largura final da sidebar;
- comportamento responsivo;
- navegação definitiva;
- uso de abas no detalhe;
- densidade da tabela;
- atalhos;
- confirmação de reabertura;
- notificações;
- acessibilidade avançada;
- suporte a múltiplos monitores;
- comportamento com escala de 125% e 150%.

---

# 42. Regra final

A interface do Nexor deve tornar evidente:

```text
o que aconteceu;
o que está disponível;
o que foi selecionado;
o que precisa de atenção;
o que será fechado;
o que foi exportado;
onde consultar depois.
```

A qualidade da UI não deve ser medida pela quantidade de efeitos visuais, mas pela capacidade de o operador concluir o fluxo com rapidez, segurança e confiança.