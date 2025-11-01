from pyrsistent import pmap, pvector


def do_immutable(mutable):
    if isinstance(mutable, list):
        return pvector(map(lambda x: do_immutable(x), mutable))
    elif isinstance(mutable, dict):
        return pmap({k: do_immutable(v) for k, v in mutable.items()})
    elif isinstance(mutable, tuple):
        return tuple(map(do_immutable, mutable))
    else:
        return mutable
