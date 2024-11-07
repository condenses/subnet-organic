import typer
import requests
import os

app = typer.Typer()

# Default API URL (can be overridden with the API_URL environment variable)
API_URL = os.getenv("API_URL", "http://localhost:8000")


@app.command()
def register_user(
    api_key: str = typer.Option(
        ..., prompt=True, hide_input=True, help="The new user API key to register."
    ),
    admin_api_key: str = typer.Option(
        ..., prompt=True, hide_input=True, help="The admin API key for authentication."
    ),
):
    """
    Register a new user API key with the server (requires admin API key).
    """
    url = f"{API_URL}/api/user-register"
    headers = {"admin_api_key": admin_api_key, "Content-Type": "application/json"}
    payload = {"api_key": api_key}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        typer.secho("User API key registered successfully.", fg=typer.colors.GREEN)
    else:
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
):
    """
    Send an organic request to the server using your API key.
    """
    url = f"{API_URL}/api/organic"
    headers = {"user_api_key": api_key, "Content-Type": "application/json"}
    payload = {"context": context}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        typer.secho("Response received:", fg=typer.colors.GREEN)
        typer.echo(response.json())
    else:
        typer.secho(
            f"Error: {response.status_code} - {response.text}", fg=typer.colors.RED
        )


if __name__ == "__main__":
    app()
