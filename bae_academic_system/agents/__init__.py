import sys

# Expose this package as top-level 'agents' for backward compatibility in tests
sys.modules.setdefault('agents', sys.modules[__name__])
