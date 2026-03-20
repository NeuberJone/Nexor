"""
Validators - Validação de dados para o frontend
Valida dados antes de enviar para o backend
"""

import re
from typing import Dict, List, Tuple, Any
from datetime import datetime

class ValidationError(Exception):
    """Exceção para erros de validação"""
    pass

class Validator:
    """Classe para validação de dados"""
    
    # Padrões de validação
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\d{10,11}$',
        'date': r'^\d{4}-\d{2}-\d{2}$',
        'datetime': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        'numeric': r'^\d+$',
        'alphanumeric': r'^[a-zA-Z0-9_-]+$',
    }
    
    @staticmethod
    def validate_required(value: Any, field_name: str = 'Campo') -> Tuple[bool, str]:
        """Valida se o campo é obrigatório"""
        if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
            return False, f"{field_name} é obrigatório"
        return True, ""
    
    @staticmethod
    def validate_string(value: str, min_length: int = 1, max_length: int = 255, 
                       field_name: str = 'Campo') -> Tuple[bool, str]:
        """Valida string"""
        if not isinstance(value, str):
            return False, f"{field_name} deve ser texto"
        
        if len(value) < min_length:
            return False, f"{field_name} deve ter no mínimo {min_length} caracteres"
        
        if len(value) > max_length:
            return False, f"{field_name} deve ter no máximo {max_length} caracteres"
        
        return True, ""
    
    @staticmethod
    def validate_integer(value: Any, min_value: int = None, max_value: int = None,
                        field_name: str = 'Campo') -> Tuple[bool, str]:
        """Valida inteiro"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False, f"{field_name} deve ser um número inteiro"
        
        if min_value is not None and int_value < min_value:
            return False, f"{field_name} deve ser no mínimo {min_value}"
        
        if max_value is not None and int_value > max_value:
            return False, f"{field_name} deve ser no máximo {max_value}"
        
        return True, ""
    
    @staticmethod
    def validate_float(value: Any, min_value: float = None, max_value: float = None,
                      field_name: str = 'Campo') -> Tuple[bool, str]:
        """Valida número decimal"""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return False, f"{field_name} deve ser um número"
        
        if min_value is not None and float_value < min_value:
            return False, f"{field_name} deve ser no mínimo {min_value}"
        
        if max_value is not None and float_value > max_value:
            return False, f"{field_name} deve ser no máximo {max_value}"
        
        return True, ""
    
    @staticmethod
    def validate_pattern(value: str, pattern: str, field_name: str = 'Campo') -> Tuple[bool, str]:
        """Valida padrão regex"""
        if not re.match(pattern, value):
            return False, f"{field_name} tem formato inválido"
        return True, ""
    
    @staticmethod
    def validate_email(value: str, field_name: str = 'Email') -> Tuple[bool, str]:
        """Valida email"""
        return Validator.validate_pattern(value, Validator.PATTERNS['email'], field_name)
    
    @staticmethod
    def validate_date(value: str, field_name: str = 'Data') -> Tuple[bool, str]:
        """Valida data (YYYY-MM-DD)"""
        is_valid, msg = Validator.validate_pattern(value, Validator.PATTERNS['date'], field_name)
        if not is_valid:
            return False, msg
        
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True, ""
        except ValueError:
            return False, f"{field_name} é inválida"
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], field_name: str = 'Campo') -> Tuple[bool, str]:
        """Valida se valor está em lista de opções"""
        if value not in choices:
            return False, f"{field_name} deve ser uma das opções: {', '.join(map(str, choices))}"
        return True, ""


class JobValidator:
    """Validador específico para Jobs"""
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados para criar job"""
        errors = []
        
        # Validar campos obrigatórios
        required_fields = ['document', 'fabric', 'height_mm', 'machine']
        for field in required_fields:
            is_valid, msg = Validator.validate_required(data.get(field), field)
            if not is_valid:
                errors.append(msg)
        
        # Validar tipos
        if 'height_mm' in data:
            is_valid, msg = Validator.validate_float(data['height_mm'], min_value=0, field_name='height_mm')
            if not is_valid:
                errors.append(msg)
        
        if 'document' in data:
            is_valid, msg = Validator.validate_string(data['document'], min_length=1, max_length=100, field_name='document')
            if not is_valid:
                errors.append(msg)
        
        return len(errors) == 0, errors


class RollValidator:
    """Validador específico para Rolos"""
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados para criar rolo"""
        errors = []
        
        # Validar campos obrigatórios
        required_fields = ['roll_name', 'fabric', 'machine']
        for field in required_fields:
            is_valid, msg = Validator.validate_required(data.get(field), field)
            if not is_valid:
                errors.append(msg)
        
        # Validar tipos
        if 'roll_name' in data:
            is_valid, msg = Validator.validate_string(data['roll_name'], min_length=1, max_length=50, field_name='roll_name')
            if not is_valid:
                errors.append(msg)
        
        if 'total_length_m' in data:
            is_valid, msg = Validator.validate_float(data['total_length_m'], min_value=0, field_name='total_length_m')
            if not is_valid:
                errors.append(msg)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_close(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados para fechar rolo"""
        errors = []
        
        # Validar campos obrigatórios
        required_fields = ['status']
        for field in required_fields:
            is_valid, msg = Validator.validate_required(data.get(field), field)
            if not is_valid:
                errors.append(msg)
        
        # Validar status
        if 'status' in data:
            is_valid, msg = Validator.validate_choice(data['status'], ['closed', 'CLOSED'], field_name='status')
            if not is_valid:
                errors.append(msg)
        
        return len(errors) == 0, errors


class MachineValidator:
    """Validador específico para Máquinas"""
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados para criar máquina"""
        errors = []
        
        # Validar campos obrigatórios
        required_fields = ['code', 'name']
        for field in required_fields:
            is_valid, msg = Validator.validate_required(data.get(field), field)
            if not is_valid:
                errors.append(msg)
        
        # Validar tipos
        if 'code' in data:
            is_valid, msg = Validator.validate_string(data['code'], min_length=1, max_length=20, field_name='code')
            if not is_valid:
                errors.append(msg)
        
        if 'name' in data:
            is_valid, msg = Validator.validate_string(data['name'], min_length=1, max_length=100, field_name='name')
            if not is_valid:
                errors.append(msg)
        
        return len(errors) == 0, errors


class FabricValidator:
    """Validador específico para Tecidos"""
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados para criar tecido"""
        errors = []
        
        # Validar campos obrigatórios
        required_fields = ['name']
        for field in required_fields:
            is_valid, msg = Validator.validate_required(data.get(field), field)
            if not is_valid:
                errors.append(msg)
        
        # Validar tipos
        if 'name' in data:
            is_valid, msg = Validator.validate_string(data['name'], min_length=1, max_length=100, field_name='name')
            if not is_valid:
                errors.append(msg)
        
        return len(errors) == 0, errors


class OperatorValidator:
    """Validador específico para Operadores"""
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados para criar operador"""
        errors = []
        
        # Validar campos obrigatórios
        required_fields = ['code', 'name']
        for field in required_fields:
            is_valid, msg = Validator.validate_required(data.get(field), field)
            if not is_valid:
                errors.append(msg)
        
        # Validar tipos
        if 'code' in data:
            is_valid, msg = Validator.validate_string(data['code'], min_length=1, max_length=20, field_name='code')
            if not is_valid:
                errors.append(msg)
        
        if 'name' in data:
            is_valid, msg = Validator.validate_string(data['name'], min_length=1, max_length=100, field_name='name')
            if not is_valid:
                errors.append(msg)
        
        return len(errors) == 0, errors
