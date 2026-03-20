"""
Nexor Desktop - Aplicação Desktop Instalável
Wrapper para executar Nexor como aplicação desktop com PyInstaller
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading
from pathlib import Path

# Detectar se está rodando como executável (PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_port():
    """Obtém porta disponível"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def start_flask_server():
    """Inicia o servidor Flask em background"""
    # Configurar variáveis de ambiente
    env = os.environ.copy()
    env['FLASK_APP'] = 'main.py'
    env['FLASK_ENV'] = 'production'
    env['DEBUG'] = 'False'
    
    port = get_port()
    env['PORT'] = str(port)
    
    # Iniciar Flask
    if getattr(sys, 'frozen', False):
        # Se for executável, usar python.exe do bundle
        python_exe = sys.executable
    else:
        python_exe = sys.executable
    
    cmd = [python_exe, os.path.join(BASE_DIR, 'main.py')]
    
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=BASE_DIR
    )
    
    return process, port

def open_browser(port, delay=2):
    """Abre o navegador após delay"""
    time.sleep(delay)
    webbrowser.open(f'http://localhost:{port}')

def main():
    """Função principal"""
    print("=" * 60)
    print("  NEXOR - Sistema de Produção Têxtil")
    print("=" * 60)
    print()
    print("Iniciando aplicação...")
    
    try:
        # Iniciar servidor Flask
        process, port = start_flask_server()
        print(f"✓ Servidor iniciado na porta {port}")
        print(f"✓ Abrindo navegador em http://localhost:{port}")
        print()
        print("Pressione Ctrl+C para encerrar")
        print()
        
        # Abrir navegador em thread separada
        browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
        browser_thread.start()
        
        # Aguardar processo Flask
        process.wait()
        
    except KeyboardInterrupt:
        print("\n\nEncerrando aplicação...")
        if 'process' in locals():
            process.terminate()
            process.wait(timeout=5)
        print("✓ Aplicação encerrada")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
