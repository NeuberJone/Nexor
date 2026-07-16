"""
Backend Client - Integração com ProjetoJocasta
Camada de comunicação entre a interface Flask e o backend Python existente
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class BackendClient:
    """Cliente para comunicação com o backend Python (ProjetoJocasta)"""
    
    def __init__(self, base_url: str = None):
        """
        Inicializa o cliente do backend
        
        Args:
            base_url: URL base do backend (ex: http://localhost:5000)
        """
        self.base_url = base_url or os.getenv('BACKEND_URL', 'http://localhost:5000')
        self.timeout = 10
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Faz uma requisição HTTP ao backend
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Endpoint da API (ex: /api/jobs)
            **kwargs: Argumentos adicionais (params, json, etc)
            
        Returns:
            Resposta JSON ou dicionário com erro
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão com backend: {e}")
            return {'error': 'Backend indisponível', 'status': 'offline'}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout na requisição: {e}")
            return {'error': 'Timeout na requisição', 'status': 'timeout'}
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP: {e}")
            return {'error': str(e), 'status': 'error'}
        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
            return {'error': str(e), 'status': 'error'}
    
    # ==================== Jobs ====================
    
    def get_jobs(self, limit: int = 1000, offset: int = 0, **filters) -> List[Dict]:
        """
        Obtém lista de jobs do backend
        
        Args:
            limit: Limite de resultados
            offset: Offset para paginação
            **filters: Filtros adicionais (machine, fabric, status, etc)
            
        Returns:
            Lista de jobs
        """
        params = {'limit': limit, 'offset': offset}
        params.update(filters)
        
        response = self._make_request('GET', '/api/jobs', params=params)
        return response if isinstance(response, list) else response.get('jobs', [])
    
    def get_job(self, job_id: int) -> Dict:
        """Obtém detalhes de um job específico"""
        return self._make_request('GET', f'/api/jobs/{job_id}')
    
    def create_job(self, job_data: Dict) -> Dict:
        """Cria um novo job"""
        return self._make_request('POST', '/api/jobs', json=job_data)
    
    def update_job(self, job_id: int, job_data: Dict) -> Dict:
        """Atualiza um job existente"""
        return self._make_request('PUT', f'/api/jobs/{job_id}', json=job_data)
    
    # ==================== Rolls ====================
    
    def get_rolls(self, limit: int = 100, offset: int = 0, **filters) -> List[Dict]:
        """
        Obtém lista de rolos
        
        Args:
            limit: Limite de resultados
            offset: Offset para paginação
            **filters: Filtros (status, machine, fabric, etc)
            
        Returns:
            Lista de rolos
        """
        params = {'limit': limit, 'offset': offset}
        params.update(filters)
        
        response = self._make_request('GET', '/api/rolls', params=params)
        return response if isinstance(response, list) else response.get('rolls', [])
    
    def get_roll(self, roll_id: int) -> Dict:
        """Obtém detalhes de um rolo específico"""
        return self._make_request('GET', f'/api/rolls/{roll_id}')
    
    def create_roll(self, roll_data: Dict) -> Dict:
        """Cria um novo rolo"""
        return self._make_request('POST', '/api/rolls', json=roll_data)
    
    def close_roll(self, roll_id: int, close_data: Dict = None) -> Dict:
        """Fecha um rolo"""
        return self._make_request('POST', f'/api/rolls/{roll_id}/close', json=close_data or {})
    
    def export_roll(self, roll_id: int, format: str = 'pdf') -> Dict:
        """Exporta um rolo em PDF ou JPG"""
        return self._make_request('GET', f'/api/rolls/{roll_id}/export', params={'format': format})
    
    # ==================== Suspects ====================
    
    def get_suspects(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Obtém lista de jobs suspeitos"""
        params = {'limit': limit, 'offset': offset}
        response = self._make_request('GET', '/api/suspects', params=params)
        return response if isinstance(response, list) else response.get('suspects', [])
    
    def get_suspect(self, suspect_id: int) -> Dict:
        """Obtém detalhes de um suspeito"""
        return self._make_request('GET', f'/api/suspects/{suspect_id}')
    
    def review_suspect(self, suspect_id: int, review_data: Dict) -> Dict:
        """Revisa um job suspeito"""
        return self._make_request('POST', f'/api/suspects/{suspect_id}/review', json=review_data)
    
    # ==================== Master Data ====================
    
    def get_machines(self) -> List[Dict]:
        """Obtém lista de máquinas"""
        response = self._make_request('GET', '/api/machines')
        return response if isinstance(response, list) else response.get('machines', [])
    
    def get_machine(self, machine_id: int) -> Dict:
        """Obtém detalhes de uma máquina"""
        return self._make_request('GET', f'/api/machines/{machine_id}')
    
    def create_machine(self, machine_data: Dict) -> Dict:
        """Cria uma nova máquina"""
        return self._make_request('POST', '/api/machines', json=machine_data)
    
    def get_fabrics(self) -> List[Dict]:
        """Obtém lista de tecidos"""
        response = self._make_request('GET', '/api/fabrics')
        return response if isinstance(response, list) else response.get('fabrics', [])
    
    def get_fabric(self, fabric_id: int) -> Dict:
        """Obtém detalhes de um tecido"""
        return self._make_request('GET', f'/api/fabrics/{fabric_id}')
    
    def create_fabric(self, fabric_data: Dict) -> Dict:
        """Cria um novo tecido"""
        return self._make_request('POST', '/api/fabrics', json=fabric_data)
    
    def get_operators(self) -> List[Dict]:
        """Obtém lista de operadores"""
        response = self._make_request('GET', '/api/operators')
        return response if isinstance(response, list) else response.get('operators', [])
    
    def get_operator(self, operator_id: int) -> Dict:
        """Obtém detalhes de um operador"""
        return self._make_request('GET', f'/api/operators/{operator_id}')
    
    def create_operator(self, operator_data: Dict) -> Dict:
        """Cria um novo operador"""
        return self._make_request('POST', '/api/operators', json=operator_data)
    
    # ==================== Metrics & Analytics ====================
    
    def get_metrics(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Obtém métricas de produção
        
        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            
        Returns:
            Dicionário com métricas
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        return self._make_request('GET', '/api/metrics', params=params)
    
    def get_production_summary(self) -> Dict:
        """Obtém resumo de produção"""
        return self._make_request('GET', '/api/metrics/summary')
    
    def get_machine_utilization(self) -> List[Dict]:
        """Obtém utilização de máquinas"""
        response = self._make_request('GET', '/api/metrics/machines')
        return response if isinstance(response, list) else response.get('machines', [])
    
    def get_fabric_distribution(self) -> List[Dict]:
        """Obtém distribuição de tecidos"""
        response = self._make_request('GET', '/api/metrics/fabrics')
        return response if isinstance(response, list) else response.get('fabrics', [])
    
    # ==================== Import & Logs ====================
    
    def import_logs(self, file_path: str) -> Dict:
        """Importa arquivo de logs"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            return self._make_request('POST', '/api/import', files=files)
    
    def get_import_history(self) -> List[Dict]:
        """Obtém histórico de importações"""
        response = self._make_request('GET', '/api/import/history')
        return response if isinstance(response, list) else response.get('history', [])
    
    # ==================== Health & Status ====================
    
    def health_check(self) -> Dict:
        """Verifica saúde do backend"""
        response = self._make_request('GET', '/api/health')
        return response or {'status': 'offline', 'error': 'Backend indisponível'}
    
    def get_status(self) -> Dict:
        """Obtém status do sistema"""
        return self._make_request('GET', '/api/status')
    
    # ==================== Sync ====================
    
    def sync_data(self, data_type: str = 'all') -> Dict:
        """
        Sincroniza dados com o backend
        
        Args:
            data_type: Tipo de dados (jobs, rolls, metrics, all)
            
        Returns:
            Resultado da sincronização
        """
        return self._make_request('POST', '/api/sync', json={'type': data_type})


# Instância global do cliente
_backend_client = None

def get_backend_client() -> BackendClient:
    """Obtém instância global do cliente"""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendClient()
    return _backend_client

def set_backend_url(url: str):
    """Define URL do backend"""
    global _backend_client
    _backend_client = BackendClient(url)
