"""Functional-style utilities."""
import inspect
import sys
import threading
from time import sleep, time
from collections import UserList
from collections import OrderedDict, UserDict
from collections.abc import Iterable, Mapping
from functools import partial
from itertools import islice, tee, zip_longest
from itertools import count

from vine import promise
from vine.utils import wraps

try:
    from functools import _NOT_FOUND
    from functools import cached_property as _cached_property
except ImportError:
    # TODO: Remove this fallback once we drop support for Python < 3.8
    from cached_property import threaded_cached_property as _cached_property

    _NOT_FOUND = object()


__all__ = (
    'LRUCache', 'is_list', 'maybe_list', 'memoize', 'mlazy', 'noop',
    'first', 'firstmethod', 'chunks', 'padlist', 'mattrgetter', 'uniq',
    'regen', 'dictfilter', 'lazy', 'maybe_evaluate', 'head_from_fun',
    'maybe', 'fun_accepts_kwargs', 'cached_property'
)

FUNHEAD_TEMPLATE = """
def {fun_name}({fun_args}):
    return {fun_value}
"""

KEYWORD_MARK = object()


class DummyContext:

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass


class lazy:
    """Holds lazy evaluation.

    Evaluated when called or if the :meth:`evaluate` method is called.
    The function is re-evaluated on every call.

    Overloaded operations that will evaluate the promise:
        :meth:`__str__`, :meth:`__repr__`, :meth:`__cmp__`.
    """

    def __init__(self, fun, *args, **kwargs):
        self._fun = fun
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        return self.evaluate()

    def evaluate(self):
        return self._fun(*self._args, **self._kwargs)

    def __str__(self):
        return str(self())

    def __repr__(self):
        return repr(self())

    def __eq__(self, rhs):
        return self() == rhs

    def __ne__(self, rhs):
        return self() != rhs

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def __reduce__(self):
        return (self.__class__, (self._fun,), {'_args': self._args,
                                               '_kwargs': self._kwargs})


class mlazy(lazy):
    """Memoized lazy evaluation.

    The function is only evaluated once, every subsequent access
    will return the same value.
    """

    #: Set to :const:`True` after the object has been evaluated.
    evaluated = False
    _value = None

    def evaluate(self):
        if not self.evaluated:
            self._value = super().evaluate()
            self.evaluated = True
        return self._value


def is_list(obj, scalars=(Mapping, str), iters=(Iterable,)):
    """Return true if the object is iterable.

    Note:
        Returns false if object is a mapping or string.
    """
    return isinstance(obj, iters) and not isinstance(obj, scalars or ())


def maybe_list(obj, scalars=(Mapping, str)):
    """Return list of one element if ``l`` is a scalar."""
    return obj if obj is None or is_list(obj, scalars) else [obj]


def maybe_evaluate(value):
    """Evaluate value only if value is a :class:`lazy` instance."""
    if isinstance(value, lazy):
        return value.evaluate()
    return value


def dictfilter(d=None, **kw):
    """Remove all keys from dict ``d`` whose value is :const:`None`."""
    d = kw if d is None else (dict(d, **kw) if kw else d)
    return {k: v for k, v in d.items() if v is not None}


def noop(*args, **kwargs):
    """No operation.

    Takes any arguments/keyword arguments and does nothing.
    """


def pass1(arg, *args, **kwargs):
    """Return the first positional argument."""
    return arg


def evaluate_promises(it):
    for value in it:
        if isinstance(value, promise):
            value = value()
        yield value


def first(predicate, it):
    """Return the first element in ``it`` that ``predicate`` accepts.

    If ``predicate`` is None it will return the first item that's not
    :const:`None`.
    """
    return next(
        (v for v in evaluate_promises(it) if (
            predicate(v) if predicate is not None else v is not None)),
        None,
    )


