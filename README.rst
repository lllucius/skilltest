.. contents::

About *skilltest*
=================

The *skilltest* command makes Alexa skill testing much easier and less tedious.
You still have to review the generated audio responses, but when you have dozens
or hundreds of utterance permutations, using *skilltest* will save you a lot of
time and your voice.

Through the use of test definitions, you give *skilltest* the utterances and sample
slot values it needs to provide synthesized input to the Alexa Voice Service.  It
then saves the MP3 files created by AVS for your review.

To create the voice input, *skilltest* can use several text-to-speech methods
including Windows *SAPI5*, the *espeak* command line utility, and the Mac OS X
*say* command line utility.

Caveat
======

Because *skilltest* is intended to function completely unattended and (currently) from the command line, it auto accepts the AVS consent and acknowledgement web pages on your behalf.  Please do not use *skilltest* if you don't want to accept them.

However, I may change this to bring up the default web browser the first time you use a new AVS device.  I'm also looking into added a web UI to *skilltest*.  In either of those cases, the normal AVS acceptance process could be used.

Installation
============

Package requirements
--------------------

All of these non-core packages should get installed automatically via pip when you
install *skilltest*:

- `bs4 <https://pypi.python.org/pypi/bs4>`_
- `numpy <https://pypi.python.org/pypi/numpy>`_
- `requests <https://pypi.python.org/pypi/requests>`_
- `requests_toolbelt <https://pypi.python.org/pypi/requests-toolbelt>`_
- `samplerate <https://pypi.python.org/pypi/samplerate>`_
- `soundfile <https://pypi.python.org/pypi/SoundFile>`_

Installing *skilltest*
----------------------

| If you downloaded the *skilltest* tarball, go ahead and extract the files and change into the resulting directory.
|
| If you checked out the source from GitHub, just change to the repo directory.
|
| Installing *skilltest* isn't absolutely necessary since it will happily run from this directory.  And since it's only a single module, it's easy to just throw it where ever you like, just ensure that all of the requirements listed above are installed.
|
| But, if you prefer to install, then simply run setup.py:
|

 | ``python setup.py install``

Configuration
=============

Speech synthesizer setup
------------------------

*skilltest* requires a speech synthesizer to convert the utterances to audio input that is then sent to AVS.  I've found that a lower pitched voice seems to work better, so try a male voice to start with.

There's many options for synthesizers, but the easiest (and free) are:

Windows
^^^^^^^

*skilltest* can use the default SAPI5 voice when running under native Windows or within the Windows Subsystem for Linux (I absolutely LOVE WSL!).

To set the default voice:

1. Right click the Start Menu icon on the taskbar.
2. Click **Run**.
3. Enter **C:\\WINDOWS\\System32\\Speech\\SpeechUX\\sapi.cpl** into the **Open** box
4. Click **OK**.
5. Choice from the **Voice selection** drop down.
6. Click **OK**.

Linux
^^^^^

The espeak **en+m2** voice works pretty well with AVS, so just install the latest espeak package and you should be good to go.  *skilltest* is set up to use **en+m2**, so if it doesn't come with your espeak package, you have to modify the *skilltest* source to select a different one.

Mac OS X
^^^^^^^^

OS X comes with a very nice set of voices and *skilltest* is set up to use the default system voice.

To select which one to use:

1. Open **System Preferences**.
2. Click on **Accessibility**.
3. Select **Speech** in the list on the left.
4. Select the desired voice in the **System Voice** drop down.

AVS device setup
----------------

If you're building a skill, then you already have an Amazon developer account, so you should be able to create the AVS device.  It looks a little daunting at first, but it's pretty easy.

Log into your developer account and:

1. Click the **Alexa** tab.
2. Under **Alexa Voice Service**, click the **Get Started >** button.
3. Click the **Register a Product** button and select **Device** from the drop down.
4. Enter whatever you want for the **Device Type ID** and **Display Name** fields.  Good examples might be **SkillTestDevice** and **Skill Test Device** respectively.

 .. Note:: Copy the **Device Type ID** as you will need it during *climacast* configuration.

