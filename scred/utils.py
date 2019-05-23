"""
scred/utils.py

Various utilities we'll want at multiple points.
"""

import logging
from urllib.parse import urlparse

# Found on StackOverflow, will fail some edge cases but generally useful
def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# Found this online and it's cool. Not used for anything yet
class LogMixin(object):
    @property
    def logger(self):
        name = '.'.join([self.__module__, self.__class__.__name__])
        FORMAT = '%(name)s:%(levelname)s:%(message)s'
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
        logger = logging.getLogger(name)
        return logger
