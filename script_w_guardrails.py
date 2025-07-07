import boto3
import logging
import json
import os

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# insert credentials here
os.environ['AWS_ACCESS_KEY_ID'] = ""
os.environ['AWS_SECRET_ACCESS_KEY'] = ""
#os.environ['AWS_SESSION_TOKEN'] = ""
# or in ~/.aws/credentials file with format:
# [default]
# aws_access_key_id = YOUR_ACCESS_KEY
# aws_secret_access_key = YOUR_SECRET   
# aws_session_token = YOUR_SESSION_TOKEN

# Create a Bedrock client
client = boto3.client('bedrock-runtime', region_name='eu-central-1')  # Change region if needed

# Function to call Converse API
def call_converse_api(system_message, user_message, model_id, streaming=False):
    """
    Calls the AWS Bedrock Converse API.
    
    Parameters:
    - system_message: The initial system message
    - user_message: The user's input message
    - model_id: The name of the model to use
    - streaming: Boolean indicating if streaming mode is on/off
    
    Returns:
    - The response from the API
    """

    # Inference parameters to use.
    temperature = 0.5
    maxTokens = 1000
    topP = 0.9
    top_k = 20

    # Base inference parameters to use.
    inference_config = {
      "temperature": temperature,
      "maxTokens": maxTokens,
      "topP": topP,
    }
    # Additional inference parameters to use.
    additional_model_fields = {
      "inferenceConfig": {
        "topK": top_k
      }
    }
    
    # Setup the system prompts and messages to send to the model.
    system_prompts = [{"text": system_message}]
    message = {
        "role": "user",
        "content": [{"text": user_message}]
    }
    messages = [message]
    
    if not streaming:

      guardrail_config = {
          "guardrailIdentifier": "bz9vanuflnf5",
          "guardrailVersion": "1",
          "trace": "enabled"
      }  

      # Call the Converse API
      response = client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
        guardrailConfig=guardrail_config
      )

      logger.info(f"Response from Converse API:\n{json.dumps(response, indent=2)}")
      print('\n\n###########################################\n\n')
      logger.info(f'Response Content Text:\n{response["output"]["message"]["content"][0]["text"]}')

      # Log token usage.
      token_usage = response['usage']
      print('\n\n###########################################\n\n')
      logger.info("Input tokens: %s", token_usage['inputTokens'])
      logger.info("Output tokens: %s", token_usage['outputTokens'])
      logger.info("Total tokens: %s", token_usage['totalTokens'])
      logger.info("Stop reason: %s", response['stopReason'])
    else:

      guardrail_config = {
          "guardrailIdentifier": "bz9vanuflnf5",
          "guardrailVersion": "1",
          "trace": "enabled",
          "streamProcessingMode": "sync"
      }  

      response = client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
        guardrailConfig=guardrail_config
      )
      stream = response.get('stream')
      if stream:
          for event in stream:

              if 'messageStart' in event:
                  print(f"\nRole: {event['messageStart']['role']}")

              if 'contentBlockDelta' in event:
                  print(event['contentBlockDelta']['delta']['text'], end="")

              if 'messageStop' in event:
                  print(f"\nStop reason: {event['messageStop']['stopReason']}")

              if 'metadata' in event:
                  metadata = event['metadata']
                  if 'usage' in metadata:
                      print("\nToken usage")
                      print(f"Input tokens: {metadata['usage']['inputTokens']}")
                      print(
                          f":Output tokens: {metadata['usage']['outputTokens']}")
                      print(f":Total tokens: {metadata['usage']['totalTokens']}")
                  if 'metrics' in event['metadata']:
                      print(
                          f"Latency: {metadata['metrics']['latencyMs']} milliseconds")

# Example usage
if __name__ == "__main__":
    # Define system and user messages
    system_message = "Rispondi in modo quanto più dettagliato possibile."
    user_message = "Questo è il mio numero di telefono: +393332221110"
    
    # Define model name and whether to use streaming
    # eu.amazon.nova-lite-v1:0
    # eu.amazon.nova-micro-v1:0
    model_id = "eu.amazon.nova-lite-v1:0"  # Replace with actual model name
    streaming = False  # Set to True to enable streaming
    
    # Call the API and print the response
    call_converse_api(system_message, user_message, model_id, streaming)