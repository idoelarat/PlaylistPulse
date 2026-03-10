import typer
import uvicorn
import os
import sys
import multiprocessing
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from dotenv import set_key, load_dotenv
from auth import app as fastapi_app
import spotify_client

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = str(BASE_DIR / ".env")
TOKEN_FILE = str(BASE_DIR / ".tokens.json")

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


def hard_clear():
    """Wipes the terminal and the scrollback buffer."""
    console.clear()

    if os.name == "nt":  # Windows
        os.system("cls")
    else:  # Mac / Linux
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.flush()


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
        all_songs = spotify_client.all_saved_songs()

    if not isinstance(all_songs, list):
        console.print(
            "[red]❌ Could not load songs. Please check your connection.[/red]"
        )
        return []

    songs = all_songs
    return songs


def select_model():
    """Direct prompt for the Gemini model name."""
    console.print(
        "\n[bold magenta]Which Gemini Model would you like to use?[/bold magenta]"
    )
    console.print(
        "[dim]Common options: gemini-2.0-flash, gemini-2.0-flash-lite-preview-02-05, gemini-1.5-flash[/dim]"
    )

    model_name = typer.prompt("Model Name", default="gemini-2.0-flash")
    return model_name


def process_gemini_and_spotify(num: int, songs, model_name: str):
    import gemini_tool

    prompt = gemini_tool.PROMPT_TEMPLATE_MOOD if num == 1 else gemini_tool.PROMPT_TEMPLATE_GENERE
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task(f"[yellow]AI is analyzing {len(songs)} songs...", total=len(songs))
        
        def update_progress(advance_by=1):
            progress.advance(task, advance_by)

        res = gemini_tool.classify_library(
            songs, 
            prompt, 
            model_name=model_name, 
            progress_callback=update_progress # Pass the function here
        )
    count = len(songs)
    console.print(f"[green]✨ AI successfully processed {count} songs![/green]")

    with console.status(
        "[bold blue]Updating your Spotify Playlists...[/bold blue]", spinner="dots"
    ):
        spotify_client.sync_playlists(res)

    console.print(
        "[bold green]✅ All playlists are synced and up to date![/bold green]"
    )
    return res


@cli.command()
def start(port: int = 8888, host: str = "127.0.0.1"):
    """
    [bold green]Start[/bold green] the Spotify Auth Server.
    """
    hard_clear()
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

    hard_clear()
    print_big_banner()
    login_link(port, host)
    with console.status(
        "[bold yellow]Waiting for Spotify authentication...", spinner="arc"
    ):
        while not os.path.exists(".tokens.json"):
            time.sleep(0.5)

    hard_clear()
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
    org_type = organize_by()
    model_name = select_model()
    process_gemini_and_spotify(org_type, songs, model_name)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