def firstmethod(method, on_call=None):
    """Multiple dispatch.

    Return a function that with a list of instances,
    finds the first instance that gives a value for the given method.

    The list can also contain lazy instances
    (:class:`~kombu.utils.functional.lazy`.)
    """

    def _matcher(it, *args, **kwargs):
        for obj in it:
            try:
                meth = getattr(maybe_evaluate(obj), method)
                reply = (on_call(meth, *args, **kwargs) if on_call
                         else meth(*args, **kwargs))
            except AttributeError:
                pass
            else:
                if reply is not None:
                    return reply

    return _matcher


def chunks(it, n):
    """Split an iterator into chunks with `n` elements each.

    Warning:
        ``it`` must be an actual iterator, if you pass this a
        concrete sequence will get you repeating elements.

        So ``chunks(iter(range(1000)), 10)`` is fine, but
        ``chunks(range(1000), 10)`` is not.

    Example:
        # n == 2
        >>> x = chunks(iter([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 2)
        >>> list(x)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [10]]

        # n == 3
        >>> x = chunks(iter([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 3)
        >>> list(x)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10]]
    """
    for item in it:
        yield [item] + list(islice(it, n - 1))


def padlist(container, size, default=None):
    """Pad list with default elements.

    Example:
        >>> first, last, city = padlist(['George', 'Costanza', 'NYC'], 3)
        ('George', 'Costanza', 'NYC')
        >>> first, last, city = padlist(['George', 'Costanza'], 3)
        ('George', 'Costanza', None)
        >>> first, last, city, planet = padlist(
        ...     ['George', 'Costanza', 'NYC'], 4, default='Earth',
        ... )
        ('George', 'Costanza', 'NYC', 'Earth')
    """
    return list(container)[:size] + [default] * (size - len(container))


def mattrgetter(*attrs):
    """Get attributes, ignoring attribute errors.

    Like :func:`operator.itemgetter` but return :const:`None` on missing
    attributes instead of raising :exc:`AttributeError`.
    """
    return lambda obj: {attr: getattr(obj, attr, None) for attr in attrs}


def uniq(it):
    """Return all unique elements in ``it``, preserving order."""
    seen = set()
    return (seen.add(obj) or obj for obj in it if obj not in seen)


def lookahead(it):
    """Yield pairs of (current, next) items in `it`.

    `next` is None if `current` is the last item.
    Example:
        >>> list(lookahead(x for x in range(6)))
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, None)]
    """
    a, b = tee(it)
    next(b, None)
    return zip_longest(a, b)


def regen(it):
    """Convert iterator to an object that can be consumed multiple times.

    ``Regen`` takes any iterable, and if the object is an
    generator it will cache the evaluated list on first access,
    so that the generator can be "consumed" multiple times.
    """
    if isinstance(it, (list, tuple)):
        return it
    return _regen(it)


class _regen(UserList, list):
    # must be subclass of list so that json can encode.

    def __init__(self, it):
        # pylint: disable=super-init-not-called
        # UserList creates a new list and sets .data, so we don't
        # want to call init here.
        self.__it = it
        self.__consumed = []
        self.__done = False

    def __reduce__(self):
        return list, (self.data,)

    def __length_hint__(self):
        return self.__it.__length_hint__()

    def __lookahead_consume(self, limit=None):
        if not self.__done and (limit is None or limit > 0):
            it = iter(self.__it)
            try:
                now = next(it)
            except StopIteration:
                return
            self.__consumed.append(now)
            # Maintain a single look-ahead to ensure we set `__done` when the
            # underlying iterator gets exhausted
            while not self.__done:
                try:
                    next_ = next(it)
                    self.__consumed.append(next_)
                except StopIteration:
                    self.__done = True
                    break
                finally:
                    yield now
                now = next_
                # We can break out when `limit` is exhausted
                if limit is not None:
                    limit -= 1
                    if limit <= 0:
                        break

    def __iter__(self):
        yield from self.__consumed
        yield from self.__lookahead_consume()

    def __getitem__(self, index):
        if index < 0:
            return self.data[index]
        # Consume elements up to the desired index prior to attempting to
        # access it from within `__consumed`
        consume_count = index - len(self.__consumed) + 1
        for _ in self.__lookahead_consume(limit=consume_count):
            pass
        return self.__consumed[index]

    def __bool__(self):
        if len(self.__consumed):
            return True

        try:
            next(iter(self))
        except StopIteration:
            return False
        else:
            return True

    @property
    def data(self):
        if not self.__done:
            self.__consumed.extend(self.__it)
            self.__done = True
        return self.__consumed

    def __repr__(self):
        return "<{}: [{}{}]>".format(
            self.__class__.__name__,
            ", ".join(repr(e) for e in self.__consumed),
            "..." if not self.__done else "",
        )


