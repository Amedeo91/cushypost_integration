import logging
import time
from functools import wraps


def logger(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.debug('About to run %s' % fn.__name__)
        try:
            return fn(*args, **kwargs)
        except Exception as error:
            raise error
        finally:
            logging.debug('Done running %s' % fn.__name__)
            logging.debug("--- %s seconds ---" % (time.time() - start_time))
    return wrapper
