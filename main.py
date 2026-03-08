# Imports
try:
    import typer
    from rich import print
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.table import Table
except Exception as e:
    print(f"Error Importing libraries: {e}")

console = Console()

app = typer.Typer()  # create new type app


@app.command()  # Command with the app
def main(name: str = "ido"):
    name = Prompt.ask(
        "Enter your name",
        choices=["Paul", "Jessica", "Duncan"],
        default="Paul",
        case_sensitive=False,
    )
    print(
        f"[bold red]Alert![/bold red] [green]Portal gun[/green] shooting! {name} :boom:"
    )
    print(Panel("Hello, [red]World!", title="Welcome", subtitle="Thank you"))
    table = Table("Name", "Item")
    table.add_row("Rick", "Portal Gun")
    table.add_row("Morty", "Plumbus")
    console.print(table)


if __name__ == "__main__":
    app()
