# Migration Guide: From AVS to Direct Lambda Invocation

## Overview

This guide helps you migrate from the AVS-based skilltest to the new direct lambda invocation version.

## What Changed?

### Architecture Change

**Old (AVS-based):**
```
Test Utterances → TTS → Audio Files → AVS API → Alexa Skill → SQS → Results
```

**New (Direct Invocation):**
```
Test Utterances → Alexa Request JSON → Lambda Function → Response JSON → Results
```

### Key Benefits

1. **No deprecated APIs** - Doesn't rely on deprecated AVS APIs
2. **Faster** - No TTS conversion or network calls to AVS
3. **Simpler** - Fewer dependencies and configuration options
4. **Offline** - Works completely offline
5. **Direct access** - Request and response JSON always saved

## Configuration Changes

### Old Configuration

```json
{
    "inputdir": "./results/input",
    "outputdir": "./results/output",
    "skilldir": "./skill",
    "testsdir": "./tests",
    "bypass": false,
    "regen": false,
    "keep": false,
    "avstasks": 1,
    "ttstasks": 1,
    "synth": "espeak",
    "invocation": "my skill",
    "queueurl": "https://sqs.us-east-1.amazonaws.com/...",
    "email": "user@example.com",
    "password": "secret",
    "deviceid": "MyDevice",
    "clientid": "amzn1.application-oa2-client...",
    "secret": "abc123...",
    "redirect": "https://localhost/return"
}
```

### New Configuration

```json
{
    "inputdir": "./results/input",
    "outputdir": "./results/output",
    "skilldir": "./skill",
    "testsdir": "./tests",
    "bypass": false,
    "regen": false,
    "keep": false,
    "tasks": 1,
    "invocation": "my skill",
    "queueurl": null,
    "lambda_dir": "./lambda",
    "lambda_module": "lambda_function",
    "lambda_handler": "lambda_handler"
}
```

### Configuration Changes

**Removed:**
- `avstasks` → replaced with `tasks`
- `ttstasks` → no longer needed (no TTS)
- `synth` → no longer needed (no TTS)
- `email` → no longer needed (no AVS authentication)
- `password` → no longer needed (no AVS authentication)
- `deviceid` → no longer needed (no AVS device)
- `clientid` → no longer needed (no AVS authentication)
- `secret` → no longer needed (no AVS authentication)
- `redirect` → no longer needed (no AVS authentication)

**Added:**
- `lambda_dir` → path to your lambda function directory
- `lambda_module` → name of your lambda module (default: "lambda_function")
- `lambda_handler` → name of your handler function (default: "lambda_handler")

**Changed:**
- `queueurl` → now optional (results are always saved to JSON files)
- `inputdir` → deprecated but kept for compatibility
- `regen` → deprecated but kept for compatibility

## Test Definition Changes

### Intent Names in Utterances

**Important:** Utterances now need to include the intent name at the beginning.

**Old format (intent extracted from file):**
```json
{
    "utterances": [
        "text 'For the forecast in {location}'"
    ]
}
```

**New format (intent included):**
```json
{
    "utterances": [
        "text 'ForecastIntent For the forecast in {location}'"
    ]
}
```

The format is: `IntentName Rest of utterance with {slots}`

If no intent name is provided, it defaults to "TestIntent".

### Setup and Cleanup

Setup and cleanup actions now invoke the lambda function directly instead of using TTS/AVS.

## Lambda Function Setup

### Directory Structure

```
your-project/
├── .skilltest                    # Configuration file
├── lambda/                       # Your lambda function
│   ├── lambda_function.py       # Main handler
│   └── ... (other modules)
├── skill/                        # Skill data (utterances, types)
└── tests/                        # Test definitions
    ├── test_forecast
    ├── test_weather
    └── ...
```

### Lambda Function Requirements

Your lambda function must:

1. **Have a handler function** that takes `(event, context)` parameters
2. **Accept None as context** during testing
3. **Return proper Alexa response JSON**

Example:

```python
def lambda_handler(event, context):
    """Main lambda handler"""
    request = event['request']
    intent = request['intent']
    intent_name = intent['name']
    
    # Your skill logic here
    
    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': 'Your response here'
            },
            'shouldEndSession': True
        }
    }
```

## Migration Steps

### Step 1: Update Configuration

1. Copy your existing `.skilltest` configuration
2. Remove all AVS-related settings:
   - `email`, `password`, `deviceid`, `clientid`, `secret`, `redirect`
   - `synth`, `ttstasks`, `avstasks`
3. Add lambda settings:
   - `lambda_dir`: Path to your lambda function (e.g., "./lambda")
   - `lambda_module`: Module name (default: "lambda_function")
   - `lambda_handler`: Handler function (default: "lambda_handler")
4. Make `queueurl` optional:
   - Set to `null` if not using SQS
   - Keep if you still want SQS validation
5. Rename `avstasks` to `tasks`

### Step 2: Update Test Definitions

1. Review all test utterances
2. Add intent names at the beginning of each utterance:
   ```
   "text 'IntentName utterance text with {slots}'"
   ```
3. Update setup/cleanup actions if needed

### Step 3: Set Up Lambda Function

1. Ensure your lambda function is in a local directory
2. Verify the handler function signature: `def lambda_handler(event, context)`
3. Test that your lambda can accept `None` as the context parameter
4. Make sure all dependencies are importable from the lambda directory

### Step 4: Test the Migration

1. Run a simple test first:
   ```bash
   python skilltest.py tests/test_simple
   ```

2. Check the output directory for JSON files

3. Verify the request/response structure

4. Run your full test suite

## Output Changes

### Old Output

- `inputdir/` - WAV audio files
- `outputdir/` - MP3 response files

### New Output

- `outputdir/` - JSON files with request and response

Example output file:
```json
{
  "request": {
    "version": "1.0",
    "session": { ... },
    "request": {
      "type": "IntentRequest",
      "intent": {
        "name": "ForecastIntent",
        "slots": {
          "location": {
            "name": "location",
            "value": "Seattle"
          }
        }
      }
    }
  },
  "response": {
    "version": "1.0",
    "response": {
      "outputSpeech": {
        "type": "PlainText",
        "text": "The forecast for Seattle..."
      },
      "shouldEndSession": true
    }
  }
}
```

## Troubleshooting

### Lambda Function Not Found

**Error:** `FileNotFoundError: Lambda function not found at ...`

**Solution:** 
- Check that `lambda_dir` points to the correct directory
- Verify that the file `<lambda_module>.py` exists in that directory (e.g., `lambda_function.py`)
- Use absolute or relative paths correctly

### Handler Not Found

**Error:** `AttributeError: Handler 'lambda_handler' not found in lambda_function`

**Solution:**
- Check that your handler function name matches `lambda_handler` config
- Verify the function is defined at module level, not inside a class

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'your_module'`

**Solution:**
- Ensure all dependencies are installed
- Check that modules are in the lambda directory or Python path
- Install required packages: `pip install -r requirements.txt`

### Intent Name Issues

**Error:** Tests run but slots aren't recognized

**Solution:**
- Add intent name at the start of utterances
- Format: `"text 'IntentName utterance with {slots}'"`

## Rollback

If you need to rollback to the AVS version:

1. Check out the previous version from git
2. Restore your old `.skilltest` configuration
3. Reinstall old dependencies: `pip install bs4 numpy requests requests_toolbelt samplerate soundfile`

## Getting Help

If you encounter issues:

1. Check the example in `example/` directory
2. Review test files in `example/tests/`
3. Look at the example lambda function in `example/lambda/lambda_function.py`
4. Open an issue on GitHub with your configuration and error messages