5. Click the **Next** button.
6. Click the **Security Profile** drop down and select **Create a new profile**.
7. Enter a name in the **Security Profile Name** field.  It could be the same as your **Device Type ID**.
8. Enter description in the **Security Profile Description** field.  I just use the **Display Name** value from above.
9. Click the **Next** button.

 .. Note:: Copy the **Client ID** and **Client Secret** values as you will need them during *skilltest* configuration.

10. Click the **Web Settings** tab.
11. Click the **Add Another** link for the **Allow Origins** setting.
12. Enter any valid URL in the edit box that appears.  A good value would be **https://localhost**.
13. Click the **Add Another** link for the **Allow Return URLs** setting.
14. Again, enter any valid URL in the edit box that appears.  A good example would be **https://localhost/return**.

 .. Note:: Copy this URL as it will be needed during *skilltest* configuration.

15. Click the **Next** button.
16. Select whatever item you like in the **Category** drop down, but **Other** seems to be the most appropriate.
17. Enter whatever you like in the **Description** field.
18. Click **No** for both of the radio buttons since this will only be used for testing Alexa skills.
19. Click **Submit**

You should see your new device in the list and you are now ready to create your *skilltest* configuration file.

Setting up *skilltest*
----------------------

The configuration file
^^^^^^^^^^^^^^^^^^^^^^

| The configuration of *skilltest* is controlled via simple JSON files.  Both **global** and **local** files are supported and some configuration items may be overridden via the command line or via the **config** dictionary within the test definition.

| When looking for configuration files, *skilltest* looks for the **global** configuration file in your **home** directory.  As stated in the Python documentation:
|

    | ''On Unix, an initial ~ is replaced by the environment variable HOME if it is set; otherwise the current user’s home directory is looked up in the password directory through the built-in module pwd. An initial ~user is looked up directly in the password directory.''
    |
    | ''On Windows, HOME and USERPROFILE will be used if set, otherwise a combination of HOMEPATH and HOMEDRIVE will be used. An initial ~user is handled by stripping the last directory component from the created user path derived above.''

| The **local** configuration file is looked for in the active directory when *skilltest* is executed.  This allows you to keep skill specific settings alongside your other skill files.

| For example, you might want to define all of the settings that would be shared when testing your different skills in the **global** configuration file and skill specific settings like the skill's invocation name, skill directory and tests directory would go into the **local** configuration file that might reside in the directory where you test your skill.
|

 .. Warning:: Because of the sensitive nature of the configuration file that contains the **password**, **clientid**, and **secret**, it is **VERY** important you protect this file from unauthorized eyes.  As there are multiple levels of configuration files available, you might store these sensitive values at the global level and the rest of the settings within a local *skill* configuration file.

| Here's the sample configuration file from the **example** subdirectory:

::

  {
      "inputdir": "./example/results/input",
      "outputdir": "./example/results/output",
      "skilldir": "./example/skill",
      "testsdir": "./example/tests",
      "bypass": false,
      "regen": false,
      "avstasks": 1,
      "ttstasks": 1,
      "ttsmethod": "espeak",
      "invocation": "your skill's invocation name",
      "email": "your AVS email address",
      "password": "your AVS password",
      "deviceid": "your AVS device type ID",
      "clientid": "your AVS device clientid",
      "secret": "your AVS device secret",
      "redirect": "your AVS device redirect URL"
  }

