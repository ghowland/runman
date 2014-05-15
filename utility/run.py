"""
Run a Job
"""


import yaml
import json
import decimal
import re
import sys

from log import log
from error import Error


class InputNotCollectable(Exception):
  """Cannot collect all required input from available collection methods and inputs"""
  

def Run(run_spec, command_options, command_args):
  """Run a job"""
  # Get the job spec name
  if len(command_args) < 1:
    Error('Missing job spec name to run', command_options)

  job_spec_key = command_args[0]
  
  # Get the job spec path, from the run spec job key
  if job_spec_key in run_spec['jobs']:
    job_spec_path = run_spec['jobs'][job_spec_key]
    
  else:
    Error('Missing job spec key in run spec: %s' % job_spec_key, command_options)

  
  # Load the job spec
  try:
    job_spec = yaml.load(open(job_spec_path))
  
  except Exception, e:
    Error('Failed to load job spec: %s: %s' % (job_spec_path, e), command_options)
  
  
  # Initiate run procedures
  input_data = RetrieveInputData(run_spec, job_spec, job_spec_path, command_options, command_args)
  
  log('Input Data: %s' % input_data)
  
  # Run it...
  log('Running job: %s' % job_spec['data']['name'])
  
  pass
  #ReportResult()...



def RetrieveInputData(runspec, job_spec, job_spec_path, command_options, command_args):
  """Returns the input_data, with all required data, or throws a InputNotCollectable exception if it cannot be collected"""
  log('Retrieving Input Data')
  
  # Start with no input fields
  input_data = {}
  
  
  # If data was passed in directly with our command options (Websource/API invocation method, not available from CLI), update dict
  if 'input_data' in command_options:
    input_data.update(command_options['input_data'])
  
  
  # Load any input from file, if specified
  if command_options['input_path']:
    # JSON
    if command_options['input_path'].endswith('.json'):
      # Attempt to load the specified input path
      try:
        input_data_loaded = json.load(open(command_options['input_path']))
        input_data.update(input_data_loaded)
      
      except Exception, e:
        Error('Failed to load input path: %s: %s' % (command_options['input_path'], e), command_options)

    # YAML
    elif command_options['input_path'].endswith('.yaml'):
      # Attempt to load the specified input path
      try:
        input_data_loaded = yaml.load(open(command_options['input_path']))
        input_data.update(input_data_loaded)
      
      except Exception, e:
        Error('Failed to load input path: %s: %s' % (command_options['input_path'], e), command_options)
    
    # Unknown input file type, fail
    else:
      Error('Unknown input file data type (suffic unknown, acceptable: .yaml, .json): %s' % command_options['input_path'], command_options)

  
  validated_input = {}
  missing_input = []
  
  
  # Validate Input from input path and determine input we still do not have, which needs to be collected
  #NOTE(g): Note this is done before collection (which needs to be validated as well) to reduce wasted time/effort if it's going
  #   to fail on this input, better to do it before making the user input the collected data interactively.
  for (key, value) in job_spec['input'].items():
    # If we have this key in input data, validate
    if key in input_data:
      # Get the validated and processed input.
      #NOTE(g): Any errors abort the run, so no error checking is necessary.
      validated_input[key] = ValidateInput(job_spec, job_spec_path, key, input_data[key], command_options)
    
    # Else, add to our missing input to collect interactively
    else:
      missing_input.append(key)
  
  # If we have validated input, log about it
  if validated_input:
    log('Validated input file data: %s item(s).  Collecting %s item(s) interactively.' % (len(validated_input), len(missing_input)))
  else:
    log('No fields validated by input file.  Collecting %s item(s) interactively.' % len(missing_input))
  
  
  # If we have missing input, but specified non-interactive in our options, fail
  if missing_input and command_options['noninteractive']:
    Error('Non-interactive run mode was missing input fields from input data: %s' % ', '.join(missing_input), command_options)
  
  # Else, if we have missing input, collect it via our collection specification
  elif missing_input:
    # Collect all our missing input (whether in Collect block or not, Collect block just gives more detail for prompting for data)
    collected_input = CollectInput(job_spec, job_spec_path, missing_input, command_options)
    
    # Validate collected input
    for (collected_key, collected_value) in collected_input.items():
      # Get the validated and processed input.
      #NOTE(g): Any errors abort the run, so no error checking is necessary.
      validated_input[collected_key] = ValidateInput(job_spec, job_spec_path, collected_key, collected_value, command_options)
      
      # Remove the collected key from missing input, not missing any more
      missing_input.remove(collected_key)
  
  
  # Check for code logic failure, still missing input keys after all of them should have been collected one way or another
  if missing_input:
    raise Exception('Code Logic Error: Failed to collect all the data between input data files and interactive collection: Missing input keys: %s' % missing_input)


  # Return our validated input fields
  return validated_input


