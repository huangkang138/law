"""
路由初始化
"""

from .analysis import router as analysis_bp
from .case import router as case_bp
from .dispute import router as dispute_bp
from .document import router as document_bp
from .document_drafting import document_drafting_bp
from .health import router as health_bp
from .knowledge_graph import router as knowledge_graph_bp
from .legal import router as legal_bp
from .legal_tools import router as legal_tools_bp
from .favorites import favorites_bp
from .agent import agent_bp
from .digital_human import router as digital_human_bp
from .digital_human_agent import router as digital_human_agent_bp

__all__ = [
    'analysis_bp',
    'case_bp',
    'dispute_bp',
    'document_bp',
    'document_drafting_bp',
    'health_bp',
    'knowledge_graph_bp',
    'legal_bp',
    'legal_tools_bp',
    'favorites_bp',
    'agent_bp',
    'digital_human_bp',
    'digital_human_agent_bp'
]
