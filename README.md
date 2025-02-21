<br /><br />
<div align="center">
  <h1 align="center">condenses-organic</h1>
  <h4 align="center"> Organic serving for text compression. Powered by Bittensor.</div>

## Installation

```bash
pip install git+https://github.com/condenses/subnet-organic.git
```

## Serving (for validators)

*Get the environment variables from your validating environment.*

```bash
export RESTFUL_BITTENSOR__BASE_URL=http://localhost:9103
export NODE_MANAGING__BASE_URL=http://localhost:9101
export WALLET_NAME=default
export WALLET_HOTKEY=default
export WALLET_PATH=~/.bittensor/wallets
```

```bash
python -m gunicorn condenses_organic.server:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

## Usage (for compressing text)

```bash
curl -X POST "http://localhost:8000/api/compress/text" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "This is a longer piece of text that I would like to compress using the API. It contains multiple sentences and provides more context for the compression process.",
           "top_node_performance": 0.1
         }'
```

- `text`: The text to compress.
- `top_node_performance`: The performance of the top node to use for compression.



