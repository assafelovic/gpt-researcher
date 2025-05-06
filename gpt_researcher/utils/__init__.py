
def check_pkg(pkg: str) -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec(pkg) is not None
    except ImportError:
        return False
