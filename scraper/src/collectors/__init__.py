"""UAP Data Collectors Package.

Contains modular collectors for each UAP data source.
"""

from .base import BaseCollector
from .nuforc_collector import NUFORCCollector
from .kaggle_collector import KaggleCollector
from .mufon_collector import MUFONCollector
from .nasa_collector import NASACollector
from .huggingface_collector import HuggingFaceCollector
from .ufostalker_collector import UFOStalkerCollector

__all__ = [
    'BaseCollector',
    'NUFORCCollector',
    'KaggleCollector',
    'MUFONCollector',
    'NASACollector',
    'HuggingFaceCollector',
    'UFOStalkerCollector',
]
