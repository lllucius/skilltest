# Skilltest 2.0 - Direct Lambda Invocation

## Overview

This repository has been successfully migrated from using deprecated Alexa Voice Services (AVS) APIs to directly invoking local lambda functions. This modernizes the testing framework and makes it faster, simpler, and more maintainable.

## What's New in Version 2.0

### Direct Lambda Invocation
- Tests now invoke your lambda function directly instead of going through AVS
- No need for voice synthesis or network calls
- Faster test execution
- Better debugging with direct access to request/response JSON

### Simplified Dependencies
- **Removed**: bs4, numpy, requests, requests_toolbelt, samplerate, soundfile, boto3
- No external dependencies required
- Lighter installation footprint
- Fewer compatibility issues

### Enhanced Testing
- Request and response JSON always saved to output directory
- Same test definition format for backward compatibility
- Better error messages and debugging

## Quick Start

### 1. Install

```bash
python setup.py install
```

Or run directly from the repository:

```bash
python skilltest.py --help
```

### 2. Configure

Create a `.skilltest` configuration file:

```json
{
    "outputdir": "./results/output",
    "skilldir": "./skill",
    "testsdir": "./tests",
    "lambda_dir": "./lambda",
    "lambda_module": "lambda_function",
    "lambda_handler": "lambda_handler",
    "invocation": "my skill name"
}
```

### 3. Write Tests

Create test files in your tests directory (e.g., `tests/test_forecast`):

```json
{
    "description": ["Test forecast intent"],
    "utterances": [
        "text 'ForecastIntent For the forecast in {location}'"
    ],
    "types": {
        "location": [
            "text 'Seattle'",
            "text 'New York'"
        ]
    }
}
```

### 4. Run Tests

```bash
python skilltest.py tests/test_forecast
```

Or run all tests:

```bash
python skilltest.py
```

## Example

The `example/` directory contains a complete working example:

```bash
cd skilltest
python skilltest.py -C example/dot_skilltest example/tests/test_simple
```

This will:
1. Load the configuration from `example/dot_skilltest`
2. Invoke the lambda function in `example/lambda/lambda_function.py`
3. Save results to `example/results/output/`

## Output

Test results are saved as JSON files in the output directory:

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
      }
    }
  }
}
```

## Migration from Version 1.x

If you're migrating from the AVS-based version, see [MIGRATION.md](MIGRATION.md) for a complete guide.

Key changes:
- Update configuration to remove AVS settings
- Add lambda function settings
- Prefix utterances with intent names
- Remove TTS-related configurations

## Documentation

- [README.rst](README.rst) - Full documentation
- [MIGRATION.md](MIGRATION.md) - Migration guide from AVS version
- [example/](example/) - Complete working example

## Requirements

- Python 2.7+ or Python 3.4+
- Your lambda function and its dependencies

## License

GNU Affero General Public License v3 or later (AGPLv3+)

## Author

Leland Lucius

## Contributing

Issues and pull requests are welcome on GitHub.
