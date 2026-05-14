# -*- coding: utf-8 -*-

"""
Use Amazon Bedrock to ask "Who are you?" to AI.
"""

import boto3
import json

# Create Bedrock Client
session = boto3.Session()
bedrock = session.client(service_name="bedrock-runtime", region_name="us-east-1")

# Prepare message
model_id = "us.amazon.nova-micro-v1:0"  # Use the cheapest model
system_prompt = "You are a helpful AI assistant."
user_message = "Who are you? Please answer in a short sentence."

# Build request
messages = [{"role": "user", "content": [{"text": user_message}]}]

# Call API
response = bedrock.converse(
    modelId=model_id,
    messages=messages,
    system=[{"text": system_prompt}],
    inferenceConfig={"maxTokens": 200, "temperature": 0.7},
)

# Extract AI response
ai_response = response["output"]["message"]["content"][0]["text"]
print("AI response:", ai_response)

# Print full response
print("\nFull response:", json.dumps(response, indent=2, ensure_ascii=False))
