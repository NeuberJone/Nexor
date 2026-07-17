# Nexor — Guia de Instalação

## 1. Objetivo

Este documento descreve os requisitos, formatos de distribuição, instalação, atualização, armazenamento local e solução de problemas do **Nexor**.

A aplicação oficial é desenvolvida em:

- C#;
- .NET 8;
- WPF;
- SQLite;
- Windows x64.

O Nexor é uma aplicação local-first e deve continuar funcional sem conexão permanente com a internet.

---

# 2. Versão documentada

Versão atual:

```text
0.2.8
```

Este documento deve ser atualizado sempre que houver mudança em:

- requisitos;
- estrutura dos artefatos;
- instalador;
- caminhos locais;
- versão Trial;
- comportamento de atualização;
- banco de dados;
- dependências;
- processo de desinstalação.

---

# 3. Requisitos do sistema

## Sistema operacional

- Windows 10 x64;
- Windows 11 x64.

Arquiteturas de 32 bits não são suportadas nesta etapa.

---

## Hardware mínimo sugerido

- processador dual-core de 64 bits;
- 4 GB de memória RAM;
- 500 MB livres para instalação;
- espaço adicional para banco, logs e exportações;
- resolução mínima recomendada de 1366 × 768.

---

## Hardware recomendado

- processador quad-core;
- 8 GB de memória RAM ou mais;
- SSD;
- resolução Full HD;
- espaço livre suficiente para manter histórico e relatórios.

O processamento do Nexor não exige placa de vídeo dedicada.

---

# 4. Dependências

## Usuário final

As publicações oficiais devem ser geradas como:

```text
self-contained
```

Isso significa que o computador do usuário não precisa possuir o .NET instalado previamente.

A publicação deve incluir o runtime necessário.

---

## Desenvolvimento

Para compilar o projeto, é necessário:

- SDK do .NET 8;
- Git;
- Visual Studio 2022, JetBrains Rider ou VS Code com suporte a C#;
- Inno Setup, quando for necessário gerar o instalador;
- PowerShell para scripts de build.

---

# 5. Formatos de distribuição

O Nexor pode ser distribuído em quatro formatos.

## 5.1 One-file oficial

Arquivo executável único da edição completa.

Exemplo:

```text
Nexor-v0.2.8.exe
```

Características:

- edição oficial;
- não expira;
- não depende do controle Trial;
- execução direta;
- publicação self-contained;
- adequada para uso portátil e testes rápidos.

A primeira inicialização pode demorar mais em razão da preparação interna do executável.

---

## 5.2 One-file Trial

Arquivo executável único da edição de avaliação.

Exemplo:

```text
Nexor-Trial-v0.2.8.exe
```

Características:

- identificada como Trial;
- avaliação local de 30 dias;
- título e tela Sobre diferenciados;
- controle isolado da edição oficial;
- publicação self-contained.

A Trial não deve alterar nem bloquear a edição oficial.

---

## 5.3 Publicação instalável

Conjunto completo de arquivos publicados para instalação ou execução manual.

Exemplo:

```text
dist/0.2.8/installable/
```

Pode conter:

- executável principal;
- DLLs;
- runtime;
- arquivos de configuração;
- recursos;
- bibliotecas;
- ícones;
- arquivos necessários à aplicação.

Essa modalidade é útil para:

- diagnóstico;
- validação;
- geração do instalador;
- investigação de falhas do one-file.

---

## 5.4 Instalador

Instalador oficial para Windows.

Exemplo:

```text
Nexor-Setup-v0.2.8.exe
```

O instalador deve:

- identificar corretamente o produto;
- mostrar a versão;
- instalar os arquivos necessários;
- criar atalhos;
- permitir atualização;
- preservar os dados locais;
- registrar desinstalação;
- não exigir Python;
- não apagar o banco do usuário.

---

# 6. Estrutura dos artefatos

Os artefatos devem ficar organizados por versão.

```text
dist/
└── 0.2.8/
    ├── onefile/
    │   └── Nexor-v0.2.8.exe
    │
    ├── trial/
    │   └── Nexor-Trial-v0.2.8.exe
    │
    ├── installable/
    │   └── arquivos da publicação
    │
    └── installer/
        └── Nexor-Setup-v0.2.8.exe
```

