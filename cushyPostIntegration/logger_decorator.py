import logging
import time
from functools import wraps


def logger(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.debug('About to run %s' % fn.__name__)
        out = fn(*args, **kwargs)
        logging.debug('Done running %s' % fn.__name__)
        logging.debug("--- %s seconds ---" % (time.time() - start_time))
        # Return the return value
        return out
    return wrapper
