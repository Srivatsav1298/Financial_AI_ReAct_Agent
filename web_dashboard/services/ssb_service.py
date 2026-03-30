"""
SSB Data Service
Manages interactions with Statistics Norway API
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import current_app
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.ssb_api import SSBApi

# Import the global cache instance
try:
    from extensions import cache
except ImportError:
    # In tests, the cache might not be available
    cache = None


class SSBService:
    """Service layer for SSB data operations"""

    def __init__(self, ssb_api: SSBApi):
        self.ssb_api = ssb_api
        self._cache_stats = {'hits': 0, 'misses': 0}

    def get_household_budget_data(self, year: str = "2022", nowcast: bool = True) -> List[Dict[str, Any]]:
        """
        Get household budget data with caching
        Returns parsed list of categories with values
        """
        cache_key = f"ssb:household_budget:{year}:nowcast={nowcast}"

        # Try cache first (24h TTL)
        cached = cache.get(cache_key) if cache else None
        if cached is not None:
            self._cache_stats['hits'] += 1
            current_app.logger.debug(f"Cache hit: {cache_key}")
            return cached

        self._cache_stats['misses'] += 1
        current_app.logger.debug(f"Cache miss: {cache_key}")

        # Fetch from SSB
        raw_data = self.ssb_api.get_household_budget_data(year=year, nowcast=nowcast)
        if not raw_data:
            return []

        # Parse
        parsed = self.ssb_api.parse_household_data(raw_data)

        # Store in cache (24 hours)
        if cache:
            cache.set(cache_key, parsed, timeout=86400)

        return parsed

    def get_cpi_adjustments(self) -> Dict[str, float]:
        """Get CPI multipliers for inflation adjustment"""
        cache_key = "ssb:cpi_multipliers"

        cached = cache.get(cache_key) if cache else None
        if cached is not None:
            return cached

        multipliers = self.ssb_api.get_cpi_adjustments()

        # Cache for 1 hour (CPI changes slowly)
        if cache:
            cache.set(cache_key, multipliers, timeout=3600)

        return multipliers

    def get_inflation_history(self, categories: List[str] = ["TOTAL"], months: int = 24) -> Dict[str, Any]:
        """Get historical inflation data for charting"""
        cache_key = f"ssb:inflation_history:{','.join(categories)}:{months}m"

        cached = cache.get(cache_key) if cache else None
        if cached is not None:
            return cached

        result = self.ssb_api.get_inflation_history(categories=categories, months=months)

        # Cache for 6 hours
        if cache:
            cache.set(cache_key, result, timeout=21600)

        return result

    def get_landing_context(self) -> Dict[str, Any]:
        """Get all data needed for the landing page dashboard"""
        return {
            'household_budget': self.get_household_budget_data(nowcast=True),
            'cpi_multipliers': self.get_cpi_adjustments(),
            'inflation_trend': self.get_inflation_history()
        }

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache hit/miss statistics"""
        return dict(self._cache_stats)
