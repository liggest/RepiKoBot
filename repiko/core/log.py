from __future__ import annotations

from loguru import logger
import sys

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from loguru import Level

logger.remove()
logger.add(sys.stderr,level="INFO",format="<level>{level}</level>: {message}",colorize=True)

def debugOnly(record:dict[str,Level]):
    return record["level"].name == "DEBUG"

logger.add(sys.stderr,level="DEBUG",filter=debugOnly,format="({name}:{line}) <level>{level}</level>: {message}")
