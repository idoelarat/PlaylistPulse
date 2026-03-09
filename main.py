import typer
import uvicorn
import os
import multiprocessing
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from dotenv import set_key, load_dotenv
from auth import app as fastapi_app
import spotify_client

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

def organize_by():
    console.print("\n[bold]How To Organize the songs?[/bold]")
    orginze_var: int = typer.prompt("Please Enter")

@cli.command()
def start(port: int = 8888, host: str = "127.0.0.1"):
    """
    [bold green]Start[/bold green] the Spotify Auth Server.
    """
    console.clear()
    print_big_banner()

    if not typer.confirm("If The Tokens You add before are ok Press Y"):
        if os.path.exists(".tokens.json"):
            os.remove(".tokens.json")
        set_env()
    
    proc = multiprocessing.Process(
        target=uvicorn.run,
        args=(fastapi_app,),
        kwargs={"host": host, "port": port, "log_level": "error"},
        daemon=True
    )
    proc.start()

    console.clear()
    print_big_banner()
    login_link(port, host)
    if not typer.confirm("Did you get access?"):
        console.clear()
        console.print("[bold red]Exiting CLI... Goodbye![/]")
        exit()
        

    console.clear()
    print_big_banner()
    if not os.path.exists(".tokens.json"):
        console.print("[bold red]Credentials are not good[/]")
        exit()
    console.print(f"[bold cyan]Logged In To:[/] [bold]{spotify_client.get_spotify_user_name()}[/]")
    console.print(f"[bold cyan]Total Saved Songs:[/] [white]{spotify_client.get_total_saved_songs()}[/]")
    organize_by()
    
if __name__ == "__main__":
    cli()
