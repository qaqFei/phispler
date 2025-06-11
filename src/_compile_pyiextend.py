import importlib.metadata

_version = importlib.metadata.version
def _new_version(n):
    v = _version(n)
    if v is not None: return v
    raise importlib.metadata.PackageNotFoundError(n)
importlib.metadata.version = _new_version

