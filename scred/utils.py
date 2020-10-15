"""
scred/utils.py

Various utilities.
"""

import logging
from urllib.parse import urlparse


def is_url(url):
    # Found on StackOverflow, fails some edge cases but generally useful
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class LogMixin(object):
    # Found this online and it's cool. Not used for anything yet
    @property
    def logger(self):
        name = ".".join([self.__module__, self.__class__.__name__])
        FORMAT = "%(name)s:%(levelname)s:%(message)s"
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
        logger = logging.getLogger(name)
        return logger
