"""Scrapers reutilizables: clientes HTTP, Serper, helpers."""

from ivan_core.scrapers.http_client import PoliteHTTPClient
from ivan_core.scrapers.serper import SerperBudgetExceeded, SerperClient, parse_organic_results

__all__ = ["PoliteHTTPClient", "SerperBudgetExceeded", "SerperClient", "parse_organic_results"]
