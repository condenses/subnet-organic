<br /><br />
<div align="center">
  <h1 align="center">condenses-organic</h1>
  </div>

> Organic serving for text compression. Powered by Bittensor.

## Installation

```bash
pip install git+https://github.com/condenses/subnet-organic.git
```

## Serving (for validators)

### Prerequisites
- TAOSTATS API key from [https://dash.taostats.io/api-keys](https://dash.taostats.io/api-keys)
- Running validator with NODE_MANAGING_BASE_URL
- Generate a random API key for server authentication

### Environment Setup

```bash
export TAOSTATS_API_KEY=your_api_key_here
export NODE_MANAGING__BASE_URL=http://localhost:9101
export WALLET_NAME=default
export WALLET_HOTKEY=default
export WALLET_PATH=~/.bittensor/wallets
export API_KEY=your_api_key_here
```

### Starting the Server

Standard start:
```bash
python -m uvicorn condenses_organic.server:app --host 0.0.0.0 --port 8080
```

Using PM2 for persistence:
```bash
pm2 start "python -m uvicorn condenses_organic.server:app --host 0.0.0.0 --port 8080" --name "condenses-organic"
```

## API Usage

### Text Compression

Compress a single text string:

```bash
curl -X POST "http://localhost:8080/api/compress/text" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_api_key_here" \
     -d '{
           "text": "This is a longer piece of text that I would like to compress using the API.",
           "top_node_performance": 0.1
         }'
```

#### Parameters:
- `text`: The text to compress
- `top_node_performance`: Fraction of top-performing nodes to consider (0.1 = top 10%)

#### Response:
```json
{
  "compressed_text": "Text to compress using API."
}
```

### Conversation Compression

Compress messages in a conversation:

```bash
curl -X POST "http://localhost:8080/api/compress/messages" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_api_key_here" \
     -d '{
           "messages": [
             {"role": "system", "content": "You are a helpful assistant."},
             {"role": "user", "content": "Can you explain how text compression works?"},
             {"role": "assistant", "content": "Text compression works by identifying and eliminating redundancies in data. Common techniques include removing repetitive patterns, using shorter codes for frequent characters, and employing algorithms like Huffman coding or LZ77. These methods reduce file size while preserving essential information for later decompression."}
           ],
           "compress_user": true,
           "compress_assistant": true,
           "top_node_performance": 0.1
         }'
```

#### Parameters:
- `messages`: Array of message objects, each with `role` and `content` fields
- `compress_user`: Whether to compress messages with "user" role (default: true)
- `compress_assistant`: Whether to compress messages with "assistant" role (default: true)
- `top_node_performance`: Fraction of top-performing nodes to consider (0.1 = top 10%)

#### Response:
```json
{
  "compressed_messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain text compression?"},
    {"role": "assistant", "content": "Text compression removes redundancies using methods like Huffman coding and LZ77 to reduce size while preserving key information."}
  ]
}
```
