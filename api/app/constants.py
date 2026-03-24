# Constantes de la aplicacion


class Limits:
    """Limites de paginacion y resultados."""
    DEFAULT = 50
    MAX = 100
    TOP = 10
    STATES = 27  # Estados de Brasil
    CATEGORIES = 15
    CITIES = 20


class OrderStatus:
    """Estados de pedido validos."""
    DELIVERED = 'delivered'
    CANCELED = 'canceled'
    SHIPPED = 'shipped'
    ALL = ['created', 'approved', 'invoiced', 'shipped', 'delivered', 'canceled']
