import sys

# Backward compatibility alias for 'core' top-level import
sys.modules.setdefault('core', sys.modules[__name__])
