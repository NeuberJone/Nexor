"""
Módulo de Sincronização
Sincroniza dados com backend Python existente
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from app import database as db


class SyncManager:
    """Gerenciador de sincronização com backend Python"""
    
    def __init__(self, backend_url: str = None):
        """Inicializa o gerenciador de sincronização"""
        self.backend_url = backend_url or os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')
        self.timeout = 10
        self.last_sync = None
        self.sync_status = 'idle'
    
    def check_backend_health(self) -> Dict[str, Any]:
        """Verifica saúde do backend Python"""
        try:
            response = requests.get(f'{self.backend_url}/status', timeout=self.timeout)
            if response.status_code == 200:
                return {
                    'ok': True,
                    'status': 'online',
                    'backend_url': self.backend_url,
                    'timestamp': datetime.now().isoformat(),
                }
            else:
                return {
                    'ok': False,
                    'status': 'offline',
                    'error': f'Status code: {response.status_code}',
                    'timestamp': datetime.now().isoformat(),
                }
        except requests.exceptions.RequestException as e:
            return {
                'ok': False,
                'status': 'unreachable',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def sync_jobs_from_backend(self) -> Dict[str, Any]:
        """Sincroniza jobs do backend Python"""
        try:
            self.sync_status = 'syncing_jobs'
            
            # Buscar jobs do backend
            response = requests.get(f'{self.backend_url}/jobs?limit=1000', timeout=self.timeout)
            
            if response.status_code != 200:
                return {
                    'ok': False,
                    'error': f'Backend retornou status {response.status_code}',
                }
            
            jobs = response.json().get('jobs', [])
            
            # Inserir jobs no banco local
            inserted = 0
            for job in jobs:
                try:
                    db.insert_job(
                        document=job.get('document', ''),
                        fabric=job.get('fabric', ''),
                        height_mm=job.get('height_mm', 0),
                        vpos_mm=job.get('vpos_mm', 0),
                        real_m=job.get('real_m', 0),
                        end_time=job.get('end_time', datetime.now().isoformat()),
                        src_file=job.get('src_file', 'backend_sync'),
                    )
                    inserted += 1
                except Exception as e:
                    print(f'Erro ao inserir job: {e}')
            
            self.sync_status = 'idle'
            self.last_sync = datetime.now()
            
            return {
                'ok': True,
                'inserted': inserted,
                'total': len(jobs),
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            self.sync_status = 'error'
            return {
                'ok': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def sync_rolls_to_backend(self) -> Dict[str, Any]:
        """Sincroniza rolos para o backend Python"""
        try:
            self.sync_status = 'syncing_rolls'
            
            # Buscar rolos fechados
            rolls = db.get_rolls(status='closed')
            
            # Enviar para backend
            synced = 0
            for roll in rolls:
                try:
                    payload = {
                        'roll_name': roll.get('roll_name', ''),
                        'machine': roll.get('machine', ''),
                        'fabric': roll.get('fabric', ''),
                        'total_m': roll.get('total_m', 0),
                        'job_count': roll.get('job_count', 0),
                        'closed_at': roll.get('closed_at', datetime.now().isoformat()),
                    }
                    
                    response = requests.post(
                        f'{self.backend_url}/rolls',
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code in [200, 201]:
                        synced += 1
                except Exception as e:
                    print(f'Erro ao sincronizar rolo: {e}')
            
            self.sync_status = 'idle'
            self.last_sync = datetime.now()
            
            return {
                'ok': True,
                'synced': synced,
                'total': len(rolls),
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            self.sync_status = 'error'
            return {
                'ok': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def sync_metrics_from_backend(self) -> Dict[str, Any]:
        """Sincroniza métricas do backend Python"""
        try:
            response = requests.get(f'{self.backend_url}/metrics', timeout=self.timeout)
            
            if response.status_code != 200:
                return {
                    'ok': False,
                    'error': f'Backend retornou status {response.status_code}',
                }
            
            metrics = response.json()
            
            return {
                'ok': True,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
    
    def full_sync(self) -> Dict[str, Any]:
        """Realiza sincronização completa"""
        try:
            self.sync_status = 'syncing'
            
            results = {
                'jobs': self.sync_jobs_from_backend(),
                'rolls': self.sync_rolls_to_backend(),
                'metrics': self.sync_metrics_from_backend(),
                'timestamp': datetime.now().isoformat(),
            }
            
            self.sync_status = 'idle'
            self.last_sync = datetime.now()
            
            return {
                'ok': True,
                'results': results,
            }
        
        except Exception as e:
            self.sync_status = 'error'
            return {
                'ok': False,
                'error': str(e),
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Retorna status de sincronização"""
        return {
            'status': self.sync_status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'backend_url': self.backend_url,
            'backend_health': self.check_backend_health(),
        }


# Instância global
_sync_manager = None


def get_sync_manager() -> SyncManager:
    """Retorna instância global do gerenciador de sincronização"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