def _argsfromspec(spec, replace_defaults=True):
    if spec.defaults:
        split = len(spec.defaults)
        defaults = (list(range(len(spec.defaults))) if replace_defaults
                    else spec.defaults)
        positional = spec.args[:-split]
        optional = list(zip(spec.args[-split:], defaults))
    else:
        positional, optional = spec.args, []

    varargs = spec.varargs
    varkw = spec.varkw
    if spec.kwonlydefaults:
        kwonlyargs = set(spec.kwonlyargs) - set(spec.kwonlydefaults.keys())
        if replace_defaults:
            kwonlyargs_optional = [
                (kw, i) for i, kw in enumerate(spec.kwonlydefaults.keys())
            ]
        else:
            kwonlyargs_optional = list(spec.kwonlydefaults.items())
    else:
        kwonlyargs, kwonlyargs_optional = spec.kwonlyargs, []

    return ', '.join(filter(None, [
        ', '.join(positional),
        ', '.join(f'{k}={v}' for k, v in optional),
        f'*{varargs}' if varargs else None,
        '*' if (kwonlyargs or kwonlyargs_optional) and not varargs else None,
        ', '.join(kwonlyargs) if kwonlyargs else None,
        ', '.join(f'{k}="{v}"' for k, v in kwonlyargs_optional),
        f'**{varkw}' if varkw else None,
    ]))


def head_from_fun(fun, bound=False, debug=False):
    """Generate signature function from actual function."""
    # we could use inspect.Signature here, but that implementation
    # is very slow since it implements the argument checking
    # in pure-Python.  Instead we use exec to create a new function
    # with an empty body, meaning it has the same performance as
    # as just calling a function.
    is_function = inspect.isfunction(fun)
    is_callable = hasattr(fun, '__call__')
    is_cython = fun.__class__.__name__ == 'cython_function_or_method'
    is_method = inspect.ismethod(fun)

    if not is_function and is_callable and not is_method and not is_cython:
        name, fun = fun.__class__.__name__, fun.__call__
    else:
        name = fun.__name__
    definition = FUNHEAD_TEMPLATE.format(
        fun_name=name,
        fun_args=_argsfromspec(inspect.getfullargspec(fun)),
        fun_value=1,
    )
    if debug:  # pragma: no cover
        print(definition, file=sys.stderr)
    namespace = {'__name__': fun.__module__}
    # pylint: disable=exec-used
    # Tasks are rarely, if ever, created at runtime - exec here is fine.
    exec(definition, namespace)
    result = namespace[name]
    result._source = definition
    if bound:
        return partial(result, object())
    return result


def arity_greater(fun, n):
    argspec = inspect.getfullargspec(fun)
    return argspec.varargs or len(argspec.args) > n


def fun_takes_argument(name, fun, position=None):
    spec = inspect.getfullargspec(fun)
    return (
        spec.varkw or spec.varargs or
        (len(spec.args) >= position if position else name in spec.args)
    )


def fun_accepts_kwargs(fun):
    """Return true if function accepts arbitrary keyword arguments."""
    return any(
        p for p in inspect.signature(fun).parameters.values()
        if p.kind == p.VAR_KEYWORD
    )


