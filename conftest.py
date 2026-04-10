"""Root conftest so pytest adds the project root to sys.path.

This lets tests import `backend.*` and `call_center_mcp.*` without any
sys.path manipulation inside the test modules themselves.
"""
