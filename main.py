import typer
import uvicorn
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from dotenv import set_key, load_dotenv
from auth import app as fastapi_app
from spotify_client import get_spotify_user_name

ENV_FILE = ".env"

console = Console()
cli = typer.Typer(rich_markup_mode="rich")


def set_env():
    console.print("\n[bold]Please Enter This Credentials[/bold]")

    client_id = typer.prompt("Enter SPOTIFY_CLIENT_ID")
    client_secret = typer.prompt("Enter SPOTIFY_CLIENT_SECRET")
    gemini_key = typer.prompt("Enter GEMINI_API_KEY")

    set_key(ENV_FILE, "SPOTIFY_CLIENT_ID", client_id, quote_mode="never")
    set_key(ENV_FILE, "SPOTIFY_CLIENT_SECRET", client_secret, quote_mode="never")
    set_key(ENV_FILE, "GEMINI_API_KEY", gemini_key, quote_mode="never")

    load_dotenv(ENV_FILE)

    console.print("[green]✓ Credentials saved to .env and loaded![/green]")


def print_big_banner():
    title = Text()
    title.append("⚡ Playlist ", style="bold cyan")
    title.append("Pulse ⚡", style="bold magenta")

    console.print(
        Panel(
            title,
            box=box.DOUBLE,
            border_style="bright_blue",
            padding=(1, 5),
            expand=False,
        )
    )

def login_link(port: int = 8888, host: str = "127.0.0.1"):
    console.print(
        Panel(
            f"🚀 [bold]Starting Spotify Connector[/bold]\n"
            f"Click On This URL 👉: [cyan]http://{host}:{port}/login[/cyan]",
            expand=True,
            border_style="green",
        )
    )


@cli.command()
def start(port: int = 8888, host: str = "127.0.0.1"):
    """
    [bold green]Start[/bold green] the Spotify Auth Server.
    """
    console.clear()
    print_big_banner()
    set_env()
    console.clear()
    print_big_banner()
    login_link(port, host)

    if not os.getenv("SPOTIFY_CLIENT_ID"):
        console.print("[bold red]Error:[/bold red] SPOTIFY_CLIENT_ID is missing!")
        raise typer.Exit(code=1)

    uvicorn.run(fastapi_app, host=host, port=port, log_level="error", access_log=False)


if __name__ == "__main__":
    cli()
