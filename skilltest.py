#!/usr/bin/python

# =============================================================================
#
# Copyright 2017 by Leland Lucius
#
# Released under the GNU Affero GPL
# See: https://github.com/lllucius/climacast/blob/master/LICENSE
#
# =============================================================================

from __future__ import print_function

import argparse
import importlib.util
import io
import itertools
import json
import multiprocessing
import os
import random
import re
import shlex
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime
from subprocess import Popen, PIPE, check_output

try:
    from urllib.parse import unquote_plus, quote_plus, urlparse, parse_qs, urljoin
except ImportError:
    from urllib import unquote_plus, quote_plus
    from urlparse import urlparse, parse_qs, urljoin

OPTS = None

VAR_RE = re.compile(r"(?P<var>{.*?})")
SUB_RE = re.compile(r"{(?P<var>.*?)\}[/\\]*")

PLAT = sys.platform

# Intent name pattern to extract from utterances
INTENT_RE = re.compile(r"^(\w+)\s+(.*)$")

CFG = \
{
    "inputdir": "./results/input",
    "outputdir": "./results/output",
    "skilldir": "./skill",
    "testsdir": "./tests",
    "bypass": False,
    "regen": False,
    "keep": False,
    "tasks": 1,
    "invocation":  "your skill's invocation name",
    "lambda_dir": "./lambda",
    "lambda_module": "lambda_function",
    "lambda_handler": "lambda_handler"
}

# Intent name pattern to extract from utterances
INTENT_RE = re.compile(r"^(\w+)\s+(.*)$")

def run_skill(filepfx, intent_name, slots, utterance):
    """Invoke the local lambda function directly with an Alexa request"""
    try:
        # Create the Alexa request JSON
        request = create_alexa_request(intent_name, slots, utterance)
        
        # Load and invoke the lambda function
        response = invoke_lambda(request)
        
        # Save the response
        with open(os.path.join(OPTS.outputdir, filepfx + ".json"), "wt") as outfile:
            json.dump({"request": request, "response": response}, outfile, indent=2)
            
        return response
    except Exception as e:
        print("Caught exception invoking skill:")
        print(utterance)
        print()
        traceback.print_exc()
        print()
        raise e

def create_alexa_request(intent_name, slots, utterance):
    """Create an Alexa skill request JSON from intent name and slots"""
    # Build slots dict
    slot_dict = {}
    for slot_name, slot_value in slots.items():
        slot_dict[slot_name] = {
            "name": slot_name,
            "value": slot_value
        }
    
    # Create the Alexa request structure
    request = {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": "SessionId.test-session-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "application": {
                "applicationId": "amzn1.ask.skill.test-skill-id"
            },
            "user": {
                "userId": "amzn1.ask.account.TEST_USER_ID"
            }
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "EdwRequestId.test-request-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().isoformat() + "Z",
            "locale": "en-US",
            "intent": {
                "name": intent_name,
                "slots": slot_dict
            }
        }
    }
    
    return request

