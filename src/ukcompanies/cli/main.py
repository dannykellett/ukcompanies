"""CLI entry point for ukcompanies package."""

import asyncio
import sys

import click
import structlog

from ukcompanies import AsyncClient

logger = structlog.get_logger()


@click.group()
@click.option("--api-key", envvar="COMPANIES_HOUSE_API_KEY", help="Companies House API key")
@click.option(
    "--base-url",
    default="https://api.company-information.service.gov.uk",
    help="API base URL"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, api_key: str | None, base_url: str, verbose: bool) -> None:
    """UK Companies House API CLI."""
    if verbose:
        structlog.configure(
            wrapper_class=structlog.dev.ConsoleRenderer,
            log_level="DEBUG"
        )

    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    ctx.obj["base_url"] = base_url


@cli.command()
@click.argument("term")
@click.option("--limit", default=20, help="Maximum number of results")
@click.pass_context
def search(ctx: click.Context, term: str, limit: int) -> None:
    """Search for companies by name."""
    asyncio.run(_search_companies(ctx.obj["api_key"], ctx.obj["base_url"], term, limit))


async def _search_companies(api_key: str | None, base_url: str, term: str, limit: int) -> None:
    """Async implementation of company search."""
    if not api_key:
        click.echo(
            "Error: API key required. Set COMPANIES_HOUSE_API_KEY environment variable "
            "or use --api-key",
            err=True
        )
        sys.exit(1)

    try:
        async with AsyncClient(api_key=api_key, base_url=base_url) as client:
            results = await client.search_companies(term)

            for i, company in enumerate(results.items[:limit]):
                click.echo(f"{i+1}. {company.title} ({company.company_number})")
                if company.address:
                    click.echo(
                        f"   {company.address.address_line_1}, {company.address.postal_code}"
                    )
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
