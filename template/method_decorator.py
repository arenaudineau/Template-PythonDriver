import types, functools, inspect

def method(obj):
  def copy_func(f):
      return types.FunctionType(f.__code__, f.__globals__, f.__name__, f.__defaults__, f.__closure__)
    
  def decorator(func):
    name = func.__name__
    if "parent" in inspect.getfullargspec(func)[0]:
      if hasattr(obj, name):
        parent = functools.partial(copy_func(getattr(obj, name)), obj)
      else:
        raise ValueError("Unexpected argument 'parent' as the method {} does not have a default implementation".format(name))
      
      def wrapped_func(*args, **kwargs):
        func(parent=parent, *args, **kwargs)
      
    else:
      def wrapped_func(*args, **kwargs):
        func(*args, **kwargs)

    setattr(obj, name, wrapped_func)

    return wrapped_func
  return decorator