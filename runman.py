#!/usr/bin/python
"""
RunMan - Management of things that need to be run

TODO:
  - ...
  -
"""


import sys
import os
import getopt
import yaml
import json
import pprint


import utility
from utility.log import log


# Output formats we support
OUTPUT_FORMATS = ['json', 'yaml', 'pprint']

# Commands we support
COMMANDS = {
  'print':'Print out job spec',
  'list':'List all jobs in runman spec',
  'run':'Run a job from the runman spec',
  'info':'Information about this environment',
  'client':'Run forever processing server requests',
}


def ProcessCommand(run_spec, command, command_options, command_args):
  """Process a command against this run_spec_path"""
  output_data = {}
  
  # Info: Information about this environment
  if command == 'info':
    output_data['options'] = command_options

  # List: List the jobs to run in this environment
  elif command == 'list':
    output_data['errors'] = []
    
    # Jobs
    #output_data['jobs'] = {}
    for (job, job_path) in run_spec['jobs'].items():
      if os.path.isfile:
        try:
          job_data = yaml.load(open(job_path))
          #output_data['jobs'][job] = {}
          #output_data['jobs'][job]['data'] = job_data['data']
          
          print 'Job: %s: %s: %s' % (job, job_data['data']['component'], job_data['data']['name'])
          
        except Exception, e:
          output_data['errors'].append('Job spec could not be loaded: %s: %s: %s' % (job, job_path, e))
          
      else:
        output_data['errors'].append('Job spec file not found: %s' % job_path)

  # Print: Print out job spec
  elif command == 'print':
    output_data['errors'] = []
    
    # Runspec
    output_data['run_spec'] = run_spec
    
    # Websource: If we have the websource (HTTP based datasource), load its data
    if 'websource' in run_spec:
      try:
        output_data['websource'] = yaml.load(open(run_spec['websource']))
        
      except Exception, e:
        output_data['errors'].append('Could not load run_spec\'s websource: %s: %s' % (run_spec['websource'], e))
    
    # Websource: missing
    else:
      output_data['errors'].append('No websource block specified in the run_spec')
    
    # Jobs
    output_data['jobs'] = {}
    for (job, job_path) in run_spec['jobs'].items():
      log('Job: %s' % job)
      if os.path.isfile:
        try:
          output_data['jobs'][job] = yaml.load(open(job_path))
          
        except Exception, e:
          output_data['errors'].append('Job spec could not be loaded: %s: %s: %s' % (job, job_path, e))
          
      else:
        output_data['errors'].append('Job spec file not found: %s' % job_path)
  
  # Run a job
  elif command == 'run':
    utility.run.Run(run_spec, command_options, command_args)
  
  # Client - Run forever processing server requests
  elif command == 'client':
    utility.client.ProcessRequestsForever(run_spec, command_options, command_args)
  
  # Unknown command
  else:
    output_data['errors'] = ['Unknown command: %s' % command]
    
  
  return output_data


def FormatAndOuput(result, command_options):
  """Format the output and return it"""
  # PPrint
  if command_options['format'] == 'pprint':
    pprint.pprint(result)
  
  # YAML
  elif command_options['format'] == 'yaml':
    print yaml.dump(result)
  
  # JSON
  elif command_options['format'] == 'json':
    print json.dumps(result)
  
  else:
    raise Exception('Unknown output format "%s", result as text: %s' % (command_options['format'], result))


def Usage(error=None):
  """Print usage information, any errors, and exit.

  If errors, exit code = 1, otherwise 0.
  """
  if error:
    print '\nerror: %s' % error
    exit_code = 1
  else:
    exit_code = 0
  
  print
  print 'usage: %s [options] <runman_spec.yaml> <command> [job_key]' % os.path.basename(sys.argv[0])
  print
  print 'example usage: "python %s ./runman_specs/*.yaml run somejob"' % os.path.basename(sys.argv[0])
  print
  print
  print 'Options:'
  print
  print '  -h, -?, --help          This usage information'
  print '  -v, --verbose           Verbose output'
  print '  -s, --strict            Strict mode: fail if input fields not specified for collection are missing'
  print '  -f, --format <format>   Format output, types: %s' % ', '.join(OUTPUT_FORMATS)
  print '  -n, --noninteractive    Do not use STDIN to prompt for missing input fields'
  print '  -i, --input <path>      Path to input file (Format specified by suffic: (.yaml, .json)'
  print
  print 'Commands:'
  print
  command_keys = list(COMMANDS.keys())
  command_keys.sort()
  for command in command_keys:
    print '  %-23s %s' % (command, COMMANDS[command])
  print
  
  sys.exit(exit_code)


