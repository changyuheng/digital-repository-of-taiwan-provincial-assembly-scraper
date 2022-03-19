import enum
import importlib.metadata


VERSION: str = importlib.metadata.version("drtpa_scraper")

class OutputFormat(enum.Enum):
    CSV: str = "csv"
    JSON: str = "json"
