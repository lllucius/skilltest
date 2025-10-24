#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example Alexa Skill Lambda Function

This is a simple example lambda function that can be used for testing
the skilltest framework with direct lambda invocation.
"""

def lambda_handler(event, context):
    """
    Main entry point for the Alexa skill
    
    Args:
        event: The Alexa request event
        context: Lambda context (may be None during testing)
    
    Returns:
        The Alexa response object
    """
    
    request = event.get('request', {})
    request_type = request.get('type', '')
    
    if request_type == 'LaunchRequest':
        return handle_launch_request(event)
    elif request_type == 'IntentRequest':
        return handle_intent_request(event)
    elif request_type == 'SessionEndedRequest':
        return handle_session_ended_request(event)
    else:
        return build_response("I didn't understand that request.")

def handle_launch_request(event):
    """Handle LaunchRequest"""
    speech_text = "Welcome to the example skill! You can ask me for the forecast or weather."
    return build_response(speech_text, should_end_session=False)

def handle_intent_request(event):
    """Handle IntentRequest"""
    intent = event['request']['intent']
    intent_name = intent['name']
    slots = intent.get('slots', {})
    
    if intent_name == 'TestIntent':
        return handle_test_intent(slots)
    elif intent_name in ['ForecastIntent', 'WeatherIntent', 'TemperatureIntent']:
        return handle_weather_intent(intent_name, slots)
    elif intent_name == 'AMAZON.HelpIntent':
        return handle_help_intent()
    elif intent_name == 'AMAZON.CancelIntent' or intent_name == 'AMAZON.StopIntent':
        return handle_cancel_intent()
    else:
        return build_response("I don't know how to handle that intent.")

def handle_test_intent(slots):
    """Handle TestIntent"""
    metric = slots.get('metric', {}).get('value', 'unknown')
    speech_text = f"You asked for the {metric}. This is a test response."
    return build_response(speech_text)

def handle_weather_intent(intent_name, slots):
    """Handle weather-related intents"""
    location = slots.get('location', {}).get('value', 'your location')
    day = slots.get('day', {}).get('value', '')
    month = slots.get('month', {}).get('value', '')
    metric = slots.get('metric', {}).get('value', 'weather')
    
    date_str = ""
    if month and day:
        date_str = f" on {month} {day}"
    elif day:
        date_str = f" on {day}"
    
    if intent_name == 'ForecastIntent':
        speech_text = f"The forecast for {location}{date_str} will be sunny with a high of 75 degrees."
    elif intent_name == 'TemperatureIntent':
        speech_text = f"The current temperature in {location} is 72 degrees."
    else:
        speech_text = f"The weather in {location}{date_str} is sunny."
    
    return build_response(speech_text)

def handle_help_intent():
    """Handle AMAZON.HelpIntent"""
    speech_text = "You can ask me for the forecast or current weather. What would you like to know?"
    return build_response(speech_text, should_end_session=False)

def handle_cancel_intent():
    """Handle AMAZON.CancelIntent or AMAZON.StopIntent"""
    speech_text = "Goodbye!"
    return build_response(speech_text)

def handle_session_ended_request(event):
    """Handle SessionEndedRequest"""
    return build_response("")

def build_response(speech_text, should_end_session=True):
    """
    Build an Alexa response
    
    Args:
        speech_text: The text to speak
        should_end_session: Whether to end the session
    
    Returns:
        The Alexa response object
    """
    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_text
            },
            'shouldEndSession': should_end_session
        }
    }
