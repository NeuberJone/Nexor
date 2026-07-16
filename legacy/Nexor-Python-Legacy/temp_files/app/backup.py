"""
Módulo de Backup
Realiza backup automático do banco de dados
"""

import os
import shutil
import sqlite3
import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class BackupManager:
    """Gerenciador de backup"""
    
    def __init__(self, db_path: str = None, backup_dir: str = None):
        """Inicializa o gerenciador de backup"""
        self.db_path = db_path or 'nexor.db'
        self.backup_dir = backup_dir or '/tmp/nexor_backups'
        
        # Criar diretório de backup se não existir
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, compress: bool = True) -> Dict[str, Any]:
        """Cria backup do banco de dados"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'nexor_backup_{timestamp}'
            
            if compress:
                backup_path = os.path.join(self.backup_dir, f'{backup_name}.db.gz')
                
                # Comprimir banco de dados
                with open(self.db_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                backup_path = os.path.join(self.backup_dir, f'{backup_name}.db')
                shutil.copy2(self.db_path, backup_path)
            
            file_size = os.path.getsize(backup_path)
            
            return {
                'ok': True,
                'backup_name': backup_name,
                'backup_path': backup_path,
                'file_size': file_size,
                'compressed': compress,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def list_backups(self) -> Dict[str, Any]:
        """Lista todos os backups disponíveis"""
        try:
            backups = []
            
            for filename in sorted(os.listdir(self.backup_dir), reverse=True):
                filepath = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    mod_time = os.path.getmtime(filepath)
                    mod_datetime = datetime.fromtimestamp(mod_time)
                    
                    backups.append({
                        'name': filename,
                        'path': filepath,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': mod_datetime.isoformat(),
                        'compressed': filename.endswith('.gz'),
                    })
            
            return {
                'ok': True,
                'backups': backups,
                'total': len(backups),
                'backup_dir': self.backup_dir,
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
            }
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restaura um backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return {
                    'ok': False,
                    'error': f'Backup não encontrado: {backup_name}',
                }
            
            # Criar backup do banco atual antes de restaurar
            current_backup = self.create_backup()
            
            if backup_name.endswith('.gz'):
                # Descomprimir
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(self.db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Copiar diretamente
                shutil.copy2(backup_path, self.db_path)
            
            return {
                'ok': True,
                'restored_from': backup_name,
                'current_backup': current_backup,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """Deleta um backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return {
                    'ok': False,
                    'error': f'Backup não encontrado: {backup_name}',
                }
            
            os.remove(backup_path)
            
            return {
                'ok': True,
                'deleted': backup_name,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def cleanup_old_backups(self, keep_count: int = 10) -> Dict[str, Any]:
        """Remove backups antigos, mantendo apenas os N mais recentes"""
        try:
            backups_list = self.list_backups()
            
            if not backups_list['ok']:
                return backups_list
            
            backups = backups_list['backups']
            
            if len(backups) <= keep_count:
                return {
                    'ok': True,
                    'deleted': 0,
                    'message': f'Apenas {len(backups)} backups existem, nenhum deletado',
                }
            
            # Deletar backups antigos
            deleted_count = 0
            for backup in backups[keep_count:]:
                try:
                    os.remove(backup['path'])
                    deleted_count += 1
                except Exception as e:
                    print(f'Erro ao deletar {backup["name"]}: {e}')
            
            return {
                'ok': True,
                'deleted': deleted_count,
                'kept': keep_count,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
            }
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de backup"""
        try:
            backups_list = self.list_backups()
            
            if not backups_list['ok']:
                return backups_list
            
            backups = backups_list['backups']
            total_size = sum(b['size'] for b in backups)
            
            return {
                'ok': True,
                'total_backups': len(backups),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_backup': backups[-1]['modified'] if backups else None,
                'newest_backup': backups[0]['modified'] if backups else None,
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
            }


# Instância global
_backup_manager = None


def get_backup_manager(db_path: str = None) -> BackupManager:
    """Retorna instância global do gerenciador de backup"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(db_path)
    return _backup_manager
