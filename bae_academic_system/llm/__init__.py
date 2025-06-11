import sys

# Backward compatibility alias for 'llm' top-level import
sys.modules.setdefault('llm', sys.modules[__name__])
