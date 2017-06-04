#!/usr/bin/python

from __future__ import print_function

import argparse
import base64
import io
import itertools
import json
import multiprocessing
import numpy as np
import os
import random
import re
import requests
import samplerate
import shlex
import soundfile
import sys
import types
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime
from requests_toolbelt import MultipartDecoder
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

CFG = \
{
    "inputdir": "./results/input",
    "outputdir": "./results/output",
    "skilldir": "./skill",
    "testsdir": "./tests",
    "bypass": False,
    "regen": False,
    "numtasks": 1,
    "ttsmethod": "sapi" if PLAT == "win32" else "osx" if PLAT == "darwin" else "espeak",
    "invocation":  "your skill's invocation name",
    "email": "your AVS email address",
    "password": "your AVS password",
    "clientid": "your AVS device clientid",
    "secret": "your AVS device secret",
    "deviceid": "your AVS device type ID",
    "redirect": "your AVS device redirect URL"
}

# Minimum required extra headers
HEADERS = \
{
    # Required for both login and API
    "Accept-Language": "en,*;q=0.1",
    # Must be a "known" user agent, otherwise we don't get a "session-id" cookie
    "User-Agent": "Links (2.14; CYGWIN_NT-10.0 2.6.1(0.305/5/3) x86_64; GNU C 5.4; text)"
}

def run_tts(filepfx, text):
    try:
        soundfile.write(os.path.join(OPTS.inputdir, filepfx + ".wav"),
                        TTS().convert("alexa ask %s %s" % (OPTS.invocation, text)),
                        16000,
                        format="WAV")
    except Exception as e:
        import traceback
        print("Caught exception generating:")
        print(text)
        print()
        traceback.print_exc()
        print()
        raise e

def run_avs(filepfx):
    try:
        with open(os.path.join(OPTS.inputdir, filepfx + ".wav"), "rb") as infile:
            with open(os.path.join(OPTS.outputdir, filepfx + ".mp3"), "wb") as outfile:
                outfile.write(AVS().recognize(infile))
    except Exception as e:
        print("Caught exception recognizing:")
        print(filepfx + ".wav")
        print()
        traceback.print_exc()
        print()
        raise e

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
        # Preserve options
        global OPTS
        savedopts = deepcopy(OPTS)
        
        tests = []
        with open(os.path.join(OPTS.testsdir, testname)) as f:
            print()
            print("#" * 80)
            print("Test:", testname)
            print("#" * 80)

            # Load the test
            test = json.load(f)

            # Merge any embedded config options
            if "config" in test:
                for var in test["config"]:
                    setattr(OPTS, var, test["config"][var])

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
                        print("    \---->", resolved)
                        filepfx = resolved.replace(" ", "_").replace("'", "")
                        tests.append([testname, utterance, resolved, filepfx])

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
                        run_tts(filepfx, val)
                        run_avs(filepfx)

            print()
            print("=" * 80)
            print("Generating voice input files")
            print("=" * 80)
            print()

            with ProcessPoolExecutor(max_workers=OPTS.numtasks) as executor:
                for testname, utterance, resolved, filepfx in tests:
                    name = os.path.join(OPTS.inputdir, filepfx + ".wav")
                    if not os.path.exists(name) or OPTS.regen:
                        print("Generating:", resolved)
                        if OPTS.numtasks == 1:
                            run_tts(filepfx, resolved)
                        else:
                            executor.submit(run_tts, filepfx, resolved)
                    else:
                        print("Reusing:", resolved)
                executor.shutdown(wait=True)

            print()
            print("=" * 80)
            print("Processing voice input files")
            print("=" * 80)
            print()

            with ProcessPoolExecutor(max_workers=OPTS.numtasks) as executor:
                for testname, utterance, resolved, filepfx in tests:
                    print("Recognizing:", resolved)
                    if OPTS.numtasks == 1:
                        run_avs(filepfx)
                    else:
                        executor.submit(run_avs, filepfx)
                executor.shutdown(wait=True)

            if "cleanup" in test:
                print()
                print("=" * 80)
                print("Performing cleanup")
                print("=" * 80)
                print()

                for action in test["setup"]:
                    for val in self.get_values(action):
                        filepfx = "CLEANUP_" + val.replace(" ", "_").replace("'", "")
                        run_tts(filepfx, val)
                        run_avs(filepfx)

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