def Main(args=None):
  if not args:
    args = []

  long_options = ['help', 'format=', 'verbose', 'strict', 'noninteractive', 'input=']
  
  try:
    (options, args) = getopt.getopt(args, '?hvnsi:f:', long_options)
  except getopt.GetoptError, e:
    Usage(e)
  
  # Dictionary of command options, with defaults
  command_options = {}
  command_options['remote'] = False   # Remote invocation.  When quitting or Error(), report back remotely with details.
  command_options['platform'] = utility.platform.GetPlatform()
  command_options['verbose'] = False
  command_options['format'] = 'pprint'
  command_options['noninteractive'] = False
  command_options['input_path'] = None
  command_options['strict'] = False
  
  
  # Process out CLI options
  for (option, value) in options:
    # Help
    if option in ('-h', '-?', '--help'):
      Usage()
    
    # Verbose output information
    elif option in ('-v', '--verbose'):
      command_options['verbose'] = True
    
    # Noninteractive.  Doesnt use STDIN to gather any missing data.
    elif option in ('-n', '--noninteractive'):
      command_options['noninteractive'] = True
    
    # Strict mode. fail if input fields not specified for collection are missing.
    elif option in ('-s', '--strict'):
      command_options['strict'] = True
    
    # Noninteractive.  Doesnt use STDIN to gather any missing data.
    elif option in ('-i', '--input'):
      command_options['input_path'] = value
    
    # Format output
    elif option in ('-f', '--format'):
      if value not in (OUTPUT_FORMATS):
        Usage('Unsupported output format "%s", supported formats: %s' % (value, ', '.join(OUTPUT_FORMATS)))
      
      command_options['format'] = value
    
    # Invalid option
    else:
      Usage('Unknown option: %s' % option)
  
  
  # Store the command options for our logging
  utility.log.RUN_OPTIONS = command_options
  
  
  # Ensure we at least have a command, it's required
  if len(args) < 1:
    Usage('No run spec specified')
  
  # Get the command
  run_spec_path = args[0]
  
  if not os.path.isfile(run_spec_path):
    Usage('Run spec file does not exist: %s' % run_spec_path)
  
  try:
    run_spec = yaml.load(open(run_spec_path))
  
  except Exception, e:
    Usage('Failed to load run_spec: %s: %s' % (run_spec_path, e))
    
  
  # Ensure we at least have a command, it's required
  if len(args) < 2:
    Usage('No command specified')
  
  # Get the command
  command = args[1]
  
  # If this is an unknown command, say so
  if command not in COMMANDS:
    Usage('Command "%s" unknown.  Commands: %s' % (command, ', '.join(COMMANDS)))
  
  # If there are any command args, get them
  command_args = args[2:]
  
  # Process the command
  if 1:
  #try:
    # Process the command and retrieve a result
    result = ProcessCommand(run_spec, command, command_options, command_args)
    
    # Format and output the result (pprint/json/yaml to stdout/file)
    FormatAndOuput(result, command_options)
  
  #NOTE(g): Catch all exceptions, and return in properly formatted output
  #TODO(g): Implement stack trace in Exception handling so we dont lose where this
  #   exception came from, and can then wrap all runs and still get useful
  #   debugging information
  #except Exception, e:
  else:
    utility.error.Error({'exception':str(e)}, command_options)


if __name__ == '__main__':
  #NOTE(g): Fixing the path here.  If you're calling this as a module, you have to 
  #   fix the utility/handlers module import problem yourself.
  sys.path.append(os.path.dirname(sys.argv[0]))

  Main(sys.argv[1:])
