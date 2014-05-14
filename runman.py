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
  'info':'Information about this environment'
}


def ProcessCommand(runspec, command, command_options, command_args):
  """Process a command against this runspec_path"""
  output_data = {}
  
  # Info: Information about this environment
  if command == 'info':
    output_data['options'] = command_options

  # Print: Print out job spec
  elif command == 'print':
    output_data['errors'] = []
    
    # Runspec
    output_data['runspec'] = runspec
    
    # Websource: If we have the websource (HTTP based datasource), load its data
    if 'websource' in runspec:
      try:
        output_data['websource'] = yaml.load(open(runspec['websource']))
        
      except Exception, e:
        output_data['errors'].append('Could not load runspec\'s websource: %s: %s' % (runspec['websource'], e))
    
    # Websource: missing
    else:
      output_data['errors'].append('No websource block specified in the runspec')
    
    # Jobs
    output_data['jobs'] = {}
    for (job, job_path) in runspec['jobs'].items():
      if os.path.isfile:
        try:
          output_data['jobs'][job] = yaml.load(open(job_path))
          
        except Exception, e:
          output_data['errors'].append('Job spec could not be loaded: %s: %s: %s' % (job, job_path, e))
          
      else:
        output_data['errors'].append('Job spec file not found: %s' % job_path)
  
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
  print '  -f, --format            Format output, types: %s' % ', '.join(OUTPUT_FORMATS)
  print
  print '  -v, --verbose           Verbose output'
  print
  print 'Commands:'
  print
  for (command, info) in COMMANDS.items():
    print '  %-23s %s' % (command, info)
  print
  
  sys.exit(exit_code)


def Main(args=None):
  if not args:
    args = []

  long_options = ['help', 'format=', 'verbose', ]
  
  try:
    (options, args) = getopt.getopt(args, '?hvf:', long_options)
  except getopt.GetoptError, e:
    Usage(e)
  
  # Dictionary of command options, with defaults
  command_options = {}
  command_options['platform'] = utility.platform.GetPlatform()
  command_options['verbose'] = False
  command_options['format'] = 'pprint'
  
  
  # Process out CLI options
  for (option, value) in options:
    # Help
    if option in ('-h', '-?', '--help'):
      Usage()
    
    # Verbose output information
    elif option in ('-v', '--verbose'):
      command_options['verbose'] = True
    
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
  runspec_path = args[0]
  
  if not os.path.isfile(runspec_path):
    Usage('Run spec file does not exist: %s' % runspec_path)
  
  try:
    runspec = yaml.load(open(runspec_path))
  
  except Exception, e:
    Usage('Failed to load runspec: %s: %s' % (runspec_path, e))
    
  
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
    result = ProcessCommand(runspec, command, command_options, command_args)
    
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