class TTS(object):
    def __init__(self):
        pass

    def convert(self, text):
        if OPTS.ttsmethod == "espeak":
            raw = self.espeakTTS(text)
        elif OPTS.ttsmethod == "osx":
            raw = self.osxTTS(text)
        elif OPTS.ttsmethod == "sapi":
            raw = self.sapiTTS(text)
        return raw

    def espeakTTS(self, text):
        p = Popen("espeak -v en+m2 --stdin --stdout", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        out = p.communicate(text.encode("UTF-8"))[0]
        raw, rate = soundfile.read(io.BytesIO(out))
        return samplerate.resample(raw, 16000.0 / rate, "sinc_best")

    def osxTTS(self, text):
        p = Popen("tmp=$(mktemp) ; say --file-format=WAVE --data-format=LEI16@16000 -o ${tmp} && cat ${tmp} ; rm ${tmp}", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        out = p.communicate(bytes(text))[0]
        return soundfile.read(io.BytesIO(out))[0]

    def sapiTTS(self, text):
        if PLAT == "win32":
            # We want 16kHz, 16-bit, mono audio
            afmt = CreateObject("sapi.SpAudioFormat")
            afmt.Type = SpeechLib.SAFT16kHz16BitMono

            # Output audio goes to a memory stream
            strm = CreateObject("sapi.SpMemoryStream")
            strm.Format = afmt

            # Create the voice (uses the default system voice)
            spkr = CreateObject("sapi.SpVoice")
            spkr.AllowOutputFormatChangesOnNextSet = False
            spkr.AudioOutputStream = strm
            spkr.Speak(text)

            return np.fromstring(bytes(strm.GetData()), np.int16);

        # Get powershell up and running
        p = Popen("powershell.exe -NonInteractive -File -", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=False, cwd="/mnt/c")

        # Create the powershell commands
        cmd = """
              add-Type -AssemblyName System.Speech;
              add-Type -AssemblyName System.IO;
              $fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono);
              $wav = New-Object System.IO.MemoryStream;
              $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
              $synth.SetOutputToAudioStream($wav, $fmt);
              $synth.Speak('%s');
              [Console]::Error.Write([System.convert]::ToBase64String($wav.ToArray()));
              $synth.Dispose();
              $wav.Dispose();
              exit;
              """ % text.replace("'", "''")

        # Send them and get the response from stderr
        out = p.communicate(cmd.encode("UTF-8"))[1]
        return np.fromstring(base64.b64decode(out.decode("UTF-8")), np.int16)

class AVS(object):
    def __init__(self):
        self.sess = requests.Session()
        self.sess.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))

    def recognize(self, wav):
        self.auth()

        # make a copy of the headers
        headers = deepcopy(HEADERS)

        data = \
        {
            "messageHeader": 
            {
                "deviceContext": 
                [
                    {
                        "name": "playbackState",
                        "namespace": "AudioPlayer",
                        "payload": 
                        {
                            "streamId": "",
                            "offsetInMilliseconds": 0,
                            "playerActivity": "IDLE"
                        }
                    }
                ]
            },
            "messageBody": 
            {
                "profile": "alexa-close-talk",
                "locale": "en-us",
                "format": "audio/L16; rate=16000; channels=1"
            }
        }

        files = \
        [
            ( 
                "request",
                (
                    "request",
                    json.dumps(data),
                    "application/json; charset=UTF-8",
                )
            ),
            (
                "audio",
                (
                    "audio",
                    wav,
                    "audio/L16; rate=16000; channels=1"
                )
            )
        ]

        headers["Authorization"] = "Bearer %s" % OPTS.access

        # Call AVS
        url = "https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize"
        try:
            r = requests.post(url, headers=headers, files=files)
        except:
            wav.seek(0)
            r = requests.post(url, headers=headers, files=files)

        # Possibly refresh token and retry
        if r.status_code == 403:
            headers["Authorization"] = "Bearer %s" % self.refresh()
            r = requests.post(url, headers=headers, files=files)

        # If the request fails, retry
        if r.status_code != 200:
            #print(r.status_code)
            #for header in r.headers:
            #    print("HEADER:", header, ":", r.headers[header])
            #print(r.content)
            wav.seek(0)
            r = requests.post(url, headers=headers, files=files)

        try:
            for part in MultipartDecoder.from_response(r).parts:
                if part.headers[b"Content-Type"] == b"audio/mpeg":
                    return part.content
        except:
            pass

        # Request failed
        print(r.status_code)
        for header in r.headers:
            print(header, ":", r.headers[header])
        print(r.content)

        return None

    def auth(self):
        # Make a copy of the headers
        headers = deepcopy(HEADERS)

        # Manually handle redirection so we can detect our (dummy) URL
        def redirect_to(resp):
            target = self.sess.get_redirect_target(resp)
            while target is not None:
                if target.startswith(OPTS.redirect):
                    query = parse_qs(urlparse(target).query)
                    return resp, query["code"][0] if "code" in query else None
                resp =  self.sess.get(target, headers=headers, allow_redirects=False)
                target = self.sess.get_redirect_target(resp)
            return resp, None

        scope_data = \
        {
            "alexa:all":
            {
                "productID": OPTS.deviceid,
                "productInstanceAttributes":
                {
                    "deviceSerialNumber": "001"
                }
            }
        }

        data = \
        {
            "client_id": OPTS.clientid,
            "scope": "alexa:all",
            "scope_data": json.dumps(scope_data),
            "response_type": "code",
            "redirect_uri": OPTS.redirect
        }

        code = None

        # Refrieve the login page
        r = self.sess.get("https://www.amazon.com/ap/oa", headers=headers, params=data)

        # Extract the form fields
        form = BeautifulSoup(r.text, "html.parser").find("form", {"name": "acknowledgement-form"})
        if form is not None:
            data = {}
            for field in form.find_all("input"):
                if "name" in field.attrs and "value" in field.attrs:
                    data[field.attrs["name"]] = field.attrs["value"]

            # Approve it
            data["acknowledgementApproved"] = ""

            # Needed for login success
            headers["Referer"] = r.request.url

            # Post it.  Do not need to redirect here since the response has all we need
            r = self.sess.get(form.attrs["action"], params=data, headers=headers, allow_redirects=False)
            r, code = redirect_to(r)

        if code is None:
            # Extract the form fields
            form = BeautifulSoup(r.text, "html.parser").find("form", {"name": "signIn"})
            if form is not None:
                data = {}
                for field in form.find_all("input"):
                    if "name" in field.attrs and "value" in field.attrs:
                        data[field.attrs["name"]] = field.attrs["value"]

                # Set the email and password
                data["email"] = OPTS.email
                data["password"] = OPTS.password

                # Needed for login success
                self.sess.cookies["ap-fid"] = '""'
                headers["Referer"] = r.request.url

                # Post it.
                r = self.sess.post(form.attrs["action"], data=data, headers=headers, allow_redirects=False)
                r, code = redirect_to(r)
                
        if code is None:
            form = BeautifulSoup(r.text, "html.parser").find("form", {"name": "consent-form"})
            if form is not None:
                data = {}
                for field in form.find_all("input"):
                    if "name" in field.attrs and "value" in field.attrs:
                        data[field.attrs["name"]] = field.attrs["value"]

                # Approve it
                data["consentApproved"] = ""

                # Needed for login success
                headers["Referer"] = r.request.url

                # Post it.  Do not need to redirect here since the response has all we need
                r = self.sess.get(form.attrs["action"], params=data, headers=headers, allow_redirects=False)
                r, code = redirect_to(r)

        data = \
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OPTS.redirect,
            "client_id": OPTS.clientid,
            "client_secret": OPTS.secret
        }

        # Retreive the access code
        r = self.sess.post("https://api.amazon.com/auth/o2/token", headers=headers, data=data)
        data = r.json()
        if "access_token" in data and "refresh_token" in data:
            OPTS.access = data["access_token"]
            OPTS.refresh = data["refresh_token"]

    def refresh(self):
        # make a copy of the headers
        headers = deepcopy(HEADERS)

        data = \
        {
            "grant_type": "refresh_token",
            "refresh_token": OPTS.refresh,
            "client_id": OPTS.clientid,
            "client_secret": OPTS.secret
        }

        # Retrieve a new refresh token
        r = self.sess.post("https://api.amazon.com/auth/o2/token", headers=headers, data=data)
        data = r.json()
        OPTS.access = data["access_token"]
        OPTS.refresh = data["refresh_token"]

        return OPTS.access

