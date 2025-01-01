# Claude 3.5 Vertex AI Bridge

A FastAPI server that provides an OpenAI-compatible API interface for Claude 3.5 on Google Cloud Vertex AI. This bridge allows you to use Claude 3.5 with any OpenAI-compatible client library while leveraging Google Cloud's infrastructure.

## Features

- OpenAI-compatible API endpoint
- Support for streaming responses
- Image analysis capabilities (PNG, JPEG, GIF, WebP)
- Automatic Google Cloud authentication
- Configurable model parameters (temperature, top_p, max_tokens)
- Proper error handling and logging

## Prerequisites

- Python 3.8+
- Google Cloud account with Vertex AI API enabled
- Service account with Vertex AI permissions
- gcloud CLI installed and configured

## Installation

1. Clone the repository:
```bash
git clone https://github.com/xexefe121/claude-vertex-bridge.git
cd claude-vertex-bridge
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and update it with your settings:
```bash
cp .env.example .env
```

5. Update the .env file with your Google Cloud settings:
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east5
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
VERTEX_AI_ENDPOINT=https://us-east5-aiplatform.googleapis.com/v1/projects/your-project-id/locations/us-east5/publishers/anthropic/models/claude-3-5-sonnet-v2@20241022:streamRawPredict
```

## Usage

1. Start the server:
```bash
python main.py
```

2. Make requests to the API:

```bash
# Basic completion request
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "claude-3-5-sonnet-v2",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}'

# Streaming request
curl -N -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "claude-3-5-sonnet-v2",
  "messages": [
    {
      "role": "user",
      "content": "Tell me a story"
    }
  ],
  "stream": true
}'

# Image analysis request
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "claude-3-5-sonnet-v2",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": "base64_encoded_image_data"
          }
        },
        {
          "type": "text",
          "text": "What's in this image?"
        }
      ]
    }
  ]
}'
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GOOGLE_CLOUD_PROJECT | Your Google Cloud project ID | Yes |
| GOOGLE_CLOUD_LOCATION | Region for Vertex AI (e.g., us-east5) | Yes |
| GOOGLE_APPLICATION_CREDENTIALS | Path to service account key file | Yes |
| VERTEX_AI_ENDPOINT | Full Vertex AI endpoint URL | Yes |
| PORT | Server port (default: 8000) | No |
| HOST | Server host (default: 0.0.0.0) | No |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
