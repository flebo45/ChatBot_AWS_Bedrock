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

# Example usage
if __name__ == "__main__":    
  # Define system and user messages
  message = "Questo è il mio numero di telefono: +393332221110."

  response = client.apply_guardrail(
  guardrailIdentifier='bz9vanuflnf5',
  guardrailVersion='1',
  source='OUTPUT', #'INPUT'|'OUTPUT'
  content=[
      {
          'text': {
              'text': message,
              'qualifiers': [
                  'grounding_source','query','guard_content',
              ]
          }
      },
  ],
  outputScope='FULL' # 'INTERVENTIONS'|'FULL'
  )
 
  print(json.dumps(response, indent=2, ensure_ascii=False))