## Regras

- não apagar builds anteriores;
- não sobrescrever outra versão;
- não limpar automaticamente a pasta `dist`;
- manter todos os artefatos da mesma versão na pasta correspondente;
- não misturar artefatos oficiais e Trial;
- incluir o número da versão nos nomes;
- não gerar pacotes extras sem necessidade.

---

# 7. Instalação pelo instalador

## 7.1 Iniciar instalação

Execute:

```text
Nexor-Setup-v0.2.8.exe
```

Caso o Windows exiba uma confirmação de segurança, verifique:

- nome do arquivo;
- versão;
- origem;
- integridade do pacote.

Não instale arquivos recebidos de fonte não confiável.

---

## 7.2 Diretório de instalação

O diretório padrão recomendado é:

```text
C:\Program Files\Nexor
```

Em instalações por usuário, poderá ser usado:

```text
%LOCALAPPDATA%\Programs\Nexor
```

A escolha definitiva depende da configuração do instalador.

---

## 7.3 Atalhos

O instalador poderá criar:

- atalho no Menu Iniciar;
- atalho opcional na Área de Trabalho;
- entrada de desinstalação no Windows.

---

## 7.4 Conclusão

Após instalar:

1. finalize o instalador;
2. abra o Nexor;
3. confirme a versão na tela Sobre;
4. verifique a criação da pasta de dados;
5. revise as configurações;
6. teste a navegação inicial.

---

# 8. Uso do one-file

O one-file não exige instalação tradicional.

## Passos

1. copie o executável para uma pasta comum;
2. execute o arquivo;
3. aguarde a primeira inicialização;
4. permita a criação da pasta local;
5. configure os caminhos necessários.

Evite executar diretamente de:

- arquivo ZIP;
- pasta temporária;
- compartilhamento instável;
- mídia somente leitura;
- diretório sem permissão.

---

# 9. Primeira execução

Na primeira execução, o Nexor deve:

1. criar a pasta local;
2. criar o banco SQLite;
3. aplicar o schema inicial;
4. registrar a versão do schema;
5. criar configurações padrão;
6. iniciar os logs técnicos;
7. abrir a interface principal.

Caso uma dessas etapas falhe, o sistema deve:

- informar o usuário;
- registrar detalhes técnicos;
- evitar banco parcial inconsistente;
- não ocultar a falha.

---

# 10. Dados locais

O diretório padrão é:

```text
%LOCALAPPDATA%\Nexor
```

Exemplo:

```text
C:\Users\NOME_DO_USUARIO\AppData\Local\Nexor
```

Estrutura prevista:

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

A estrutura pode variar de acordo com a versão implementada.

---

# 11. Banco de dados

Arquivo padrão:

```text
%LOCALAPPDATA%\Nexor\nexor.db
```

O banco contém dados operacionais, como:

- arquivos importados;
- itens de impressão;
- rolos;
- itens vinculados;
- eventos;
- exportações;
- configurações persistidas, quando aplicável.

## Regras importantes

- o banco não fica na pasta de instalação;
- atualização comum não deve apagá-lo;
- desinstalação não deve apagá-lo automaticamente;
- o banco do Projeto Jocasta não deve ser alterado;
- migrações devem preservar os dados;
- alterações de schema devem ser versionadas.

---

# 12. Configurações locais

O Nexor poderá armazenar preferências como:

- tema;
- máquina padrão;
- pasta de importação;
- pasta de PDF;
- pasta de JPG;
- largura do JPG;
- DPI;
- limite de busca;
- comportamento após exportação.

Arquivo sugerido:

```text
%LOCALAPPDATA%\Nexor\config.json
```

Caso o arquivo esteja ausente ou inválido, a aplicação deve restaurar padrões seguros sem apagar os dados operacionais.

---

# 13. Logs técnicos

Diretório previsto:

```text
%LOCALAPPDATA%\Nexor\logs
```

Os logs ajudam a diagnosticar:

- falha de inicialização;
- erro de banco;
- erro de migration;
- erro de parsing;
- falha de importação;
- erro de exportação;
- exceções não tratadas.

Antes de solicitar suporte, preserve:

- data e hora do erro;
- versão instalada;
- ação realizada;
- mensagem exibida;
- arquivo de log correspondente.

Não envie arquivos de produção confidenciais sem autorização.

---

# 14. Exportações

Diretório padrão sugerido:

```text
%LOCALAPPDATA%\Nexor\exports
```

Estrutura:

```text
exports/
├── pdf/
│   └── AAAA/
│       └── MM/
└── mirror/
    └── AAAA/
        └── MM/
```

O usuário poderá configurar outro destino.

## Regras

- a pasta deve ser validada;
- diretórios ausentes devem ser criados;
- arquivos antigos não devem ser sobrescritos;
- reexportações devem criar nova versão;
- o caminho final deve ser informado.

---

# 15. Versão Trial

A edição Trial atual utiliza avaliação local de:

```text
30 dias
```

## Identificação

A Trial deve estar claramente identificada em:

- nome do executável;
- título da janela;
- tela Sobre;
- instalador;
- documentação;
- metadados.

## Regras

- o período começa conforme a regra implementada;
- a edição oficial não expira;
- a edição oficial não depende do estado da Trial;
- os dados da Trial devem ficar isolados das regras operacionais;
- reinstalar não deve ser apresentado como método para reiniciar a avaliação;
- falhas de controle não devem corromper o banco operacional.

Diretório sugerido:

```text
%LOCALAPPDATA%\Nexor\trial
```

A implementação real do controle deve ser documentada em versão específica quando estiver estabilizada.

---

# 16. Atualização

## 16.1 Atualização pelo instalador

Para atualizar:

1. feche o Nexor;
2. mantenha uma cópia de segurança dos dados;
3. execute o instalador da nova versão;
4. instale sobre a versão existente;
5. abra o Nexor;
6. confirme a versão;
7. verifique o banco;
8. teste a operação principal.

---

## 16.2 Atualização do one-file

Para atualizar o one-file:

1. feche a versão antiga;
2. preserve o executável anterior;
3. copie o novo arquivo;
4. execute a nova versão;
5. confirme a versão na tela Sobre.

O one-file não deve armazenar o banco ao lado do executável.

---

## 16.3 Migração do banco

Ao detectar schema antigo, o Nexor deve:

1. identificar a versão;
2. validar a sequência;
3. criar backup quando necessário;
4. executar migrations;
5. registrar o resultado;
6. iniciar a aplicação somente após sucesso.

Em caso de falha:

- não continuar silenciosamente;
- não apagar o banco;
- registrar o erro;
- orientar recuperação.

---

# 17. Backup

Antes de:

- atualizar versão;
- testar migration;
- reinstalar;
- mover dados;
- restaurar configuração;
- realizar manutenção;

faça uma cópia de:

```text
%LOCALAPPDATA%\Nexor
```

O arquivo mais importante é:

```text
nexor.db
```

Também é recomendado preservar:

- `config.json`;
- pasta `exports`;
- pasta `logs`;
- pasta `backups`.

---

# 18. Restauração

Para restaurar manualmente:

1. feche o Nexor;
2. copie a pasta atual para um local seguro;
3. substitua o banco pelo backup compatível;
4. preserve o nome esperado;
5. abra o aplicativo;
6. verifique logs e versão do schema;
7. confirme os registros.

Não restaure banco de versão futura em versão antiga sem procedimento específico.

---

# 19. Desinstalação

A desinstalação remove os arquivos instalados do programa.

Ela não deve apagar automaticamente:

```text
%LOCALAPPDATA%\Nexor
```

Isso preserva:

- banco;
- configurações;
- logs;
- relatórios;
- dados Trial.

Caso o usuário deseje remoção completa, deverá apagar manualmente a pasta local após criar backup.

---

# 20. Instalação limpa

Para simular uma primeira instalação:

1. desinstale o Nexor;
2. faça backup da pasta local;
3. renomeie temporariamente:

```text
%LOCALAPPDATA%\Nexor
```

4. instale a nova versão;
5. execute;
6. confirme a criação dos dados;
7. teste o fluxo.

Não exclua dados reais sem backup.

---

# 21. Validação pós-instalação

Após instalar, verificar:

