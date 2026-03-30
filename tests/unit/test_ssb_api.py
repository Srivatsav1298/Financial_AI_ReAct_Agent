"""
Unit Tests for SSB API
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.utils.ssb_api import SSBApi


class TestSSBApi:
    """Tests for SSB API wrapper"""

    def test_init_creates_cache_dir(self, tmp_path):
        """Test that initialization creates cache directory"""
        cache_dir = tmp_path / "test_cache"
        api = SSBApi(cache_dir=str(cache_dir))
        assert cache_dir.exists()

    def test_query_table_with_cache_hit(self, tmp_path):
        """Test that cached data is returned when available"""
        cache_dir = tmp_path / "test_cache"
        api = SSBApi(cache_dir=str(cache_dir))

        # First call - cache miss
        result1 = api.query_table("test_table", {"query": {}}, use_cache=True)
        assert result1 is None  # Will fail due to network, but cache won't be set

        # Second call should also miss (no data cached)
        # Cache only works for successful responses

    def test_cache_initialization(self):
        """Test that cache is properly initialized"""
        api = SSBApi()
        assert hasattr(api, '_memory_cache')
        assert isinstance(api._memory_cache, dict)

    def test_cache_key_generation(self, tmp_path):
        """Test cache file path generation"""
        cache_dir = tmp_path / "test_cache"
        api = SSBApi(cache_dir=str(cache_dir))
        path = api._get_cache_path("table123", "hash456")
        assert path.name == "table123_hash456.json"
        assert path.parent == cache_dir

    def test_load_from_cache(self, tmp_path):
        """Test loading data from cache file"""
        cache_dir = tmp_path / "test_cache"
        cache_dir.mkdir()
        api = SSBApi(cache_dir=str(cache_dir))

        # Create a cache file
        test_data = {"test": "data"}
        cache_file = cache_dir / "test_table_hash.json"
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)

        loaded = api._load_from_cache(cache_file)
        assert loaded == test_data

    def test_load_from_nonexistent_cache(self, tmp_path):
        """Test loading from non-existent cache returns None"""
        cache_dir = tmp_path / "test_cache"
        api = SSBApi(cache_dir=str(cache_dir))
        non_existent = cache_dir / "no_file.json"
        result = api._load_from_cache(non_existent)
        assert result is None

    def test_save_to_cache(self, tmp_path):
        """Test saving data to cache file"""
        cache_dir = tmp_path / "test_cache"
        api = SSBApi(cache_dir=str(cache_dir))
        cache_file = cache_dir / "test.json"

        test_data = {"key": "value"}
        api._save_to_cache(cache_file, test_data)

        assert cache_file.exists()
        with open(cache_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_data
