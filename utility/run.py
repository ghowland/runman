"""
Run a Job
"""


import yaml

from log import log
from error import Error


def Run(runspec, command_options, command_args):
  """Run a job"""
  # Get the job spec name
  if len(command_args) < 1:
    Error('Missing job spec name to run', command_options)

  job_spec_key = command_args[0]
  
  # Get the job spec path, from the run spec job key
  if job_spec_key in runspec['jobs']:
    job_spec_path = runspec['jobs'][job_spec_key]
    
  else:
    Error('Missing job spec key in run spec: %s' % job_spec_key, command_options)

  
  # Load the job spec
  try:
    job_spec = yaml.load(open(job_spec_path))
  
  except Exception, e:
    Error('Failed to load job spec: %s: %s' % (job_spec_path, e), command_options)
  
  
  # Initiate run procedures
  log('Running job: %s' % job_spec['data']['name'])