def maybe(typ, val):
    """Call typ on value if val is defined."""
    return typ(val) if val is not None else val


def seq_concat_item(seq, item):
    """Return copy of sequence seq with item added.

    Returns:
        Sequence: if seq is a tuple, the result will be a tuple,
           otherwise it depends on the implementation of ``__add__``.
    """
    return seq + (item,) if isinstance(seq, tuple) else seq + [item]


def seq_concat_seq(a, b):
    """Concatenate two sequences: ``a + b``.

    Returns:
        Sequence: The return value will depend on the largest sequence
            - if b is larger and is a tuple, the return value will be a tuple.
            - if a is larger and is a list, the return value will be a list,
    """
    # find the type of the largest sequence
    prefer = type(max([a, b], key=len))
    # convert the smallest list to the type of the largest sequence.
    if not isinstance(a, prefer):
        a = prefer(a)
    if not isinstance(b, prefer):
        b = prefer(b)
    return a + b


class LRUCache(UserDict):
    """LRU Cache implementation using a doubly linked list to track access.

    Arguments:
        limit (int): The maximum number of keys to keep in the cache.
            When a new key is inserted and the limit has been exceeded,
            the *Least Recently Used* key will be discarded from the
            cache.
    """

    def __init__(self, limit=None):
        self.limit = limit
        self.mutex = threading.RLock()
        self.data = OrderedDict()

    def __getitem__(self, key):
        with self.mutex:
            value = self[key] = self.data.pop(key)
            return value

    def update(self, *args, **kwargs):
        with self.mutex:
            data, limit = self.data, self.limit
            data.update(*args, **kwargs)
            if limit and len(data) > limit:
                # pop additional items in case limit exceeded
                for _ in range(len(data) - limit):
                    data.popitem(last=False)

    def popitem(self, last=True):
        with self.mutex:
            return self.data.popitem(last)

    def __setitem__(self, key, value):
        # remove least recently used key.
        with self.mutex:
            if self.limit and len(self.data) >= self.limit:
                self.data.pop(next(iter(self.data)))
            self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def _iterate_items(self):
        with self.mutex:
            for k in self:
                try:
                    yield (k, self.data[k])
                except KeyError:  # pragma: no cover
                    pass
    iteritems = _iterate_items

    def _iterate_values(self):
        with self.mutex:
            for k in self:
                try:
                    yield self.data[k]
                except KeyError:  # pragma: no cover
                    pass

    itervalues = _iterate_values

    def _iterate_keys(self):
        # userdict.keys in py3k calls __getitem__
        with self.mutex:
            return self.data.keys()
    iterkeys = _iterate_keys

    def incr(self, key, delta=1):
        with self.mutex:
            # this acts as memcached does- store as a string, but return a
            # integer as long as it exists and we can cast it
            newval = int(self.data.pop(key)) + delta
            self[key] = str(newval)
            return newval

    def __getstate__(self):
        d = dict(vars(self))
        d.pop('mutex')
        return d

    def __setstate__(self, state):
        self.__dict__ = state
        self.mutex = threading.RLock()

    keys = _iterate_keys
    values = _iterate_values
    items = _iterate_items


def memoize(maxsize=None, keyfun=None, Cache=LRUCache):
    """Decorator to cache function return value."""
    def _memoize(fun):
        mutex = threading.Lock()
        cache = Cache(limit=maxsize)

        @wraps(fun)
        def _M(*args, **kwargs):
            if keyfun:
                key = keyfun(args, kwargs)
            else:
                key = args + (KEYWORD_MARK,) + tuple(sorted(kwargs.items()))
            try:
                with mutex:
                    value = cache[key]
            except KeyError:
                value = fun(*args, **kwargs)
                _M.misses += 1
                with mutex:
                    cache[key] = value
            else:
                _M.hits += 1
            return value

        def clear():
            """Clear the cache and reset cache statistics."""
            cache.clear()
            _M.hits = _M.misses = 0

        _M.hits = _M.misses = 0
        _M.clear = clear
        _M.original_func = fun
        return _M

    return _memoize


