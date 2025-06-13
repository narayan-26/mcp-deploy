import os
import boto3
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import json
import time
import uuid

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS CloudWatch client
cloudwatch_logs = boto3.client('logs')

class LogEvent(BaseModel):
    timestamp: int
    message: str

class MCPMessage(BaseModel):
    role: str
    content: str

class MCPRequest(BaseModel):
    messages: List[MCPMessage]
    model: str = "claude-3-opus-20240229"
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class MCPResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@app.get('/')
def read_root():
    return {'message': 'Hello, MCP Deploy!'}

@app.post('/v1/chat/completions')
async def mcp_chat(request: MCPRequest):
    try:
        # Generate a unique ID for this response
        response_id = f"chatcmpl-{uuid.uuid4().hex}"
        current_time = int(time.time())
        
        # Create the response in the exact format Claude Desktop expects
        response = {
            "id": response_id,
            "object": "chat.completion",
            "created": current_time,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a test response from MCP server"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/v1/models')
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "claude-3-opus-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic",
                "permission": [
                    {
                        "id": f"modelperm-{uuid.uuid4().hex}",
                        "object": "model_permission",
                        "created": 1677610602,
                        "allow_create_engine": True,
                        "allow_sampling": True,
                        "allow_logprobs": True,
                        "allow_search_indices": True,
                        "allow_view": True,
                        "allow_fine_tuning": True,
                        "organization": "*",
                        "group": None,
                        "is_blocking": False
                    }
                ],
                "root": "claude-3-opus-20240229",
                "parent": None
            }
        ]
    }

@app.get('/health')
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mcp": {
            "enabled": True,
            "version": "1.0.0",
            "endpoints": {
                "chat": "/v1/chat/completions",
                "models": "/v1/models"
            }
        }
    }

@app.get('/mcp/status')
async def mcp_status():
    return {
        "status": "running",
        "version": "1.0.0",
        "endpoints": ["/mcp/chat", "/mcp/status"]
    }

@app.get('/log-groups')
def list_log_groups():
    try:
        response = cloudwatch_logs.describe_log_groups()
        return {'log_groups': response.get('logGroups', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/log-events/{log_group_name}')
def get_log_events(log_group_name: str, limit: Optional[int] = 10):
    try:
        response = cloudwatch_logs.get_log_events(
            logGroupName=log_group_name,
            limit=limit
        )
        return {'log_events': response.get('events', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
