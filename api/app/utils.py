# Utilidades comunes para routers

def truncate_id(id_str: str, length: int = 8) -> str:
    """Trunca un ID largo para mostrar en respuestas."""
    if not id_str or len(id_str) <= length:
        return id_str
    return f"{id_str[:length]}..."


def safe_float(value, default: float = 0.0) -> float:
    """Convierte valor a float de forma segura."""
    return float(value) if value else default


def safe_int(value, default: int = 0) -> int:
    """Convierte valor a int de forma segura."""
    return int(value) if value else default


def safe_round(value, decimals: int = 2) -> float:
    """Redondea valor de forma segura."""
    return round(float(value), decimals) if value else 0.0