class cached_property(_cached_property):
    """Implementation of Cached property."""

    def __init__(self, fget=None, fset=None, fdel=None):
        super().__init__(fget)
        self.__set = fset
        self.__del = fdel

        if not hasattr(self, 'attrname'):
            # This is a backport so we set this ourselves.
            self.attrname = self.func.__name__

    def __get__(self, instance, owner=None):
        # TODO: Remove this after we drop support for Python<3.8
        #  or fix the signature in the cached_property package
        return super().__get__(instance, owner)

    def __set__(self, instance, value):
        if instance is None:
            return self

        with self.lock:
            if self.__set is not None:
                value = self.__set(instance, value)

            cache = instance.__dict__
            cache[self.attrname] = value

    def __delete__(self, instance):
        if instance is None:
            return self

        with self.lock:
            value = instance.__dict__.pop(self.attrname, _NOT_FOUND)

            if self.__del and value is not _NOT_FOUND:
                self.__del(instance, value)

    def setter(self, fset):
        return self.__class__(self.func, fset, self.__del)

    def deleter(self, fdel):
        return self.__class__(self.func, self.__set, fdel)


def fxrange(start=1.0, stop=None, step=1.0, repeatlast=False):
    cur = start * 1.0
    while 1:
        if not stop or cur <= stop:
            yield cur
            cur += step
        else:
            if not repeatlast:
                break
            yield cur - step


def fxrangemax(start=1.0, stop=None, step=1.0, max=100.0):
    sum_, cur = 0, start * 1.0
    while 1:
        if sum_ >= max:
            break
        yield cur
        if stop:
            cur = min(cur + step, stop)
        else:
            cur += step
        sum_ += cur


def retry_over_time(fun, catch, args=None, kwargs=None, errback=None,
                    max_retries=None, interval_start=2, interval_step=2,
                    interval_max=30, callback=None, timeout=None):
    """Retry the function over and over until max retries is exceeded.

    For each retry we sleep a for a while before we try again, this interval
    is increased for every retry until the max seconds is reached.

    Arguments:
        fun (Callable): The function to try
        catch (Tuple[BaseException]): Exceptions to catch, can be either
            tuple or a single exception class.

    Keyword Arguments:
        args (Tuple): Positional arguments passed on to the function.
        kwargs (Dict): Keyword arguments passed on to the function.
        errback (Callable): Callback for when an exception in ``catch``
            is raised.  The callback must take three arguments:
            ``exc``, ``interval_range`` and ``retries``, where ``exc``
            is the exception instance, ``interval_range`` is an iterator
            which return the time in seconds to sleep next, and ``retries``
            is the number of previous retries.
        max_retries (int): Maximum number of retries before we give up.
            If neither of this and timeout is set, we will retry forever.
            If one of this and timeout is reached, stop.
        interval_start (float): How long (in seconds) we start sleeping
            between retries.
        interval_step (float): By how much the interval is increased for
            each retry.
        interval_max (float): Maximum number of seconds to sleep
            between retries.
        timeout (int): Maximum seconds waiting before we give up.
    """
    kwargs = {} if not kwargs else kwargs
    args = [] if not args else args
    interval_range = fxrange(interval_start,
                             interval_max + interval_start,
                             interval_step, repeatlast=True)
    end = time() + timeout if timeout else None
    for retries in count():
        try:
            return fun(*args, **kwargs)
        except catch as exc:
            if max_retries is not None and retries >= max_retries:
                raise
            if end and time() > end:
                raise
            if callback:
                callback()
            tts = float(errback(exc, interval_range, retries) if errback
                        else next(interval_range))
            if tts:
                for _ in range(int(tts)):
                    if callback:
                        callback()
                    sleep(1.0)
                # sleep remainder after int truncation above.
                sleep(abs(int(tts) - tts))
