# Validator Application & CLI - Neural Condense Subnet (NCS)

This repository contains the **Validator Application** along with a CLI tool, **ncs-cli**, for interacting with the application. The validator app is built with FastAPI and can be deployed using Docker and Docker Compose, while the `ncs-cli` tool provides a convenient command-line interface for registering and making organic requests.

This application allows validators to register and sell their miner bandwidth.
To join, validators have to opt in some parameters when launch their subnet validating process at https://github.com/condenses/neural-condense-subnet.
- `--validator.gate_port`: an opened port
- `--validator.organic_client_url`: url of this app deployment

![validator-app-white](https://github.com/user-attachments/assets/7ce80213-4ddd-4bf0-8b18-4df3715051f8)


---

## Table of Contents

1. [Guide to Spin Up the Validator App](#guide-to-spin-up-the-validator-app)
2. [Guide to Interact Using `ncs-cli`](#guide-to-interact-using-ncs-cli)

---

## Guide to Spin Up the Validator App

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup Instructions

1. **Clone the Repository**

   If you haven’t already, clone this repository to your local machine:

   ```bash
   git clone https://github.com/condenses/subnet-organic
   cd subnet_organic
   ```


1. **Navigate to the `proxy_server` directory:**

   ```bash
   cd proxy_server
   ```

2. **Set Environment Variables**

   Update the `docker-compose.yml` file located in `proxy_server/` to set the required environment variables.

   - Ensure you set a valid value for `ADMIN_API_KEY` to secure the `/api/user-register` endpoint.
   
   Example configuration:

   ```yaml
   environment:
     NETUID: "52"
     MONGOHOST: "mongodb"
     MONGOPORT: "27017"
     MONGOUSER: "root"
     MONGOPASSWORD: "example"
     SUBTENSOR_NETWORK: "finney"
     ADMIN_API_KEY: "your_admin_api_key_here"
   ```

3. **Build and Start the Containers**

   Run the following command to build and start the containers for both the FastAPI application and MongoDB:

   ```bash
   docker-compose up --build
   ```

   - This command will:
     - Build the Docker image for the FastAPI Validator application.
     - Start both the FastAPI application and MongoDB services.

4. **Access the Application**

   The Validator app will be accessible at `http://localhost:8000`.

5. **Stop the Containers**

   To stop the containers, press `Ctrl+C` in the terminal where Docker Compose is running.

   Alternatively, you can stop the containers with:

   ```bash
   docker-compose down
   ```

### API Documentation

#### Overview

The Organic API provides an endpoint to submit a request with specific parameters to process and return compressed tokens. This includes the ability to select a model, incentive tier, and miner options to optimize the processing of a given context. The `/api/organic` endpoint returns compressed tokens in base64 format.

#### Register a User API Key

**Endpoint:** `POST /api/user-register`  
**Headers:**  
  - `admin-api-key`: The admin API key (defined in `docker-compose.yml`)

**Request Body Parameters:**

| Parameter  | Type   | Description                    |
|------------|--------|--------------------------------|
| `api_key`  | string | User's API key for registration|

**Example using `curl`:**

```bash
curl -X POST "http://localhost:8000/api/user-register" \
     -H "Content-Type: application/json" \
     -H "admin-api-key: your_admin_api_key_here" \
     -d '{"api_key": "user_api_key_here"}'
```

#### Organic Request

**Endpoint:** `POST /api/organic`  
**Headers:**  
  - `user-api-key`: User's API key (as registered above)

**Request Body Parameters:**

| Parameter         | Type    | Description                                                                                                 |
|-------------------|---------|-------------------------------------------------------------------------------------------------------------|
| `context`         | string  | Text context to be compressed                                                                              |
| `tier`            | string  | Processing tier; available options: `research`, `inference_0`, `inference_1`                               |
| `target_model`    | string  | ID of the language model to use for processing (e.g., `mistralai/Mistral-7B-Instruct-v0.2`)                |
| `miner_uid`       | integer | Specify a miner UID, or -1 to pick randomly                                                                 |
| `top_incentive`   | float   | Specifies a percentile threshold (e.g., `0.9` for the top 90%) to pick miners with incentive              |

**Response:**  
On a successful request, the endpoint will return a JSON response containing the compressed tokens in base64 format. Then you have to decode the base64 string to get the compressed tokens. It has shape `(num_tokens, hidden_size)`.

```json
{
  "compressed_tokens_b64": "base64_encoded_compressed_tokens"
}
```

**Example using `curl`:**

```bash
curl -X POST "http://localhost:8000/api/organic" \
     -H "Content-Type: application/json" \
     -H "user-api-key: user_api_key_here" \
     -d '{
           "context": "your_context_here",
           "tier": "inference_0",
           "target_model": "mistralai/Mistral-7B-Instruct-v0.2",
           "miner_uid": -1,
           "top_incentive": 0.9
         }'
```

*Alternatively, we provide a CLI tool, `ncs-cli`, to interact with the FastAPI application. Refer to the next section for more details.*

---

## Guide to Interact Using `ncs-cli`

This cli tool is used to interact with the `proxy_server` application. The tool provides commands to register a user API key and send organic requests to the FastAPI application.

### Prerequisites

- [Python 3.9+](We recommend to use [miniconda](https://docs.anaconda.com/miniconda/index.html#quick-command-line-install))

### Installation

1. **Clone the Repository**

   If you haven’t already, clone this repository to your local machine:

   ```bash
   git clone https://github.com/condenses/subnet-organic
   cd subnet-organic
   ```

2. **Install the `ncs-cli` Package**

   Navigate to the root of the project directory and install the CLI package:

   ```bash
   pip install .
   ```

   - This will install the `ncs-cli` tool as a global command, allowing you to run it from any directory.

3. **Usage**

   After installation, you can use `ncs-cli` with the following commands:

   #### See Available Commands
   ```bash
   ncs-cli --help
   ```

   #### Register a User API Key

   To register a new user API key, use the `register-user` command:

   ```bash
   ncs-cli register-user
   ```

   - You will be prompted to enter:
     - **api_key**: The new user API key you wish to register.
     - **admin_api_key**: The admin API key for authentication.

   Example:

   ```bash
   $ ncs-cli register-user
   Enter the value for api-key: [Hidden]
   Enter the value for admin-api-key: [Hidden]
   User API key registered successfully.
   ```

   #### Send an Organic Request

   To send an organic request, use the `organic-request` command:

   ```bash
   ncs-cli organic-request
   ```

   - You will be prompted to enter:
     - **api_key**: Your registered user API key.
     - **context**: The context for the organic request.

   Example:

   ```bash
   $ ncs-cli organic-request
   Enter the value for api-key: [Hidden]
   Enter the value for context: Hello, world!
   Enter the value for output_file: compressed_tokens.json
   Response received:
    {
      "compressed_tokens_b64": "base64_encoded_compressed_tokens"
    }
   ```

4. **Environment Variable for API URL (Optional)**

   By default, the CLI points to `http://localhost:8000`. If your API runs on a different URL or port, set the `API_URL` environment variable:

   ```bash
   export API_URL="http://your_api_host:your_api_port"
   ```

### Uninstalling the `ncs-cli`

To uninstall the CLI tool, run:

```bash
pip uninstall ncs-cli
```

---

## Additional Notes

- Ensure that the MongoDB data persists between container restarts by using the Docker volume defined in `docker-compose.yml`.
- Make sure your FastAPI application files, including `app.py`, are in the correct directory structure so Docker can build and run the application.

---
