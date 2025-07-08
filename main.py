from flask import Flask, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send
import boto3
import logging
import json
import os
from Bot import Bot

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# insert credentials here
os.environ['AWS_ACCESS_KEY_ID'] = ""
os.environ['AWS_SECRET_ACCESS_KEY'] = ""
os.environ['AWS_SESSION_TOKEN'] = ""
# or in ~/.aws/credentials file with format:
# [default]
# aws_access_key_id = YOUR_ACCESS_KEY
# aws_secret_access_key = YOUR_SECRET   
# aws_session_token = YOUR_SESSION_TOKEN

# Create a Bedrock client
client = boto3.client('bedrock-runtime', region_name='eu-central-1')  # Change region if needed

"""
Bot Initialization
"""
# Define model system message
system_message = "You are an helpfull assistant."

# Define model name and whether to use streaming
# eu.amazon.nova-lite-v1:0
# eu.amazon.nova-micro-v1:0
model_id = "eu.amazon.nova-lite-v1:0"  # Replace with actual model name
streaming = True  # Set to True to enable streaming


bot = Bot(client, logger, model_id)


app = Flask(__name__)
app.config["SECRET_KEY"] = "alsldkjfjc"
socketio = SocketIO(app)

@app.route("/", methods=["GET", "POST"])
def home():
    print(bot.getRag())
    return render_template("home.html", rag_status = bot.getRag(), guardrails_status = bot.getGuardrails())

@socketio.on("clear")
def clear(data):
    if data.get("clear"):
        bot.clearMessages()
        print(bot.getMessagesNumber())

@socketio.on("message")
def message(data): 
    response = bot.call_converse_api(system_message, data["data"], streaming)
    msg_id = bot.getMessagesNumber()
    if not streaming:
        start_message = {
            "start": True,
            "msg_id": msg_id
        }
        
        content = {
            "stream": response["output"]["message"]["content"][0]["text"],
            "msg_id": msg_id
        }
        
        end_message = {
            "start": False,
            "msg_id": msg_id
        }
        
        send(start_message)
        send(content)
        send(end_message)
        # Log token usage.
        token_usage = response['usage']
        print('\n\n###########################################\n\n')
        logger.info("Input tokens: %s", token_usage['inputTokens'])
        logger.info("Output tokens: %s", token_usage['outputTokens'])
        logger.info("Total tokens: %s", token_usage['totalTokens'])
        logger.info("Stop reason: %s", response['stopReason'])
        
        if token_usage['inputTokens'] >= (bot.getMaxInputtoken() / 100 * 80):
            bot.summary(system_message)
    
    else:
        for event in response:

            if 'messageStart' in event:
                start_message = {
                    "start": True,
                    "msg_id": msg_id
                }
                send(start_message)
                print(f"\nRole: {event['messageStart']['role']}")

            if 'contentBlockDelta' in event:
                content = {
                    "stream": event['contentBlockDelta']['delta']['text'],
                    "msg_id": msg_id
                }
                send(content)
                print(event['contentBlockDelta']['delta']['text'], end="")

            if 'messageStop' in event:
                end_message = {
                    "start": False,
                    "msg_id": msg_id
                }
                send(end_message)
                print(f"\nStop reason: {event['messageStop']['stopReason']}")

            if 'metadata' in event:
                metadata = event['metadata']
                if 'usage' in metadata:
                    print("\nToken usage")
                    print(f"Input tokens: {metadata['usage']['inputTokens']}")
                    print(f":Output tokens: {metadata['usage']['outputTokens']}")
                    print(f":Total tokens: {metadata['usage']['totalTokens']}")
                    
                    # If the Input token is gretaher than the 80% of the max input token then we nedd to summarize
                    if metadata['usage']['inputTokens'] >= (bot.getMaxInputtoken() / 100 * 80):
                        bot.summary(system_message)
                        
                if 'metrics' in event['metadata']:
                    print(
                        f"Latency: {metadata['metrics']['latencyMs']} milliseconds")

@socketio.on("model_selected")
def model_selected(data):    
    if(data["model"] == "nova-micro"):
        bot.setModel("nova-micro")
    elif(data["model"] == "nova-lite"):
        bot.setModel("nova-lite")
    else:
        bot.setModel("nova-lite")
    print(bot.getModel())
    
@socketio.on("switch_status")
def switch_status(data):
    print(f"{data}")
    if data["type"] == "guardrails_status":
        bot.setGuardrails(data["status"])

    elif data["type"] == "rag_status":
        bot.setRag(data["status"])

if __name__ == '__main__':
    app.run(debug=True)