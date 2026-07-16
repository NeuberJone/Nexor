"""
Error Handler - Tratamento robusto de erros
Centraliza tratamento de erros e retorna respostas padronizadas
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from flask import jsonify, request

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Exceção base para erros da API"""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Erro de validação"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 400, 'VALIDATION_ERROR', details)


class NotFoundError(APIError):
    """Recurso não encontrado"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 404, 'NOT_FOUND', details)


class BackendError(APIError):
    """Erro ao comunicar com backend"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 502, 'BACKEND_ERROR', details)


class DatabaseError(APIError):
    """Erro de banco de dados"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 500, 'DATABASE_ERROR', details)


class ErrorResponse:
    """Classe para construir respostas de erro padronizadas"""
    
    @staticmethod
    def success(data: Any = None, message: str = 'Sucesso', status_code: int = 200) -> Tuple[Dict, int]:
        """Retorna resposta de sucesso"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'error': None
        }, status_code
    
    @staticmethod
    def error(message: str, error_code: str = 'ERROR', status_code: int = 400, 
             details: Dict = None, data: Any = None) -> Tuple[Dict, int]:
        """Retorna resposta de erro"""
        return {
            'success': False,
            'message': message,
            'error': {
                'code': error_code,
                'details': details or {}
            },
            'data': data
        }, status_code
    
    @staticmethod
    def validation_error(errors: list, message: str = 'Erro de validação') -> Tuple[Dict, int]:
        """Retorna erro de validação"""
        return {
            'success': False,
            'message': message,
            'error': {
                'code': 'VALIDATION_ERROR',
                'details': {'errors': errors}
            },
            'data': None
        }, 400
    
    @staticmethod
    def backend_error(message: str = 'Erro ao comunicar com backend') -> Tuple[Dict, int]:
        """Retorna erro de backend"""
        return {
            'success': False,
            'message': message,
            'error': {
                'code': 'BACKEND_ERROR',
                'details': {}
            },
            'data': None
        }, 502


def handle_errors(f):
    """Decorator para tratamento automático de erros em rotas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {e.message} (code: {e.error_code})")
            return ErrorResponse.error(
                e.message,
                e.error_code,
                e.status_code,
                e.details
            )
        except ValueError as e:
            logger.warning(f"Validation Error: {str(e)}")
            return ErrorResponse.error(
                str(e),
                'VALIDATION_ERROR',
                400
            )
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}\n{traceback.format_exc()}")
            return ErrorResponse.error(
                'Erro interno do servidor',
                'INTERNAL_ERROR',
                500
            )
    
    return decorated_function


def safe_request_json(required_fields: list = None):
    """Decorator para validar JSON da requisição"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
            except Exception as e:
                logger.warning(f"Invalid JSON: {str(e)}")
                return ErrorResponse.error(
                    'JSON inválido',
                    'INVALID_JSON',
                    400
                )
            
            if data is None:
                return ErrorResponse.error(
                    'Corpo da requisição vazio',
                    'EMPTY_BODY',
                    400
                )
            
            # Validar campos obrigatórios
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return ErrorResponse.error(
                        f"Campos obrigatórios faltando: {', '.join(missing_fields)}",
                        'MISSING_FIELDS',
                        400,
                        {'missing_fields': missing_fields}
                    )
            
            return f(data, *args, **kwargs)
        
        return decorated_function
    return decorator


def log_request(f):
    """Decorator para logar requisições"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"{request.method} {request.path} - IP: {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function


class ErrorLogger:
    """Classe para logging centralizado de erros"""
    
    @staticmethod
    def log_backend_error(endpoint: str, error: str, response: Dict = None):
        """Loga erro de comunicação com backend"""
        logger.error(f"Backend Error - Endpoint: {endpoint}, Error: {error}, Response: {response}")
    
    @staticmethod
    def log_database_error(operation: str, error: str):
        """Loga erro de banco de dados"""
        logger.error(f"Database Error - Operation: {operation}, Error: {error}")
    
    @staticmethod
    def log_validation_error(field: str, error: str):
        """Loga erro de validação"""
        logger.warning(f"Validation Error - Field: {field}, Error: {error}")
    
    @staticmethod
    def log_exception(exception: Exception, context: str = ""):
        """Loga exceção com contexto"""
        logger.error(f"Exception ({context}): {str(exception)}\n{traceback.format_exc()}")
