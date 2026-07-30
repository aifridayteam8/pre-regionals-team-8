from .auth_routes import auth_ns
from .incident_routes import incident_ns
from .report_routes import report_ns
from .analytics_routes import analytics_ns

__all__ = ['auth_ns', 'incident_ns', 'report_ns', 'analytics_ns']
