"""
Módulo de Analytics
Calcula métricas de produção, eficiência e utilização
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from app import database as db


class ProductionAnalytics:
    """Classe para análise de produção"""
    
    @staticmethod
    def get_production_metrics(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Obtém métricas gerais de produção"""
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        rolls = db.get_rolls(status='closed')
        
        # Filtrar por data
        filtered_rolls = []
        for roll in rolls:
            try:
                closed_at = datetime.fromisoformat(roll['closed_at'])
                if date_from <= closed_at <= date_to:
                    filtered_rolls.append(roll)
            except:
                pass
        
        if not filtered_rolls:
            return {
                'total_rolls': 0,
                'total_meters': 0,
                'total_jobs': 0,
                'avg_efficiency': 0,
                'avg_roll_size': 0,
                'period_days': (date_to - date_from).days,
            }
        
        total_meters = sum(r.get('total_m', 0) for r in filtered_rolls)
        total_jobs = sum(r.get('job_count', 0) for r in filtered_rolls)
        
        return {
            'total_rolls': len(filtered_rolls),
            'total_meters': round(total_meters, 2),
            'total_jobs': total_jobs,
            'avg_efficiency': round(total_meters / len(filtered_rolls) if filtered_rolls else 0, 2),
            'avg_roll_size': round(total_meters / len(filtered_rolls) if filtered_rolls else 0, 2),
            'period_days': (date_to - date_from).days,
        }
    
    @staticmethod
    def get_machine_utilization(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Obtém utilização por máquina"""
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        rolls = db.get_rolls(status='closed')
        
        # Agrupar por máquina
        machines = {}
        for roll in rolls:
            try:
                closed_at = datetime.fromisoformat(roll['closed_at'])
                if date_from <= closed_at <= date_to:
                    machine = roll.get('machine', 'DESCONHECIDA')
                    if machine not in machines:
                        machines[machine] = {
                            'name': machine,
                            'rolls': 0,
                            'total_m': 0,
                            'total_jobs': 0,
                        }
                    machines[machine]['rolls'] += 1
                    machines[machine]['total_m'] += roll.get('total_m', 0)
                    machines[machine]['total_jobs'] += roll.get('job_count', 0)
            except:
                pass
        
        # Calcular percentuais
        total_m = sum(m['total_m'] for m in machines.values())
        for machine in machines.values():
            machine['percentage'] = round((machine['total_m'] / total_m * 100) if total_m > 0 else 0, 1)
            machine['total_m'] = round(machine['total_m'], 2)
        
        return {
            'machines': list(machines.values()),
            'total_machines': len(machines),
        }
    
    @staticmethod
    def get_fabric_distribution(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Obtém distribuição de tecidos"""
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        rolls = db.get_rolls(status='closed')
        
        # Agrupar por tecido
        fabrics = {}
        for roll in rolls:
            try:
                closed_at = datetime.fromisoformat(roll['closed_at'])
                if date_from <= closed_at <= date_to:
                    fabric = roll.get('fabric', 'DESCONHECIDO')
                    if fabric not in fabrics:
                        fabrics[fabric] = {
                            'name': fabric,
                            'rolls': 0,
                            'total_m': 0,
                        }
                    fabrics[fabric]['rolls'] += 1
                    fabrics[fabric]['total_m'] += roll.get('total_m', 0)
            except:
                pass
        
        # Calcular percentuais
        total_m = sum(f['total_m'] for f in fabrics.values())
        for fabric in fabrics.values():
            fabric['percentage'] = round((fabric['total_m'] / total_m * 100) if total_m > 0 else 0, 1)
            fabric['total_m'] = round(fabric['total_m'], 2)
        
        # Ordenar por quantidade
        sorted_fabrics = sorted(fabrics.values(), key=lambda x: x['total_m'], reverse=True)
        
        return {
            'fabrics': sorted_fabrics[:10],  # Top 10
            'total_fabrics': len(fabrics),
        }
    
    @staticmethod
    def get_daily_production(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Obtém produção diária"""
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        rolls = db.get_rolls(status='closed')
        
        # Agrupar por dia
        daily = {}
        for roll in rolls:
            try:
                closed_at = datetime.fromisoformat(roll['closed_at'])
                if date_from <= closed_at <= date_to:
                    day = closed_at.date().isoformat()
                    if day not in daily:
                        daily[day] = {
                            'date': day,
                            'rolls': 0,
                            'total_m': 0,
                        }
                    daily[day]['rolls'] += 1
                    daily[day]['total_m'] += roll.get('total_m', 0)
            except:
                pass
        
        # Formatar para gráfico
        data = []
        for day in sorted(daily.keys()):
            data.append({
                'date': day,
                'rolls': daily[day]['rolls'],
                'meters': round(daily[day]['total_m'], 2),
            })
        
        return {
            'data': data,
            'total_days': len(data),
        }
    
    @staticmethod
    def get_efficiency_metrics(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Obtém métricas de eficiência"""
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        rolls = db.get_rolls(status='closed')
        
        # Calcular eficiência
        efficiencies = []
        for roll in rolls:
            try:
                closed_at = datetime.fromisoformat(roll['closed_at'])
                if date_from <= closed_at <= date_to:
                    total_m = roll.get('total_m', 0)
                    job_count = roll.get('job_count', 1)
                    if job_count > 0:
                        efficiency = total_m / job_count
                        efficiencies.append(efficiency)
            except:
                pass
        
        if not efficiencies:
            return {
                'avg_efficiency': 0,
                'min_efficiency': 0,
                'max_efficiency': 0,
                'median_efficiency': 0,
            }
        
        efficiencies.sort()
        avg = sum(efficiencies) / len(efficiencies)
        median = efficiencies[len(efficiencies) // 2]
        
        return {
            'avg_efficiency': round(avg, 2),
            'min_efficiency': round(min(efficiencies), 2),
            'max_efficiency': round(max(efficiencies), 2),
            'median_efficiency': round(median, 2),
            'total_samples': len(efficiencies),
        }
    
    @staticmethod
    def get_comparison_periods(periods: int = 4) -> Dict[str, Any]:
        """Compara produção entre períodos"""
        
        today = datetime.now()
        period_length = 7  # Uma semana
        
        comparison = []
        for i in range(periods):
            end_date = today - timedelta(days=i * period_length)
            start_date = end_date - timedelta(days=period_length)
            
            metrics = ProductionAnalytics.get_production_metrics(start_date, end_date)
            
            comparison.append({
                'period': f"Semana {periods - i}",
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'rolls': metrics['total_rolls'],
                'meters': metrics['total_meters'],
                'jobs': metrics['total_jobs'],
            })
        
        return {
            'comparison': comparison,
        }
    
    @staticmethod
    def get_top_machines(limit: int = 5, date_from: datetime = None, date_to: datetime = None) -> List[Dict[str, Any]]:
        """Obtém máquinas com melhor desempenho"""
        
        utilization = ProductionAnalytics.get_machine_utilization(date_from, date_to)
        machines = utilization['machines']
        
        # Ordenar por metros produzidos
        sorted_machines = sorted(machines, key=lambda x: x['total_m'], reverse=True)
        
        return sorted_machines[:limit]
    
    @staticmethod
    def get_top_fabrics(limit: int = 5, date_from: datetime = None, date_to: datetime = None) -> List[Dict[str, Any]]:
        """Obtém tecidos mais produzidos"""
        
        distribution = ProductionAnalytics.get_fabric_distribution(date_from, date_to)
        fabrics = distribution['fabrics']
        
        return fabrics[:limit]
