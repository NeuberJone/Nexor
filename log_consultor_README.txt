Consultor de Logs de Impressão

Arquivos:
- log_consultor.py -> programa principal

Recursos:
- Importa um ou mais logs .txt
- Suporta drag and drop quando tkinterdnd2 estiver instalado
- Mostra resumo amigável, campos brutos e JSON resumido
- Converte tamanhos para metros
- Calcula tempo de impressão, metragem real impressa, consumo total de papel até o fim da impressão, área, velocidade média e tinta total
- Mostra margens laterais, ocupação da largura e outras informações possíveis
- Tela de configurações para papel e tintas
- Estimativa de custo de papel, tinta e total
- Exporta o relatório amigável para TXT

Dependências:
- Python 3.10+
- tkinter (normalmente já vem com o Python no Windows)
- tkinterdnd2 (opcional, apenas para drag and drop)

Instalação opcional do drag and drop:
    pip install tkinterdnd2

Rodar:
    python log_consultor.py

Gerar onefile com PyInstaller:
    pyinstaller --noconfirm --onefile --windowed --hidden-import=tkinterdnd2 log_consultor.py

Observações:
- O arquivo de configuração é salvo como log_consultor_config.json na mesma pasta do executável/script.
- Nem todo log informa espaço depois da impressão. Nesses casos o programa informa que o dado não está disponível.
- Quantidade de cópias realmente concluídas em impressão interrompida não é provada diretamente por esse tipo de log; o dado mais confiável continua sendo a metragem.
