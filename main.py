from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from google.cloud import aiplatform
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any, Literal
import asyncio
import base64
import httpx
import json
import os
import time

# Data Models
class ImageSource(BaseModel):
    type: Literal["base64"]
    media_type: Literal["image/png", "image/jpeg", "image/gif", "image/webp"]
    data: str

class ContentItem(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    source: Optional[ImageSource] = None

class Message(BaseModel):
    role: str
    content: Union[str, List[ContentItem]]

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    anthropic_version: str = "vertex-2023-10-16"

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str = "stop"  # Default value to handle None cases

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

app = FastAPI(title="OpenAI to Vertex AI Bridge")

def transform_request(request: ChatCompletionRequest) -> Dict[str, Any]:
    """Transform request to Claude 3.5 Vertex AI format."""
    transformed_messages = []
    
    for msg in request.messages:
        if isinstance(msg.content, str):
            # Convert string content to proper format
            transformed_messages.append({
                "role": msg.role,
                "content": [{"type": "text", "text": msg.content}]
            })
        else:
            # Content is already in proper format (list of ContentItems)
            transformed_messages.append({
                "role": msg.role,
                "content": msg.content
            })
    
    request_data = {
        "anthropic_version": request.anthropic_version,
        "messages": transformed_messages,
        "max_tokens": request.max_tokens,
        "stream": request.stream
    }
    
    # Only include optional parameters if they're different from defaults
    if request.temperature != 1.0:
        request_data["temperature"] = request.temperature
    if request.top_p != 1.0:
        request_data["top_p"] = request.top_p
        
    return request_data

def transform_response(response_data: Dict[str, Any]) -> ChatCompletionResponse:
    """Transform Claude 3.5 response format to OpenAI format."""
    return ChatCompletionResponse(
        id=f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model="claude-3-5-sonnet-v2",
        choices=[
            Choice(
                index=0,
                message=Message(
                    role="assistant",
                    content=response_data.get("content", [{"type": "text", "text": ""}])[0].get("text", "")
                ),
                finish_reason=response_data.get("stop_reason", "stop")
            )
        ],
        usage=Usage(
            prompt_tokens=response_data.get("usage", {}).get("input_tokens", 0),
            completion_tokens=response_data.get("usage", {}).get("output_tokens", 0),
            total_tokens=response_data.get("usage", {}).get("total_tokens", 0)
        )
    )

@app.on_event("startup")
async def startup_event():
    """Validate environment configuration on startup."""
    required_env_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "VERTEX_AI_ENDPOINT"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """Handle chat completion requests."""
    try:
        # Log incoming request
        print(f"Incoming request: {request.dict()}")
        
        # Transform request to Claude 3.5 format
        claude_request = transform_request(request)
        print(f"Transformed request: {claude_request}")
        
        # Get authentication token
        auth_token = os.popen("gcloud auth print-access-token").read().strip()
        if not auth_token:
            raise HTTPException(
                status_code=500,
                detail="Failed to get authentication token"
            )
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        endpoint_url = os.getenv("VERTEX_AI_ENDPOINT")
        
        async def stream_response():
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    endpoint_url,
                    json=claude_request,
                    headers=headers
                ) as response:
                    print(f"Response status: {response.status_code}")
                    if response.status_code != 200:
                        error_content = await response.aread()
                        print(f"Error response: {error_content}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Vertex AI Error: {error_content.decode()}"
                        )
                    
                    if request.stream:
                        current_content = ""
                        async for line in response.aiter_lines():
                            if line and line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if data["type"] == "content_block_delta":
                                        if "delta" in data and data["delta"]["type"] == "text_delta":
                                            delta = data["delta"]["text"]
                                            current_content += delta
                                            transformed_data = transform_response({
                                                "content": [{"type": "text", "text": current_content}],
                                                "stop_reason": "stop",  # Use default value for intermediate chunks
                                                "usage": {"output_tokens": len(current_content.split())}
                                            })
                                            yield f"data: {json.dumps(transformed_data.dict())}\n\n"
                                    elif data["type"] == "message_delta" and "stop_reason" in data.get("delta", {}):
                                        transformed_data = transform_response({
                                            "content": [{"type": "text", "text": current_content}],
                                            "stop_reason": data["delta"]["stop_reason"],
                                            "usage": data.get("usage", {})
                                        })
                                        yield f"data: {json.dumps(transformed_data.dict())}\n\n"
                                        yield "data: [DONE]\n\n"
                                except json.JSONDecodeError:
                                    if line.strip() != "data: [DONE]":
                                        continue
                    else:
                        content = await response.aread()
                        print(f"Response content: {content.decode()}")
                        response_data = json.loads(content)
                        transformed_data = transform_response(response_data)
                        yield json.dumps(transformed_data.dict())
        
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream" if request.stream else "application/json"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