- aplicativo abre;
- versão correta aparece;
- sidebar funciona;
- telas abrem;
- tema é aplicado;
- tema persiste após reiniciar;
- banco é criado;
- logs são criados;
- configurações são salvas;
- aplicação fecha sem erro;
- edição Trial e oficial permanecem separadas.

Quando o núcleo estiver completo, testar também:

- importação;
- fechamento;
- PDF;
- JPG;
- consulta;
- reexportação.

---

# 22. Erros comuns

## Aplicação não abre

Verifique:

- sistema x64;
- arquivos completos;
- antivírus;
- logs;
- permissões;
- integridade do executável.

Teste a publicação instalável para obter diagnóstico mais detalhado.

---

## Banco não foi criado

Verifique:

- permissão em `%LOCALAPPDATA%`;
- espaço em disco;
- bloqueio do arquivo;
- logs;
- migration.

---

## Banco está bloqueado

Possíveis causas:

- duas instâncias;
- processo anterior ainda aberto;
- ferramenta externa acessando o SQLite;
- antivírus;
- arquivo em pasta sincronizada.

Feche os processos e tente novamente.

---

## Tema não permanece

Verifique:

- criação de `config.json`;
- permissão da pasta;
- logs;
- formato do arquivo.

---

## Arquivo não é importado

Verifique:

- extensão `.txt`;
- conteúdo;
- campos obrigatórios;
- `EndTime`;
- `HeightMM`;
- se o arquivo já foi importado;
- logs.

---

## PDF ou JPG não é gerado

Verifique:

- pasta de saída;
- permissão;
- espaço;
- arquivo existente aberto;
- dependência da biblioteca;
- logs;
- dados do rolo.

---

## Windows bloqueia o executável

Aplicações sem assinatura digital podem exibir alerta do SmartScreen.

Confirme:

- origem;
- nome;
- versão;
- hash quando fornecido.

Assinatura digital poderá ser adotada futuramente.

---

## Antivírus sinaliza o one-file

Publicações one-file podem gerar falso positivo em alguns antivírus.

Ações recomendadas:

- validar o hash;
- testar publicação instalável;
- enviar o arquivo para análise do fornecedor;
- não desativar permanentemente o antivírus;
- utilizar assinatura digital futura.

---

# 23. Limitações atuais

Na versão documentada:

- importação pela interface ainda está em desenvolvimento;
- fechamento não está completamente finalizado;
- exportações ainda estão sendo implementadas;
- consulta histórica está parcial;
- instalador precisa de validação em ambiente limpo;
- screenshots ainda não foram incorporados;
- Trial precisa permanecer alinhada com o comportamento real.

O instalador não deve ser considerado validado apenas porque foi gerado.

---

# 24. Instalação para desenvolvimento

Clone o repositório e entre na pasta:

```powershell
git clone https://github.com/NeuberJone/Nexor.git
cd Nexor
```

Restaurar:

```powershell
dotnet restore Nexor.sln
```

Build:

```powershell
dotnet build Nexor.sln -c Release
```

Testes:

```powershell
dotnet test Nexor.sln -c Release
```

Executar:

```powershell
dotnet run --project src/Nexor.Desktop/Nexor.Desktop.csproj
```

---

# 25. Publicação manual

Exemplo de publicação self-contained:

```powershell
dotnet publish src/Nexor.Desktop/Nexor.Desktop.csproj `
  -c Release `
  -r win-x64 `
  --self-contained true
```

Exemplo one-file:

```powershell
dotnet publish src/Nexor.Desktop/Nexor.Desktop.csproj `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true
```

Os comandos definitivos devem ser centralizados nos scripts de build do repositório.

---

# 26. Instalador Inno Setup

Arquivo previsto:

```text
installer/Nexor.iss
```

O script deve obter ou receber:

- versão;
- caminho da publicação;
- nome do produto;
- ícone;
- arquivos;
- diretório de saída.

Saída:

```text
Nexor-Setup-vX.Y.Z.exe
```

O instalador não deve incluir:

- código-fonte;
- testes;
- banco de desenvolvimento;
- dados reais;
- arquivos temporários;
- segredos;
- legado Python;
- conteúdo da pasta `dist` de versões anteriores.