def ValidateInput(job_spec, job_spec_path, key, value, command_options):
  """If successful, returns the processed value that passes validation.  If unsuccessful the run terminates with Error()."""
  # Get validation information
  input_validation = job_spec['input'][key]
  
  # There must be a type to validate on, any error aborts
  if 'type' not in input_validation:
    Error('Invalid input validation spec in job_spec: %s: Input "%s": No type was specified for validation' % (job_spec_path, key), command_options)
  
  # Text validation
  if input_validation['type'] == 'text':
    validated_value = str(value)
    
    # Minimum length: optional validation
    if 'min length' in input_validation and len(validated_value) < input_validation['min']:
      Error('Input Validation: Value is less than minimum (job_spec_path="%s", input_key="%s"): %s (min size = %s)' % (job_spec_path, key, len(validated_value), input_validation['min']), command_options)
    
    # Minimum length: optional validation
    if 'max length' in input_validation and len(validated_value) < input_validation['max']:
      Error('Input Validation: Value is more than maximum (job_spec_path="%s", input_key="%s"): %s (max size = %s)' % (job_spec_path, key, len(validated_value), input_validation['max']), command_options)
    
    # Regex Match Validation: optional validation
    if 'regex validate' in input_validation and not re.findall(input_validation['regex validate'], validated_value):
      Error('Input Validation: Regex match not found (job_spec_path="%s", input_key="%s"): %s (regex = "%s")' % (job_spec_path, key, validated_value, input_validation['regex validate']), command_options)
    

  # Integer
  elif input_validation['type'] in ['integer', 'int']:
    # Coerce to integer, or fail
    try:
      validated_value = int(value)
    except Exception, e:
      Error('Input Validation: Value is not an Integer (job_spec_path="%s", input_key="%s"): %s' % (job_spec_path, key, value), command_options)
    
    # Minimum value: optional validation
    if 'min' in input_validation and validated_value < input_validation['min']:
      Error('Input Validation: Value is less than minimum (job_spec_path="%s", input_key="%s"): %s < %s (min)' % (job_spec_path, key, validated_value, input_validation['min']), command_options)
    
    # Minimum value: optional validation
    if 'max' in input_validation and validated_value < input_validation['max']:
      Error('Input Validation: Value is more than maximum (job_spec_path="%s", input_key="%s"): %s > %s (max)' % (job_spec_path, key, validated_value, input_validation['max']), command_options)
      

  # Decimal
  elif input_validation['type'] == 'decimal':
    validated_value = decimal.Decimal(value)
    
    # Minimum value: optional validation
    if 'min' in input_validation and validated_value < input_validation['min']:
      Error('Input Validation: Value is less than minimum (job_spec_path="%s", input_key="%s"): %s < %s (min)' % (job_spec_path, key, value, input_validation['min']), command_options)
    
    # Minimum value: optional validation
    if 'max' in input_validation and validated_value < input_validation['max']:
      Error('Input Validation: Value is more than maximum (job_spec_path="%s", input_key="%s"): %s > %s (max)' % (job_spec_path, key, value, input_validation['max']), command_options)
  
  # Unknown - fail
  else:
    Error('Unknown input validation type (job_spec_path="%s", input_key="%s"): %s' % (job_spec_path, key, input_validation['type']), command_options)
  

  return validated_value
  

def CollectInput(job_spec, job_spec_path, missing_input, command_options):
  """Returns a dict of input fields (key/value) after prompting the user for them interactively.
  
  First it prompts for fields that are not in the Collect block (ones that should be sent non-interactively if invoked
  in a distributed manner (not CLI based)).  Second it prompts for fields that are specified in a Collect block, and have
  actual prompting information.  In a distributed invocation, Collect block fields would be collected in a web form or something,
  CLI invocation will get this readline method.
  """
  log('Collecting Input')
  
  collected_data = {}
  

  # Find what fields are in the Collect block
  collect_block_keys = []
  for item in job_spec['collect']:
    for (item_set_key, item_set_value) in item['set'].items():
      collect_block_keys.append(item_set_key)
  

  # First pass - Collect input fields that are not in the Collect block (no prompt information)
  missing_input_keys = list(missing_input)
  missing_input_keys.sort()
  for key in missing_input_keys:
    # Skip collect block keys, we will do them after we do the keys not in the Collect block
    #TODO(g): Maybe this is an uncessary idea, but I like the idea of separating them for a few reasons, so doing it this way
    if key in collect_block_keys:
      continue
    
    # Prompt
    print '\nEnter input data field: %s: ' % key,
    sys.stdout.flush()
    
    # Read input
    collected_data[key] = sys.stdin.readline()
  
  
  # Second pass - Collect input fields that are in the Collect block
  for collect_item in job_spec['collect']:
    print '\nCollect data for: %(label)s: %(info)s' % collect_item
    
    for item_set_field in collect_item['set']:
      # If this item is already specified in input data (not in missing_input list), skip it
      if item_set_field not in missing_input:
        print '\nField value specified in input data: %s' % item_set_field
        continue
      
      # Prompt
      print '\nEnter field: %s: ' % item_set_field,
      sys.stdout.flush()
      
      # Read input
      collected_data[item_set_field] = sys.stdin.readline()[:-1]  # Strip ending new-line character
  
  
  return collected_data


