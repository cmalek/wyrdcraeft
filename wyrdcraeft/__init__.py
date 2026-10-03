from .db.base import Base
from .models import TextMetadata
from .services.ingest import DocumentIngestor
from .settings import Settings

__version__ = "1.2.0"

__all__ = [
    "Base",
    "DocumentIngestor",
    "Settings",
    "TextMetadata",
    "__version__",
]