---

# 27. Verificação de versão

A versão deve aparecer de forma consistente em:

- `.csproj`;
- assembly;
- executável;
- tela Sobre;
- README;
- changelog;
- guia de instalação;
- instalador;
- pasta de distribuição;
- nome dos artefatos.

Exemplo:

```text
0.2.8
```

Não deve existir mistura como:

```text
aplicativo 0.2.8
instalador 0.2.5
README 0.2.4
```

---

# 28. Checklist de instalação

## Antes de distribuir

- [ ] versão atualizada;
- [ ] changelog atualizado;
- [ ] README atualizado;
- [ ] licença presente;
- [ ] build Release concluído;
- [ ] testes aprovados;
- [ ] one-file oficial gerado;
- [ ] Trial gerada;
- [ ] publicação instalável gerada;
- [ ] instalador gerado;
- [ ] nomes versionados;
- [ ] artefatos na pasta correta;
- [ ] nenhuma versão anterior sobrescrita;
- [ ] sem segredos;
- [ ] sem banco de desenvolvimento;
- [ ] sem dados reais;
- [ ] instalador testado;
- [ ] aplicação aberta após instalação;
- [ ] dados locais preservados em atualização.

---

# 29. Checklist de primeira execução

- [ ] pasta local criada;
- [ ] banco criado;
- [ ] schema aplicado;
- [ ] configuração criada;
- [ ] logs criados;
- [ ] versão correta exibida;
- [ ] tema inicial aplicado;
- [ ] navegação funcionando;
- [ ] reinicialização funcionando.

---

# 30. Suporte e diagnóstico

Ao relatar um problema, informar:

- versão;
- edição oficial ou Trial;
- Windows;
- modalidade de instalação;
- ação realizada;
- mensagem exibida;
- horário;
- trecho relevante do log;
- se era instalação limpa ou atualização.

Não enviar publicamente:

- banco real;
- nomes de clientes;
- registros de produção;
- caminhos sensíveis;
- dados pessoais;
- credenciais.

---

# 31. Segurança

Baixe o Nexor somente de fontes autorizadas.

O projeto não deve solicitar:

- senha do Windows;
- token pessoal;
- credenciais bancárias;
- desativação permanente de antivírus;
- acesso administrativo sem necessidade.

O instalador pode solicitar elevação apenas quando o diretório escolhido exigir.

---

# 32. Relação com o Projeto Jocasta

O Nexor utiliza o PXPrintLogs e o PXSearchOrders como referências funcionais.

A instalação do Nexor:

- não exige o Jocasta;
- não altera o banco do Jocasta;
- não depende do Python;
- não instala módulos do Jocasta;
- não compartilha automaticamente os dados.

Uma migração futura deverá ser explícita.

---

# 33. Relação com o ListForge

O ListForge é apenas referência visual.

A instalação do Nexor:

- não instala o ListForge;
- não depende do ListForge;
- não compartilha licenciamento;
- não compartilha configurações;
- não compartilha dados Trial;
- não reutiliza arquivos do outro aplicativo em runtime.

---

# 34. Critério de aceite do instalador

O instalador será considerado validado quando:

- funcionar em Windows limpo;
- instalar a versão correta;
- abrir o aplicativo;
- criar atalhos;
- criar dados locais;
- permitir atualização;
- preservar o banco;
- permitir desinstalação;
- não exigir SDK;
- não exigir Python;
- não deixar arquivos desnecessários;
- não corromper a edição Trial ou oficial.

---

# 35. Próximos passos

Após estabilizar a instalação:

- assinatura digital;
- verificação de hash;
- atualização assistida;
- backup automático;
- pacote de suporte;
- diagnóstico interno;
- política formal de retenção;
- canal de atualização opcional.

---

# 36. Síntese

A instalação do Nexor deve separar claramente:

```text
Arquivos do programa
        ↓
pasta de instalação

Dados do usuário
        ↓
%LOCALAPPDATA%\Nexor

Artefatos de desenvolvimento
        ↓
dist/X.Y.Z
```

Atualizar o aplicativo não deve significar apagar os dados.

A prioridade é garantir instalação previsível, preservação do banco e possibilidade de recuperação.