def main():
    global OPTS
    multiprocessing.log_to_stderr()

    parser = argparse.ArgumentParser(description='Alexa Skill Tester')
    parser.add_argument("file", nargs="+",
                        help="name of test file(s)")
    parser.add_argument("-b", "--bypass", default=False, action="store_const", const=True,
                        help="bypass calling AVS to process utterance")
    parser.add_argument("-c", "--config", type=str, default="./.config",
                        help="path to configuration file")
    parser.add_argument("-i", "--inputdir", type=str,
                        help="path to voice input directory")
    parser.add_argument("-n", "--numtasks", type=int,
                        help="number of concurrent requests to run")
    parser.add_argument("-o", "--outputdir", type=str,
                        help="path to voice output directory")
    parser.add_argument("-r", "--regen", default=False, action="store_const", const=True,
                        help="regenerate voice input files")
    parser.add_argument("-s", "--skilldir", type=str,
                        help="path to skill directory")
    parser.add_argument("-t", "--testsdir", type=str,
                        help="path to tests directory")
    parser.add_argument("-v", "--voice", choices=["espeak", "osx", "sapi"],
                        help="TTS synthesizer to use")
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

    try:
        with open(args.config, "rt") as c:
            BaseOptions = type("BaseOptions", (), json.load(c))
    except:
        print("Couldn't load config file %s" % args.config)
        quit()

    # Create an instance of our base options
    OPTS = BaseOptions()

    # Merge args into the options
    for arg in vars(args):
        if getattr(args,arg):
            setattr(OPTS, arg, getattr(args, arg))

    # Need comtypes if we're using SAPI under native Windows (not WSL)
    if OPTS.ttsmethod == "sapi" and PLAT == "win32":
        from comtypes.client import CreateObject
        from comtypes.gen import SpeechLib

    tester = Tester()

    if len(OPTS.file) > 0:
        for name in OPTS.file:
            tester.process(name)
    else:
        for name in os.listdir(OPTS.testsdir):
            if name.startswith("test_"):
                tester.process(name)

if __name__ == "__main__":
    main()
