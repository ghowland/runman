"""
RunMan Client: Run forever processing server requests
"""


import yaml
import urllib2
import urllib
import base64
import json
import hashlib
import time
import signal
import sys

from log import log
from error import Error

import run
import platform


# Loop for second before checking again
LOOP_DELAY = 10.0

# Default to running, SIGKILL changes that
RUNNING = True

# Maximum errors in a row before we quit, so we dont freak out
MAX_CONSECUTIVE_ERRORS = 5

# Seconds to wait after a consecutive processing error (more than 1 error in a row)
CONSECUTIVE_ERROR_WAIT = 5.0


def SignalHandler_Quit(signum, frame):
  """Quit during a safe time after receiving a quit signal."""
  log('Received signal to quit: %s' % signum)
  
  global RUNNING
  RUNNING = False


def ProcessRequestsForever(run_spec, command_options, command_args):
  global RUNNING
  
  log('Running forever in Client Mode... (%s) [%s]' % (platform.GetHostname(), platform.GetPlatform()))

  # Get the Web Source we load and report our jobs to and from  
  websource = yaml.load(open(run_spec['websource']))
  
  # Create data to pass to the web request
  job_get_data = {'hostname':platform.GetHostname()}
  
  consecutive_errors = 0
  
  # Run forever, until we quit
  while RUNNING:
    try:
      # Get the jobs the server has for us
      result = WebGet(websource['job_get'], job_get_data)
      server_result = json.loads(result)
      jobs = json.loads(server_result['jobs'])
      
      # Loop over the jobs the server gave us
      for job_request in jobs:
        log('Processing job request: %s: %s' % (job_request['id'], job_request['job_key']))
        # Load Selected job
        fp = open(run_spec['jobs'][job_request['job_key']])
        job = yaml.load(fp)
        fp.close()
        
        # Create an MD5 digest of it
        #print job_spec
        #NOTE(g): Using the above JSON dump allows us to test the data, ignoring comments (stripped in YAML load), and any reording
        #   of keys (sort_keys).  This produces a more stable md5 digest than a strict text file eval, and also allows working with
        #   already loaded data.
        job_json = json.dumps(job, sort_keys=True)
        job_json_md5 = hashlib.md5(job_json).hexdigest()
        
        
        
        
        #TODO ---->  Switch this to receiving the job data from the server, and not having local data, because we are taking it
        #   in snippets.  No double verification, but no having to sync all the time either....
        pass
      
      
      
      
        
        # Compare local client and remote server md5 digests of this Job
        #NOTE(g): Using the above JSON dump allows us to test the data, ignoring comments (stripped in YAML load), and any reording
        #   of keys (sort_keys).  This produces a more stable md5 digest than a strict text file eval, and also allows working with
        #   already loaded data.
        if job_json_md5 == job_request['job_data_server_md5_digest']:
          log('Matched MD5 digests: (client) %s == %s (server)' % (job_json_md5, job_request['job_data_server_md5_digest']))
          
        # Else, failed to match MD5 digest of data
        else:
          log('ERROR: Failed to match MD5 digests, skipping: (client) %s != %s (server)' % (job_json_md5, job_request['job_data_server_md5_digest']))
          
          # Report the changes
          report_result = WebGet(websource['job_report'], {'id':job_request['id'], 'data':json.dumps({'job_data_remote_md5_digest':job_json_md5})})
          log('Report Result: %s' % report_result)
          
          # Skip this one until it's MD5 issues are corrected
          continue
        
        import pprint
        input_data = json.loads(job_request['input_data_json'])
        pprint.pprint(input_data)
        
        print job_request['job_key']
        
        
        
        
        
        
        
        # Run the job
        #TODO(g): Run a job item, not the full Job...  Get the input data for the job from WebGet...
        #
        #   Should report on ongoing processing, and then finally when finished...
        #
        run_result = run.Run(run_spec, command_options, [job_request['job_key']], input_data=input_data)
        
        
        
        
        
        
        pprint.pprint(run_result)
        
        # Add in the local MD5 digest
        run_result['job_data_remote_md5_digest'] = job_json_md5
        run_result['result_data_json'] = json.dumps(run_result, sort_keys=True)
        
        run_result_json = json.dumps(run_result)
        
        # Report the results
        report_result = WebGet(websource['job_report'], {'id':job_request['id'], 'data':run_result_json})
        log('Report Result: %s' % report_result)
        
      
      # Sleep - Give back to the system, if we are going to keep running (otherwise, quit faster)
      #log('Sleeping... (%s seconds)' % LOOP_DELAY)
      if RUNNING:
        time.sleep(LOOP_DELAY)
        
        # Clear any consecutive errors, we made it to the end of processing
        consecutive_errors = 0
    
    except Exception, e:
      log('Main loop exception:\n\n%s' % e)
      consecutive_errors += 1
      
      # Reaches max?  Quit
      if consecutive_errors > MAX_CONSECUTIVE_ERRORS:
        log('Consecutive errors about max (%s), quitting...' % MAX_CONSECUTIVE_ERRORS)
        sys.exit(1)
      
      # Else, if we have had 2 errors in a row, sleep for a back-off time
      elif consecutive_errors >= 2:
        log('Sleeping for consecutive error backoff: %s seconds' % CONSECUTIVE_ERROR_WAIT)
        time.wait(CONSECUTIVE_ERROR_WAIT)
    

def WebGet(websource, args=None):
  """Wrap dealing with web requests.  The job server uses this to avoid giving out database credentials to all machines."""
  #log('WebGet: %s' % websource)
  try:
    http_request = urllib2.Request(websource['url'])
  
    # If Authorization
    if websource.get('username', None):
      auth = base64.standard_b64encode('%s:%s' % (websource['username'], websource['password'])).replace('\n', '')
      http_request.add_header("Authorization", "Basic %s" % auth)
    
    
    # If args (POST)
    if args:
      http_request.add_data(urllib.urlencode(args))
  
  
    result = urllib2.urlopen(http_request)
    data = result.read()
    
    return data

  except Exception, e:
    log('WebGet error: %s' % (e))
    
    # No jobs, just keep going, we logged the error (in JSON format)
    return """{"jobs":[]}"""