| Where:

 :inputdir: the path where the AVS voice input files get written.  It may be the same as the **outputdir** if desired.

 :outputdir: the path where the AVS response files get written.  Again, it may be the same as the **inputdir**, but you might want to keep them separate since the TTS process can be bypassed if the file already exists.  And you'll probably be cleaning the **outputdir** quite often.  (Makes it easier to review the output.)

 :skilldir: the path where you store (at least) your *utterance* file.  If your skill also uses custom types, you might want to store copies of them in this directory as they can be used to resolve slot values in the utterances.  (See the **example/skill** directory for samples.)

 :testsdir: the path were you store (at least) your *test definition* files.  You might want to also store pseudo custom types here for resolving slot values.  (See the **exampe/tests** director for samples.)

 :bypass: **true** or **false** Boolean that indicates whether utterances should be sent to AVS after resolving the slot values.  Setting this to **true** can be useful while creating your tests to review the correctness of the resolution.

 :regen: **true** or **false** Boolean when set to **true** will force regeneration of the AVS voice input files.  Otherwise, existing files using the same utterance will be reused.

 :avstasks: the number of AVS tasks that will be run concurrently.  While Amazon can probably handle anything you throw at it, you might want to be a good netizen and not set this too high.

 :ttstasks: the number of TTS tasks that will be run concurrently.  Totally depends on your machine, but setting to at least the number of processors core you have will greatly speed up TTS conversions.

 :ttsmethod: this tells *skilltest* which TTS method to use.  The valid values are **espeak**, **osx**, and **sapi**.  See `Speech synthesizer setup <Speech synthesizer setup_>`_ for a discussion of the different methods.

 :invocation: your skill's invocation name as defined in the Amazon **Skill Information** page for the target skill.  Other than the use of a synthesized voice, *skilltest* asks Alexa to invoke your skill just like you would, so it needs the invocation name.

 :email: your AWS developer email address is needed to perform initial authentication to your AVS test device.

 :password: your AWS developer password is needed as well.

 :deviceid: this is the **Device Type ID** you gave your AVS device.

 :clientid: this is the **Client ID** you copied when creating your AVS device.

 :secret: this is the **Client Secret** you copied when creating your AVS device.

 :redirect: this is the URL you entered for the **Allow Return URLs** settting when creating your AVS device.

Using *skilltest*
=================

Setting up the tests
--------------------

The test definition file
^^^^^^^^^^^^^^^^^^^^^^^^

| The following is a sample of a (hypothetical) test definition file.  It shows all of the items with several combinations of the methods used to provide test data.
|
| This definition can be found in **example/tests/test_example**:

::

  {
      "description":
      [
          "Tests the utterances that ask for things like: if it will be raining..."
      ],
      "utterances":
      [
          "file --utterances --filter '.*{leadin}.*' '{skilldir}/utterances'",
          "text 'additional utterances can be added'",
          "file --utterances 'as/well/as/more/files'"
      ],
      "types":
      {
          "leadin":
          [
              "file --filter '^(if|is|will).*be.*' '{skilldir}/type_leadin'",
              "text 'additional slot values may be specified as well'"
          ],
          "day":
          [
              "exec 'python {testsdir}/exec_month_day day 1 0 7'",
              "file --random 1 '{skilldir}/type_day'"
          ]
      },
      "setup":
      [
          "text 'Set rate to 109 percent'"
      ],
      "cleanup":
      [
          "text 'Set rate to 109 percent'"
      ],
      "config":
      {
          "ttsmethod": "espeak",
          "regen": true
      }
  }

| Where:

:utterances: (list) This is the only required item and it provides a list of all the utterances to be tested with this defintion.

:types: (dict) If the specified utterances contain slot names, then each name must have a corresponding entry in this dictionary.  You may have more types specified than are actually used by the utterances.

 :<slotname>: (list) Provides a list of values that *skilltest* will use to replace the slot name in the utterances.  It may be as many values as you need and *skilltest* will test the same utterance with each one substituted.  For example, if you have an utterance that has a slot expecting the names of the months and you provide all 12 names here, that utterance will be tested 12 times, once for each of the names.

