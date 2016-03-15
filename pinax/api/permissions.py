
def add(backends):
    def decorator(func):
        func.permissions = backends
        return func
    return decorator
