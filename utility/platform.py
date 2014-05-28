"""
RunMan Platform: Determine OS platform (ex: linux_redhat, linux_debian, solaris)

This is used to determine which execution block is used for a given job.  All platforms have files in 
different places and some other formatting issues, so their execution and success tests must be customized.

This can be as detailed as necessary to separate running environments.
"""


import sys
import commands


class PlatformNotFound(Exception):
  """No platform was able to be determined"""


def GetPlatform():
  """Returns a string, which is used to specify what to run for a given job"""
  # Gather platform details
  details = {}
  details['python_platform'] = sys.platform
  details['python_version'] = sys.version
  
  # Linux - Red Hat
  if details['python_platform'] in ['linux2',] and 'Red Hat' in details['python_version']:
    platform = 'linux_redhat'
  
  # Solaris
  elif details['python_platform'] in ['sunos5',]:
    platform = 'solaris'

  # Failure to find a platform
  else:  
    raise PlatformNotFound('System Details: %s' % details)
  
  return platform


def GetHostname():
  """Returns a string, the fully qualified domain name (FQDN) of this local host."""
  (status, output) = commands.getstatusoutput('/bin/hostname')
  return output.split('.')[0]