:setup: (list) All items listed here will be performed before starting the testing.  This is useful for things like resetting skill configurations to a known state.

:cleanup: (list) This is the counterpart to **setup** and the items will be performed after all testing is complete.

:config: (dict) You may override any of the *skilltest* configuration settings when a test begins.  The example shown, changes the synthesizer and forces regeneration, presumably because this particular test works better with a different voice (for example).

|
| Each **list** item, may utilize any combination of different methods for supplying the test data.  You may specify as many as you need, just remember that for every item listed, each value provided by the method will cause an additional test to be sent to AVS and you can quickly get into the hundreds of tests.  See the **bypass** configuration and command line options for reviewing the utterances before actually testing.
|
| You may use the **{skilldir}** and **{testsdir}** variables in the items to refer to either of those paths.
|
| The methods utilize command line parsing for their arguments, so arguments with spaces should be quoted.
|
| The following arguments are optional and can be used with all of the methods:
|

 --filter  Specifies a regular expression that will be used to filter the provided values.  Mostly useful with the **file** and **exec** methods.
 --random  Specifies the number of values to randomly select from the list of provided values.  Mostly useful with the **file** and **exec** methods.
 --digits  A switch that tells *skilltest* to look for values that contain all digits and separate the digits with a space when substituting.  This is useful for things like zip codes where you'd typically say the individual digits.  For example, the number "55118" would be substituted as "5 5 1 1 8".

