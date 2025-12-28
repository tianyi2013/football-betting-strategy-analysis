# python
import typer

app = typer.Typer()

@app.command()
def greet(
        name: str = typer.Option(..., help="Name to greet"),
        times: int = typer.Option(1, help="How many times to print the greeting"),
):
    for _ in range(times):
        typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
