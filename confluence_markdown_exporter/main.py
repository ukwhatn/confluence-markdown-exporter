import os
from pathlib import Path
from typing import Annotated

import typer

from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.config_interactive import main_config_menu_loop
from confluence_markdown_exporter.utils.measure_time import measure
from confluence_markdown_exporter.utils.type_converter import str_to_bool

DEBUG: bool = str_to_bool(os.getenv("DEBUG", "False"))

app = typer.Typer()


def override_output_path_config(value: Path | None) -> None:
    """Override the default output path if provided."""
    if value is not None:
        set_setting("export.output_path", value)


@app.command(help="Export one or more Confluence pages by ID or URL to Markdown.")
def pages(
    pages: Annotated[list[str], typer.Argument(help="Page ID(s) or URL(s)")],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page

    with measure(f"Export pages {', '.join(pages)}"):
        for page in pages:
            override_output_path_config(output_path)
            _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
            _page.export()


@app.command(help="Export Confluence pages and their descendant pages by ID or URL to Markdown.")
def pages_with_descendants(
    pages: Annotated[list[str], typer.Argument(help="Page ID(s) or URL(s)")],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
    ignore: Annotated[
        str | None,
        typer.Option(
            "--ignore",
            help="Comma-separated page IDs to exclude (ignored pages and their descendants will be skipped).",
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page

    # Parse ignore string into a set of ints
    ignore_set: set[int] | None = None
    if ignore:
        try:
            ignore_set = {
                int(pid.strip())
                for pid in ignore.split(",")
                if pid.strip() and pid.strip().isdigit()
            }
        except ValueError:
            # Non-integer values are ignored silently; Typer help explains IDs only
            ignore_set = {
                int(pid.strip())
                for pid in ignore.split(",")
                if pid.strip().isdigit()
            }

    with measure(f"Export pages {', '.join(pages)} with descendants"):
        for page in pages:
            override_output_path_config(output_path)
            _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
            _page.export_with_descendants(ignore=ignore_set)


@app.command(help="Export all Confluence pages of one or more spaces to Markdown.")
def spaces(
    space_keys: Annotated[list[str], typer.Argument()],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Space

    with measure(f"Export spaces {', '.join(space_keys)}"):
        for space_key in space_keys:
            override_output_path_config(output_path)
            space = Space.from_key(space_key)
            space.export()


@app.command(help="Export all Confluence pages across all spaces to Markdown.")
def all_spaces(
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Organization

    with measure("Export all spaces"):
        override_output_path_config(output_path)
        org = Organization.from_api()
        org.export()


@app.command(help="Open the interactive configuration menu.")
def config(
    jump_to: Annotated[
        str | None, typer.Option(help="Jump directly to a config submenu, e.g. 'auth.confluence'")
    ] = None,
) -> None:
    """Interactive configuration menu."""
    main_config_menu_loop(jump_to)


if __name__ == "__main__":
    app()
