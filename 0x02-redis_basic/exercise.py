#!/usr/bin/env python3
"""
using redis for basic operations and as a simple cache
"""
import uuid
from typing import Any, Callable, Union
from functools import wraps
import redis


def replay(fn: Callable) -> None:
    """
    displays the history of calls of a particular function
    """
    if fn is None or not hasattr(fn, '__self__'):
        return
    my_db = getattr(fn.__self__, '_redis', None)
    if not isinstance(my_db, redis.Redis):
        return
    func = fn.__qualname__
    input_key = f"{func}:inputs"
    output_key = f"{func}:outputs"
    count = 0
    if my_db.exists(func) != 0:
        count = int(my_db.get(func))
    print(f"{func} was called {count} times:")
    data_input = my_db.lrange(input_key, 0, -1)
    data_output = my_db.lrange(output_key, 0, -1)
    for i, o in zip(data_input, data_output):
        print(f"{func}(*{i.decode('utf-8')}) -> {o}")


def call_history(method: Callable) -> Callable:
    """
    stores history of inputs and outputs for particular function
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> Any:
        """
        adds output and input parameters to different lists in redis
        """
        input_key = f"{method.__qualname__}:inputs"
        output_key = "{method.__qualname__}:outputs"
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(input_key, str(args))
        output = method(self, *args, **kwargs)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(output_key, output)
        return output
    return wrapper


def count_calls(method: Callable) -> Callable:
    """
    returns the value returned by the original method
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> Any:
        """
        increments the count for that key every time the method is called
        """
        if isinstance(self._redis, redis.Redis):
            self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return wrapper


class Cache:
    """
    creates and flushes instances of the Redis client
    """

    def __init__(self) -> None:
        """
        creates and flushes instances of the Redis client
        """
        self._redis = redis.Redis()
        self._redis.flushdb(True)

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        generate a random key (e.g. using uuid), store the input data
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Callable = None
            ) -> Union[str, bytes, int, float]:
        """
        converts the data back to the desired format
        """
        data = self._redis.get(key)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> str:
        """
        parametrizes Cache.get with string
        """
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> int:
        """
        parametrizes Cache.get with integer
        """
        return self.get(key, lambda x: int(x))