def invoke_lambda(event):
    """Load and invoke the local lambda function"""
    # Build the path to the lambda module
    lambda_path = os.path.abspath(OPTS.lambda_dir)
    module_file = os.path.join(lambda_path, OPTS.lambda_module + ".py")
    
    if not os.path.exists(module_file):
        raise FileNotFoundError(f"Lambda function not found at {module_file}")
    
    # Add lambda directory to sys.path if not already there
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(OPTS.lambda_module, module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the handler function
    if not hasattr(module, OPTS.lambda_handler):
        raise AttributeError(f"Handler '{OPTS.lambda_handler}' not found in {OPTS.lambda_module}")
    
    handler = getattr(module, OPTS.lambda_handler)
    
    # Invoke the handler
    response = handler(event, None)
    
    return response

def extract_intent_and_slots(utterance, resolved, types_dict):
    """Extract intent name and slots from an utterance"""
    # Try to parse intent name from utterance file format
    # Format: "IntentName utterance text with {slots}"
    match = INTENT_RE.match(utterance.strip())
    if match:
        intent_name = match.group(1)
        # Use the intent name from the utterance
    else:
        # Default intent name if not specified
        intent_name = "TestIntent"
    
    # Extract slots from the types dictionary
    slots = {}
    for typename, value in types_dict.items():
        # Remove braces from typename
        slot_name = typename.strip("{}")
        slots[slot_name] = value
    
    return intent_name, slots

class Options(object):
    def __init__(self):
        setattr(self, "file", None)
        self.merge_dict(CFG)

    def load_config(self, path):
        path = os.path.join(os.path.expanduser(path), ".skilltest")
        if os.path.exists(path):
            with open(path, "rt") as c:
                self.merge_dict(json.load(c))

    def merge_dict(self, opts):
        for opt in opts:
            setattr(self, opt, opts[opt])

    def merge_args(self, opts):
        for opt in vars(opts):
            if getattr(opts, opt): 
                setattr(self, opt, getattr(opts, opt))

class Tester(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog="skilltest", add_help=False)

        shared = argparse.ArgumentParser(add_help=False)
        shared.add_argument("--filter", type=str)
        shared.add_argument("--random", type=int)
        shared.add_argument("--digits", default=False, action=("store_true"))

        subpar = self.parser.add_subparsers()

        sp = subpar.add_parser("file", parents=[shared])
        sp.add_argument("--utterances", default=False, action=("store_true"))
        sp.add_argument("path", type=argparse.FileType("r"))
        sp.set_defaults(func=Tester.handle_file)

        sp = subpar.add_parser("exec", parents=[shared])
        sp.add_argument("cmd", type=str)
        sp.set_defaults(func=Tester.handle_exec)

        sp = subpar.add_parser("text", parents=[shared])
        sp.add_argument("text", type=str)
        sp.set_defaults(func=Tester.handle_text)

    def process(self, testname):
        global OPTS

        # Locate the test file
        if os.path.exists(testname):
            path = testname
        else:
            path = os.path.join(OPTS.testsdir, testname)
            if not os.path.exists(path):
                print("Unable to locate test:", testname)
                return
 
        # Preserve options
        savedopts = deepcopy(OPTS)

        tests = []
        with open(path) as f:
            print()
            print("#" * 80)
            print("Test:", testname)
            print("#" * 80)

            # Load the test
            test = json.load(f)

            # Merge any embedded config options
            if "config" in test:
                OPTS.merge_dict(test["config"])

            # Using unit testing?
            if "unittest" in test or OPTS.keep:
                # Must single thread if unit testing or keeping results
                OPTS.tasks = 1

            print()
            print("=" * 80)
            print("Resolving utterances")
            print("=" * 80)
            print()

            types = {}
            for name in test.get("types", {}):
                typename = "{%s}" % name
                types[typename] = []
                for val in test["types"][name]:
                    types[typename] += self.get_values(val)

            for val in test["utterances"]:
                for utterance in self.get_values(val):
                    typenames = VAR_RE.findall(utterance)

                    iterables = []
                    for typename in typenames:
                        if typename not in types:
                            # Extract the slot name without curly braces for the error message
                            slotname = typename.strip('{}')
                            print()
                            print("ERROR: Utterance contains slot type '%s' that is not defined in the 'types' section." % slotname)
                            print("       Utterance: %s" % utterance)
                            print()
                            print("Please add '%s' to the 'types' dictionary in your test definition." % slotname)
                            print()
                            sys.exit(1)
                        iterables.append(types[typename])

                    for iterable in itertools.product(*iterables):
                        t = {}
                        ndx = 0
                        for typename in typenames:
                            t[typename] = iterable[ndx]
                            ndx += 1

                        # Substitute the slot names with values
                        last = 0
                        resolved = ""
                        for match in VAR_RE.finditer(utterance):
                            val = t[match.group(0)]
                            resolved += utterance[last:match.start()] + val
                            last = match.end()
                        resolved += utterance[last:]

                        print("Utterance:", utterance)
                        print("    \\---->", resolved)
                        filepfx = resolved.replace(" ", "_").replace("'", "")
                        tests.append([testname, utterance, resolved, filepfx, t])

        if not OPTS.bypass:
            if "setup" in test:
                print()
                print("=" * 80)
                print("Performing setup")
                print("=" * 80)
                print()

                for action in test["setup"]:
                    for val in self.get_values(action):
                        filepfx = "SETUP_" + val.replace(" ", "_").replace("'", "")
                        # Extract intent and slots for setup action
                        intent_name, slots = extract_intent_and_slots(val, val, {})
                        run_skill(filepfx, intent_name, slots, val)

            print()
            print("=" * 80)
            print("Invoking lambda function directly")
            print("=" * 80)
            print()

            with ProcessPoolExecutor(max_workers=OPTS.tasks) as executor:
                for testname, utterance, resolved, filepfx, types in tests:
                    print("Processing:", resolved)
                    
                    # Extract intent name and slots from utterance
                    intent_name, slots = extract_intent_and_slots(utterance, resolved, types)
                    
                    if OPTS.tasks > 1:
                        executor.submit(run_skill, filepfx, intent_name, slots, resolved)
                        continue
                    
                    # Invoke the skill directly
                    response = run_skill(filepfx, intent_name, slots, resolved)

                    # Continue to next utterance if we're not checking results
                    if "unittest" not in test and not OPTS.keep:
                        continue

                    # Use the response directly - load from saved file
                    with open(os.path.join(OPTS.outputdir, filepfx + ".json"), "rt") as f:
                        data = json.load(f)
                        er = {"event": data["request"], "response": data["response"]}

                    # Make sure we have both the event and response dicts
                    if "event" not in er or "response" not in er:
                        print("Results message missing event/response dict")
                        continue

                    # Remove the braces from the type names
                    newtypes = {}
                    for t in types:
                        newtypes[t.strip("{}")] = types[t]

                    # Create the unit test input
                    data = \
                    {
                        "testname": testname,
                        "utterance": utterance,
                        "resolved": resolved,
                        "types": newtypes,
                        "message": er
                    }

                    # Write it out if keeping results
                    if OPTS.keep:
                        with open(os.path.join(OPTS.outputdir, filepfx + ".txt"), "wt") as f:
                            json.dump(data, f, indent=4)

                    # Done if we're not doing unit testing
                    if "unittest" not in test:
                        continue

                    unittest = test["unittest"].replace("{skilldir}", OPTS.skilldir). \
                                                replace("{testsdir}", OPTS.testsdir)

                    p = Popen(unittest, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                    _, err = p.communicate(json.dumps(data).encode("UTF-8"))

                    leader = "Unittest:   "
                    err = err.decode("UTF-8").replace("\r\n", "\n").replace("\r", "\n")
                    for line in err.split("\n"):
                        print("%s %s" % (leader, line))
                        leader = " " * 12

                executor.shutdown(wait=True)

            if "cleanup" in test:
                print()
                print("=" * 80)
                print("Performing cleanup")
                print("=" * 80)
                print()

                for action in test["cleanup"]:
                    for val in self.get_values(action):
                        filepfx = "CLEANUP_" + val.replace(" ", "_").replace("'", "")
                        # Extract intent and slots for cleanup action
                        intent_name, slots = extract_intent_and_slots(val, val, {})
                        run_skill(filepfx, intent_name, slots, val)

        # Restore options
        OPTS = deepcopy(savedopts)
 
    def get_values(self, instr):
        instr = instr.replace("{skilldir}", OPTS.skilldir). \
                      replace("{testsdir}", OPTS.testsdir)

        argv = shlex.split(instr)
        args = self.parser.parse_args(argv)
        vals = args.func(self, args)

        if args.filter:
            rx = re.compile(args.filter or r".*") 
            vals = [val for val in vals if rx.match(val)]

        if args.random:
            vals = random.sample(vals, int(args.random))

        if args.digits:
            vals = [" ".join(list(val)) if val.isdigit() else val for val in vals]

        return vals

    def handle_exec(self, args):
        vals = []
        lines = check_output(args.cmd, shell=True).decode("UTF-8").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for line in lines:
            line = line.strip()
            if not line.startswith("#") and len(line) > 0:
                vals.append(line)

        return vals

    def handle_file(self, args):
        vals = []
        lines = args.path.readlines()
        for line in lines:
            line = line.strip()
            if not line.startswith("#") and len(line) > 0:
                if args.utterances:
                    vals.append(line.partition(" ")[2].strip())
                else:
                    vals.append(line)

        args.path.close()

        return vals

    def handle_text(self, args):
        return [args.text]

def main():
    global OPTS
    multiprocessing.log_to_stderr()

    parser = argparse.ArgumentParser(description='Alexa Skill Tester - Direct Lambda Invocation')
    parser.add_argument("file", nargs="*",
                        help="name of test file(s)")
    parser.add_argument("-C", "--config", type=argparse.FileType('rt'),
                        help="path to configuration file")
    parser.add_argument("-I", "--inputdir", type=str,
                        help="path to input directory (for compatibility)")
    parser.add_argument("-O", "--outputdir", type=str,
                        help="path to output directory for results")
    parser.add_argument("-S", "--skilldir", type=str,
                        help="path to skill directory")
    parser.add_argument("-T", "--testsdir", type=str,
                        help="path to tests directory")
    parser.add_argument("-L", "--lambda_dir", type=str,
                        help="path to lambda function directory")
    parser.add_argument("-M", "--lambda_module", type=str,
                        help="lambda module name (default: lambda_function)")
    parser.add_argument("-H", "--lambda_handler", type=str,
                        help="lambda handler function name (default: lambda_handler)")
    parser.add_argument("-t", "--tasks", type=int,
                        help="number of concurrent tasks")
    parser.add_argument("-b", "--bypass", action="store_const", const=True,
                        help="bypass calling lambda to process utterance")
    parser.add_argument("-i", "--invocation", type=str,
                        help="invocation name of skill")
    parser.add_argument("-k", "--keep", action="store_const", const=True,
                        help="keep the event/response for each utterance")
    parser.add_argument("-w", "--writeconfig",
                        help="path for generated configuration file")

    args = parser.parse_args()

    if args.writeconfig is not None:
        try:
            with open(args.writeconfig, "w") as c:
                json.dump(CFG, c, indent=4)
                print("sample configuration written to %s" % args.writeconfig)
        except:
            print("Couldn't generate config file:", args.writeconfig)
        quit()

    # Create an instance of our base options
    OPTS = Options()

    # Merge in any global options
    OPTS.load_config("~")

    # Merge in any local options
    OPTS.load_config(".")

    # A command line config file overrides global and local configs
    if args.config:
        OPTS = Options()
        OPTS.merge_dict(json.load(args.config))
        args.config.close()
        args.config = None

    # Merge args into the options
    OPTS.merge_args(args)

    # Run the tests
    tester = Tester()
    if OPTS.file:
        for name in OPTS.file:
            tester.process(name)
    else:
        for name in os.listdir(OPTS.testsdir):
            if name.startswith("test_"):
                tester.process(os.path.join(OPTS.testsdir, name))

if __name__ == "__main__":
    main()
