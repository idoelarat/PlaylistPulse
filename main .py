import typer

def main(firstname: str, lastname: str):
    print(f"Hello {firstname} {lastname}")

if __name__ == "__main__":
    typer.run(main)