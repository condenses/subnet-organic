<br /><br />
<div align="center">
  <h1 align="center">condenses-organic</h1>
  <h4 align="center"> Organic serving for text compression. Powered by Bittensor.</div>


## Installation

```bash
pip install git+https://github.com/condenses/subnet-organic.git
```

## Serving (for validators)

- Get a TAOSTATS API key from https://dash.taostats.io/api-keys
- Get NODE_MANAGING_BASE_URL from a running validator

Set environment variables:

```bash
export TAOSTATS_API_KEY=your_api_key_here
export NODE_MANAGING__BASE_URL=http://localhost:9101
export WALLET_NAME=default
export WALLET_HOTKEY=default
export WALLET_PATH=~/.bittensor/wallets
```

Start the server:

```bash
python -m gunicorn condenses_organic.server:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

## Usage (for compressing text)

```bash
curl -X POST "http://localhost:8080/api/compress/text" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "This is a longer piece of text that I would like to compress using the API.",
           "top_node_performance": 0.1
         }'
```

### Parameters:
- `text`: The text to compress
- `top_node_performance`: Fraction of top-performing nodes to consider (0.1 = top 10%)
