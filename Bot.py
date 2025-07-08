import boto3
import logging
import json
import os

from botocore.exceptions import ClientError

class Bot:
    """Class that implement the interaction with Amazon Nova AI"""
    
    def __init__(self, client, logger, model_id):
        self.messages = [] 
        # Inference parameters to use      
        self.temperature = 0.5
        self.maxTokens = 1000
        self.topP = 0.9
        self.top_k = 20
        self.client = client
        self.logger = logger
        self.model_id = model_id
        self.rag = True
        self.guardrails = True
        if self.model_id == "eu.amazon.nova-lite-v1:0":
            self.maxInputToken = 300000
        elif self.model_id == "eu.amazon.nova-micro-v1:0":
            self.maxInputToken = 128000
            
    def getMessagesNumber(self):
        return len(self.messages)
    
    def getModel(self):
        return self.model_id
    
    def getMaxInputtoken(self):
        return self.maxInputToken
    
    def setModel(self, model_id):
        if model_id == "nova-lite":
            self.model_id = "eu.amazon.nova-lite-v1:0"
            self.maxInputToken = 300000
        elif model_id == "nova-micro":
            self.model_id = "eu.amazon.nova-micro-v1:0"
            self.maxInputToken = 128000
        else:
            self.model_id = "eu.amazon.nova-lite-v1:0"
            self.maxInputToken = 300000
    
    def getRag(self):
        return self.rag
    
    def setRag(self, rag_status):
        if rag_status:
            self.rag = True
        else:
            self.rag = False
            
    def getGuardrails(self):
        return self.guardrails
    
    def setGuardrails(self, guardrails_status):
        if guardrails_status:
            self.guardrails = True
        else:
            self.guardrails = False
        
        
    def call_converse_api(self,system_message, user_message, streaming=False):
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
        # Base inference parameters to use.
        inference_config = {
        "temperature": self.temperature,
        "maxTokens": self.maxTokens,
        "topP": self.topP,
        }
        # Additional inference parameters to use.
        additional_model_fields = {
        "inferenceConfig": {
            "topK": self.top_k
        }
        }
        
        # Setup the system prompts and messages to send to the model.
        system_prompts = [{"text": system_message}]
        message = {
            "role": "user",
            "content": [{"text": user_message}]
        }
        
        self.addMessage(message)
        
        if not streaming:
            if self.guardrails:
                guardrail_config = {
                    "guardrailIdentifier": "bz9vanuflnf5",
                    "guardrailVersion": "1",
                    "trace": "enabled"
                }
                
                # Call the Converse API
                response = self.client.converse(
                    modelId=self.model_id,
                    messages=self.messages,
                    system=system_prompts,
                    inferenceConfig=inference_config,
                    additionalModelRequestFields=additional_model_fields,
                    guardrailConfig=guardrail_config
                )
                
            else:
                # Call the Converse API
                response = self.client.converse(
                    modelId=self.model_id,
                    messages=self.messages,
                    system=system_prompts,
                    inferenceConfig=inference_config,
                    additionalModelRequestFields=additional_model_fields
                )

            return response

        else:
            if self.guardrails:
                guardrail_config = {
                    "guardrailIdentifier": "bz9vanuflnf5",
                    "guardrailVersion": "1",
                    "trace": "enabled",
                    "streamProcessingMode": "sync"
                }
                
                response = self.client.converse_stream(
                    modelId=self.model_id,
                    messages=self.messages,
                    system=system_prompts,
                    inferenceConfig=inference_config,
                    additionalModelRequestFields=additional_model_fields,
                    guardrailConfig=guardrail_config
                )
                
            else:
                response = self.client.converse_stream(
                    modelId=self.model_id,
                    messages=self.messages,
                    system=system_prompts,
                    inferenceConfig=inference_config,
                    additionalModelRequestFields=additional_model_fields
                )
    
            stream = response.get('stream')
            if stream:
                return stream
                
 
    def clearMessages(self):
        self.messages.clear()
        
    def addMessage(self, message):
        self.messages.append(message)
        
    
    # This method is to be called when the input token excede a maximum number of token
    def summary(self, system_message):
        user_message = f"""
        You are an helpfull assistant. 
        Take all the messages between you and the user. Your task is to generate a comprehensive, detailed summary of all the user's inputs throughout the conversation. 
        The summary should: 
        - Clearly outline all key **themes and topics** the user discussed.
        - Highlight any **questions**, **goals**, or **intentions** the user expressed.
        - Preserve relevant **context** and **sequence** of topics to maintain continuity.
        - Be written in a concise and organized form, readable and structured as if it's one coherent message the user could have written.

        Avoid mentioning that this is a summary or referring to the assistant's replies. Focus exclusively on what the user communicated or asked.
        """
        summary_message = self.call_converse_api(system_message, user_message)
        message = {
            "role": "user",
            "content": [{"text": summary_message["output"]["message"]["content"][0]["text"]}]
        }
        self.clearMessages()
        self.addMessage(message)
        
         
        