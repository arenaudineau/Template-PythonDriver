import types, functools, inspect

def method(obj):
  def copy_func(f):
      return types.FunctionType(f.__code__, f.__globals__, f.__name__, f.__defaults__, f.__closure__)
  def apply_self(fn, self, fullargspec=None):
    fullargspec = fullargspec or inspect.getfullargspec(fn)[0]
    if len(fullargspec) != 0 and fullargspec[0] == "self":
      return functools.partial(fn, obj)
    else:
      return fn
  
  def decorator(func):
    name = func.__name__
    fullargspec = inspect.getfullargspec(func)[0]
    if "parent" in fullargspec:
      if hasattr(obj, name):
        func_copy = copy_func(getattr(obj, name))
        parent = apply_self(func_copy, obj)
      else:
        raise ValueError("Unexpected argument 'parent' as the method {} does not have a default implementation".format(name))
      
      def wrapped_func(*args, **kwargs):
        func(parent=parent, *args, **kwargs)
      
    else:
      def wrapped_func(*args, **kwargs):
        func(*args, **kwargs)

    wrapped_func = apply_self(wrapped_func, obj, fullargspec)
    setattr(obj, name, wrapped_func)
    return wrapped_func
  return decorator
