#!/usr/bin/env python3
"""
obtain the HTML content of a particular URL and returns it.
"""
from functools import wraps
from typing import Callable
import requests
import redis


my_db = redis.Redis()


def data_cacher(method: Callable) -> Callable:
    """
    decorator to cache the results of a function call for a
    given period of time
    """

    @wraps(method)
    def wrapper(url) -> str:
        """
        gets the result of a function call from the cache for a given period
        of time
        """
        my_db.incr(f'count:{url}')
        result = my_db.get(f'result:{url}')
        if result:
            return result.decode('utf-8')
        result = method(url)
        my_db.set(f'count:{url}', 0)
        my_db.setex(f'result:{url}', 10, result)
        return result
    return wrapper


@data_cacher
def get_page(url: str) -> str:
    """
    gets the content of a web page, with data caching
    for a given period of time
    """
    return requests.get(url).text
