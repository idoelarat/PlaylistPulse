import typer
import uvicorn
import os
import multiprocessing
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from dotenv import set_key, load_dotenv
from auth import app as fastapi_app
import spotify_client
import gemini_tool

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
            expand=False,
            border_style="green",
        )
    )


def organize_by():
    while True:
        console.print("\n[bold]How To Organize the songs?\n1 - Mood | 2 - Genre[/bold]")
        organize_var = typer.prompt("Please Enter a Number")

        if organize_var in ["1", "2"]:
            return int(organize_var)
        console.print("[red]Invalid choice. Please enter 1 or 2.[/red]")


def fetch_songs():
    with console.status("[bold yellow]Fetching your library...", spinner="arc"):
        songs = spotify_client.all_saved_songs()

    if not isinstance(songs, list):
        console.print(
            "[red]❌ Could not load songs. Please check your connection.[/red]"
        )
        return

    table = Table(
        title="Your Saved Library", show_header=True, header_style="bold magenta"
    )
    table.add_column("ID", style="dim", width=22)
    table.add_column("Song Name", style="cyan")
    table.add_column("Artist", style="white")

    for s in songs[:10]:
        table.add_row(
            str(s.get("id", "N/A")),
            str(s.get("name", "Unknown")),
            str(s.get("artist", "Unknown")),
        )

    console.print(table)

    if len(songs) > 10:
        console.print(f"[italic]... plus [bold]{len(songs) - 10}[/] more tracks.[/]\n")

    return songs


def process_gemini_and_spotify(num: int, songs):
    if num == 1:
        status_msg = "[bold yellow]Organizing By Mood... Please Wait It might take time"
        prompt = gemini_tool.PROMPT_TEMPLATE_MOOD
    else:
        status_msg = "[bold yellow]Organizing By Genre... Please Wait It might take time"
        prompt = gemini_tool.PROMPT_TEMPLATE_GENERE

    with console.status(status_msg, spinner="arc"):
        res = gemini_tool.classify_library(songs, prompt)

        count = len(songs)

        console.print(f"[green]Successfully processed {count} songs![/green]")

    return res


test_songs = [
    {
        "id": "7ouMYWpwJ422jRcDASZB7P",
        "name": "The Fate of Ophelia",
        "artist": "Taylor Swift",
    },
    {"id": "4VqPOruhp5EdPBeR92t6lQ", "name": "I Just Might", "artist": "Bruno Mars"},
    {"id": "2takcwOaAZWiXQijPHIx7B", "name": "Azizam", "artist": "Ed Sheeran"},
    {
        "id": "1dc4c347-a1db-32aa-b14f",
        "name": "Beat Yourself Up",
        "artist": "Charlie Puth",
    },
    {
        "id": "50369905-68ca-48d2-912d",
        "name": "Stateside",
        "artist": "PinkPantheress ft. Zara Larsson",
    },
]


@cli.command()
def start(port: int = 8888, host: str = "127.0.0.1"):
    """
    [bold green]Start[/bold green] the Spotify Auth Server.
    """
    console.clear()
    print_big_banner()

    if typer.confirm("Want to change tokens?", default=False):
        set_env()

    if os.path.exists(".tokens.json"):
        os.remove(".tokens.json")

    proc = multiprocessing.Process(
        target=uvicorn.run,
        args=(fastapi_app,),
        kwargs={"host": host, "port": port, "log_level": "error"},
        daemon=True,
    )
    proc.start()

    console.clear()
    print_big_banner()
    login_link(port, host)
    with console.status(
        "[bold yellow]Waiting for Spotify authentication...", spinner="arc"
    ):
        while not os.path.exists(".tokens.json"):
            time.sleep(0.5)

    console.clear()
    print_big_banner()
    if not os.path.exists(".tokens.json"):
        console.print("[bold red]Credentials are not good[/]")
        exit()
    console.print(
        f"[bold cyan]Logged In To:[/] [bold]{spotify_client.get_spotify_user_name()}[/]"
    )
    console.print(
        f"[bold cyan]Total Saved Songs:[/] [white]{spotify_client.get_total_saved_songs()}[/]"
    )
    songs = fetch_songs()
    gemini_songs = process_gemini_and_spotify(organize_by(), test_songs)
    console.print(gemini_songs) 


if __name__ == "__main__":
    cli()
