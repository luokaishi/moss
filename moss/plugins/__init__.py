"""
MOSS Plugins
============

Plugin package for MOSS extensibility.

Available plugins:
- task_agent_plugin: Task-aware autonomous agent (5 scenarios)
"""

__version__ = "9.5.0"

# Export main plugin class
try:
    from moss.plugins.task_agent_plugin import TaskAgentPlugin
    __all__ = ["TaskAgentPlugin"]
except ImportError:
    __all__ = []
