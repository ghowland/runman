"""
Logging
"""

import time
import sys


# Run options, may specify logging level or log output targets, etc
RUN_OPTIONS = {}

# Store all of our logged lines in memory
LOGGED = []


def log(text, options=RUN_OPTIONS):
  """Send log messages to STDERR, so we can template to STDOUT by default (no output path, easier testing)"""
  global LOGGED
  
  current_time = time.time()
  local_time = time.localtime(current_time)
  timestamp = '[%d-%02d-%02d %02d:%02d:%02d] ' % local_time[:6]
  
  # Save the log text to our global storage variable
  LOGGED.append((current_time, text))
  
  sys.stderr.write(timestamp + str(text) + '\n')
  sys.stderr.flush()

