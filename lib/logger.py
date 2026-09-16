import logging
import os
import sys

__all__ = ['logger']

LOGGER_NAME = 'c4dos'


def _setup_logger():
  logger = logging.getLogger(LOGGER_NAME)

  if getattr(logger, '_is_configured', False):
    return logger

  env_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
  log_level = getattr(logging, env_level, logging.INFO)
  logger.setLevel(log_level)

  is_systemd = 'JOURNAL_STREAM' in os.environ or 'INVOCATION_ID' in os.environ

  if is_systemd:
    fmt = '[%(process)d] [%(levelname)s] %(message)s'
  else:
    fmt = '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s'

  datefmt = '%Y-%m-%d %H:%M:%S %z'
  formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

  is_gunicorn = 'gunicorn' in sys.modules or os.environ.get(
      'SERVER_SOFTWARE', ''
  ).startswith('gunicorn')

  if is_gunicorn:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)
    logger.propagate = False

    for handler in logger.handlers:
      handler.setFormatter(formatter)
  else:
    if not logger.handlers:
      stderr_handler = logging.StreamHandler(sys.stderr)
      stderr_handler.setFormatter(formatter)
      logger.addHandler(stderr_handler)
      logger.propagate = False

  logger._is_configured = True
  return logger


logger = _setup_logger()

