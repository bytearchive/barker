# Clive is Copyright 2011 SimpleGeo, Inc.
# Written by Paul Lathrop <paul@simplegeo.com>

import logging
import os
from itertools import imap, ifilter
from functools import partial
from optparse import OptionParser
try:
    import simplejson as json
except ImportError:
    import json

import eventlet
from eventlet.green import subprocess

import clive.config as config

LOGGER = logging.getLogger('clive.pod')

def get_pod_output(filename):
    """Executes a 'pod' file (an executable file which should output
    JSON to stdout) and returns the output."""
    LOGGER.debug("Executing pod file %s", filename)
    return subprocess.Popen([filename], stdout=subprocess.PIPE).communicate()[0]

def load_pod(filename, timeout=30):
    """Attempts to execute a pod file, possibly with a timeout, and
    parse the output as JSON. If the execution times out or an error
    is encountered during execution, or if the output is not valid
    JSON, this will return an empty tuple. Otherwise, it will return
    a tuple: (filename, parsed_output)"""
    pod = ()
    with eventlet.Timeout(timeout, False):
        try:
            LOGGER.debug("Executing and parsing pod %s with timeout %s",
                         filename, timeout)
            pod = (os.path.basename(filename), json.loads(get_pod_output(filename)))
        except OSError, exc:
            LOGGER.warning("OSError while executing pod plugin %s,"
                           "ignoring pod!", filename)
            LOGGER.debug(exc)
        except (ValueError, TypeError), exc:
            LOGGER.warning("Error while parsing output from pod plugin %s, "
                           "ignoring pod!", filename)
            LOGGER.debug(exc)
    if not pod:
        LOGGER.warning("Timed out while executing pod plugin %s,"
                       "ignoring pod!", filename)
    return pod

def executable_file_p(filename):
    """Predicate to check if a given file is executable."""
    result =  os.access(filename, os.X_OK) and not os.path.isdir(filename)
    if result:
        LOGGER.debug("%s is an executable file", filename)
    else:
        LOGGER.debug("%s is not an executable file", filename)
    return result

def get_pod_files(dirname):
    """Returns the fully-qualified paths for the list of executable
    files in the specified directory. Does not recurse into
    subdirectories."""
    LOGGER.debug("Locating executable files in pod directory %s", dirname)
    return ifilter(executable_file_p, imap(partial(os.path.join, dirname),
                                           os.listdir(dirname)))

def load_pod_dir(dirname=config.POD_DIR, timeout=config.POD_TIMEOUT):
    """Concurrently loads the pod files in the given directory and
    returns a dict containing their output."""
    if dirname[-1] != os.sep:
        dirname += os.sep
        LOGGER.info("Appended file separator to specified pod dir %s",
                    dirname)
    pool = eventlet.GreenPool()
    LOGGER.debug("Loading pod files from directory %s with timeout %s",
                 dirname, timeout)
    return dict(ifilter(None, pool.imap(partial(load_pod, timeout=timeout), get_pod_files(dirname))))

def load_pod_subset(pods, dirname=config.POD_DIR, timeout=config.POD_TIMEOUT):
    """Concurrently loads only the specified pod files in the given
    directory and returns a dict containing their output."""
    if dirname[-1] != os.sep:
        dirname += os.sep
        LOGGER.info("Appended file separator to specified pod dir %s",
                    dirname)
    pool = eventlet.GreenPool()
    LOGGER.debug("Loading specified pod files from directory %s with"
                 "timeout %s", dirname, timeout)
    return dict(ifilter(None, pool.imap(partial(load_pod, timeout=timeout),
                                        ifilter(lambda p: os.path.basename(p) in pods,
                                                get_pod_files(dirname)))))


def clive_pod_cmd():
    parser = OptionParser()
    # TODO: Add option to control timeouts
    (options, args) = parser.parse_args()
    if len(args) > 0:
        print json.dumps(load_pod_subset(args), sort_keys=True, indent=4)
    else:
        print json.dumps(load_pod_dir(), sort_keys=True, indent=4)