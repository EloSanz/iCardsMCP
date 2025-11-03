from pyrsistent import pmap, pvector


def do_immutable(mutable):
    if isinstance(mutable, list):
        return pvector(do_immutable(x) for x in mutable)
    if isinstance(mutable, dict):
        return pmap({k: do_immutable(v) for k, v in mutable.items()})
    if isinstance(mutable, tuple):
        return tuple(map(do_immutable, mutable))
    return mutable
