import typer

app = typer.Typer()


@app.command()
def list_all():
    """List all tasks."""
    pass
