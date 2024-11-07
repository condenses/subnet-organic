import typer
import requests
import os
import json

app = typer.Typer()

# Default API URL (can be overridden with the API_URL environment variable)
API_URL = os.getenv("API_URL", "http://localhost:8000")


@app.command()
def register_user(
    api_key: str = typer.Option(
        ..., prompt=True, hide_input=False, help="The new user API key to register."
    ),
    admin_api_key: str = typer.Option(
        ..., prompt=True, hide_input=False, help="The admin API key for authentication."
    ),
):
    """
    Register a new user API key with the server (requires admin API key).
    """
    url = f"{API_URL}/api/user-register"
    headers = {"admin-api-key": admin_api_key, "Content-Type": "application/json"}
    payload = {"api_key": api_key}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        typer.secho("User API key registered successfully.", fg=typer.colors.GREEN)
    else:
        typer.secho(
            f"Headers: {headers}",
            fg=typer.colors.BLUE,
        )
        typer.secho(
            f"Payload: {payload}",
            fg=typer.colors.BLUE,
        )
        typer.secho(
            f"Error: {response.status_code} - {response.text}", fg=typer.colors.RED
        )


@app.command()
def organic_request(
    api_key: str = typer.Option(
        ..., prompt=True, hide_input=True, help="Your user API key."
    ),
    context: str = typer.Option(
        ..., prompt=True, help="The context for the organic request."
    ),
    output_file: str = typer.Option(
        "response.json", prompt=True, help="The output file for the response."
    ),
):
    """
    Send an organic request to the server using your API key.
    """
    url = f"{API_URL}/api/organic"
    headers = {"user-api-key": api_key, "Content-Type": "application/json"}
    payload = {"context": context}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        typer.secho("Response received:", fg=typer.colors.GREEN)
        with open(output_file, "w") as f:
            json.dump(response.json(), f, indent=4)
        typer.secho(f"Response saved to {output_file}.", fg=typer.colors.GREEN)
    else:
        typer.secho(
            f"Error: {response.status_code} - {response.text}", fg=typer.colors.RED
        )


if __name__ == "__main__":
    app()