|
| Any empty ("") values or values beginning with a pound sign (#) will be dropped and will not be considered for the **random** and **filter** arguments.  This allows you to put comments into your pseudo-type files in case you want to describe why one particular entry was included.

|
| The methods are:
|

:text:  [--filter FILTER] [--random RANDOM] [--digits] text

    | specifies a text literal.  It will be substituted as-is.

:file:  [--filter FILTER] [--random RANDOM] [--digits] [--utterances] path

    | specifies the path to a file from which values should be read.  The **utterances** switch, if used, tells *skilltest* that the file contains a list of utterances and that it should ignore the intent name at the beginning each line.

:exec: [--filter FILTER] [--random RANDOM] [--digits] cmd

    | specifies a command to run.  All lines sent to stdout by the command will be used as values.

Running *skilltest*
-------------------

| The syntax of the *skilltest* command:

::

skilltest [-h] [-C CONFIG] [-I INPUTDIR] [-O OUTPUTDIR]
               [-S SKILLDIR] [-T TESTSDIR] [-a AVSTASKS] [-b]
               [-i INVOCATION] [-r] [-s {espeak,osx,sapi}] [-t TTSTASKS]
               [-w WRITECONFIG]
               [file [file ...]]

**positional arguments**:
  file                  name of test file(s)

**optional arguments**:
  -h, --help            show this help message and exit
  -C, --config          path to configuration file
  -I, --inputdir        path to voice input directory
  -O, --outputdir       path to voice output directory
  -S, --skilldir        path to skill directory
  -T, --testsdir        path to tests directory
  -a, --avstasks        number of concurrent AVS requests
  -b, --bypass          bypass calling AVS to process utterance
  -i, --invocation      invocation name of skill
  -r, --regen           regenerate voice input files
  -s, --synth           TTS synthesizer to use (espeak, osx, sapi)
  -t, --ttstasks        number of concurrent TTS conversions
  -w, --writeconfig     path for generated configuration file

| With the exception of the following, most of the arguments simply override the configuration file settings.  So refer to `The configuration file <The configuration file>`_ section for details.
|
| The **--config** argument allows you to specify the path of a configuration file that will be used instead of the **global** and **local** configurations.  The settings within this file will completely override all others except for any other command arguments and configuration settings specified within the test definitions.
|
| The **--writeconfig** argument writes out a skeleton configuration file to the specified path.
|
| If you do not specify the **file** argument, *skilltest* will look in the **testsdir** directory for all files beginning with **test_** and run the tests in each file it locates.
|
| However, if you do specify one or more **file** arguments, then *skilltest* will look for a files with that names (you may include relative or absolute paths).  If it doesn't find one, it will look in the **testsdir** for the file.

Example executions
------------------

Example **test_location**
^^^^^^^^^^^^^^^^^^^^^^^^^

The test definition:

::

  {
      "description":
      [
          "Tests the handling of the location"
      ],
      "utterances":
      [
          "text 'For the forecast in {location}'",
          "text 'For the current temperature in {location}'"
      ],
      "types":
      {
          "location":
          [
              "text 'west saint paul minnesota'",
              "text 'duluth'",
              "text 'phoenix'",
              "text 'new ulm minnesnowta'"
          ]
      }
  }

Produces:

::

  ################################################################################
  Test: test_location
  ################################################################################

  ================================================================================
  Resolving utterances
  ================================================================================

  Utterance: For the forecast in {location}
      \----> For the forecast in west saint paul minnesota
  Utterance: For the forecast in {location}
      \----> For the forecast in duluth
  Utterance: For the forecast in {location}
      \----> For the forecast in phoenix
  Utterance: For the forecast in {location}
      \----> For the forecast in new ulm minnesnowta
  Utterance: For the current temperature in {location}
      \----> For the current temperature in west saint paul minnesota
  Utterance: For the current temperature in {location}
      \----> For the current temperature in duluth
  Utterance: For the current temperature in {location}
      \----> For the current temperature in phoenix
  Utterance: For the current temperature in {location}
      \----> For the current temperature in new ulm minnesnowta

  ================================================================================
  Generating voice input files
  ================================================================================

  Generating: For the forecast in west saint paul minnesota
  Generating: For the forecast in duluth
  Generating: For the forecast in phoenix
  Generating: For the forecast in new ulm minnesnowta
  Generating: For the current temperature in west saint paul minnesota
  Generating: For the current temperature in duluth
  Generating: For the current temperature in phoenix
  Generating: For the current temperature in new ulm minnesnowta

  ================================================================================
  Processing voice input files
  ================================================================================

  Recognizing: For the forecast in west saint paul minnesota
  Recognizing: For the forecast in duluth
  Recognizing: For the forecast in phoenix
  Recognizing: For the forecast in new ulm minnesnowta
  Recognizing: For the current temperature in west saint paul minnesota
  Recognizing: For the current temperature in duluth
  Recognizing: For the current temperature in phoenix
  Recognizing: For the current temperature in new ulm minnesnowta

Example **test_month**
^^^^^^^^^^^^^^^^^^^^^^

The test definition:

::

  {
      "description":
      [
          "Tests the handling of the months."
      ],
      "utterances":
      [
          "text 'For the forecast on {month} {day}'"
      ],
      "types":
      {
          "month":
          [
              "file '{skilldir}/type_month'",
              "text 'bogus month'"
          ],
          "day":
          [
              "text '1st'"
          ]

      }
  }

Produces:

::

  ################################################################################
  Test: test_month
  ################################################################################

  ================================================================================
  Resolving utterances
  ================================================================================

  Utterance: For the forecast on {month} {day}
      \----> For the forecast on january 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on february 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on march 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on april 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on may 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on june 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on july 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on august 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on september 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on october 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on november 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on december 1st
  Utterance: For the forecast on {month} {day}
      \----> For the forecast on bogus month 1st

  ================================================================================
  Generating voice input files
  ================================================================================

  Generating: For the forecast on january 1st
  Generating: For the forecast on february 1st
  Generating: For the forecast on march 1st
  Generating: For the forecast on april 1st
  Generating: For the forecast on may 1st
  Generating: For the forecast on june 1st
  Generating: For the forecast on july 1st
  Generating: For the forecast on august 1st
  Generating: For the forecast on september 1st
  Generating: For the forecast on october 1st
  Generating: For the forecast on november 1st
  Generating: For the forecast on december 1st
  Generating: For the forecast on bogus month 1st

  ================================================================================
  Processing voice input files
  ================================================================================

  Recognizing: For the forecast on january 1st
  Recognizing: For the forecast on february 1st
  Recognizing: For the forecast on march 1st
  Recognizing: For the forecast on april 1st
  Recognizing: For the forecast on may 1st
  Recognizing: For the forecast on june 1st
  Recognizing: For the forecast on july 1st
  Recognizing: For the forecast on august 1st
  Recognizing: For the forecast on september 1st
  Recognizing: For the forecast on october 1st
  Recognizing: For the forecast on november 1st
  Recognizing: For the forecast on december 1st
  Recognizing: For the forecast on bogus month 1st

Example **test_zipcode**
^^^^^^^^^^^^^^^^^^^^^^^^

The test definition:

::


  {
      "description":
      [
          "Make sure zip code handling works correctly"
      ],
      "utterances":
      [
          "text 'For the alerts in {zipcode}'",
          "text 'For the alerts in zip code {zipcode}'"
      ],
      "types":
      {
          "zipcode":
          [
              "file --digits '{testsdir}/type_zipcode'",
              "text --digits 12142",
              "text --digits 11112"
          ]
      }
  }

Produces:

::

  ################################################################################
  Test: test_zipcode
  ################################################################################

  ================================================================================
  Resolving utterances
  ================================================================================

  Utterance: For the alerts in {zipcode}
      \----> For the alerts in 5 5 1 1 8
  Utterance: For the alerts in {zipcode}
      \----> For the alerts in 7 1 3 0 1
  Utterance: For the alerts in {zipcode}
      \----> For the alerts in 5 6 3 0 8
  Utterance: For the alerts in {zipcode}
      \----> For the alerts in 1 2 1 4 2
  Utterance: For the alerts in {zipcode}
      \----> For the alerts in 1 1 1 1 2
  Utterance: For the alerts in zip code {zipcode}
      \----> For the alerts in zip code 5 5 1 1 8
  Utterance: For the alerts in zip code {zipcode}
      \----> For the alerts in zip code 7 1 3 0 1
  Utterance: For the alerts in zip code {zipcode}
      \----> For the alerts in zip code 5 6 3 0 8
  Utterance: For the alerts in zip code {zipcode}
      \----> For the alerts in zip code 1 2 1 4 2
  Utterance: For the alerts in zip code {zipcode}
      \----> For the alerts in zip code 1 1 1 1 2

  ================================================================================
  Generating voice input files
  ================================================================================

  Generating: For the alerts in 5 5 1 1 8
  Generating: For the alerts in 7 1 3 0 1
  Generating: For the alerts in 5 6 3 0 8
  Generating: For the alerts in 1 2 1 4 2
  Generating: For the alerts in 1 1 1 1 2
  Generating: For the alerts in zip code 5 5 1 1 8
  Generating: For the alerts in zip code 7 1 3 0 1
  Generating: For the alerts in zip code 5 6 3 0 8
  Generating: For the alerts in zip code 1 2 1 4 2
  Generating: For the alerts in zip code 1 1 1 1 2

  ================================================================================
  Processing voice input files
  ================================================================================

  Recognizing: For the alerts in 5 5 1 1 8
  Recognizing: For the alerts in 7 1 3 0 1
  Recognizing: For the alerts in 5 6 3 0 8
  Recognizing: For the alerts in 1 2 1 4 2
  Recognizing: For the alerts in 1 1 1 1 2
  Recognizing: For the alerts in zip code 5 5 1 1 8
  Recognizing: For the alerts in zip code 7 1 3 0 1
  Recognizing: For the alerts in zip code 5 6 3 0 8
  Recognizing: For the alerts in zip code 1 2 1 4 2
  Recognizing: For the alerts in zip code 1 1 1 1 2

