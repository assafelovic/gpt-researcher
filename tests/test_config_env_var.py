"""
Test configuration loading from environment variable.

This module tests the GPT_RESEARCHER_CONFIG_PATH environment variable
support for loading configuration files, as requested in GitHub issue #1630.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch

from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG


class TestConfigEnvVar:
    """Test configuration loading from GPT_RESEARCHER_CONFIG_PATH env var."""

    def test_config_without_env_var_uses_defaults(self):
        """Test that Config uses defaults when no env var or path is provided."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            os.environ.pop("GPT_RESEARCHER_CONFIG_PATH", None)
            
            config = Config()
            
            # Should have default values
            assert config.config_path is None

    def test_config_with_env_var_loads_custom_config(self):
        """Test that Config loads from GPT_RESEARCHER_CONFIG_PATH when set."""
        # Create a temporary config file
        custom_config = {
            "FAST_LLM": "openai:gpt-4o",
            "SMART_LLM": "openai:gpt-4o",
            "STRATEGIC_LLM": "openai:gpt-4o",
            "EMBEDDING": "openai:text-embedding-3-small"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_path = f.name
        
        try:
            with patch.dict(os.environ, {"GPT_RESEARCHER_CONFIG_PATH": temp_path}):
                config = Config()
                
                # Should have loaded from the env var path
                assert config.config_path == temp_path
                assert config.fast_llm_model == "gpt-4o"
        finally:
            os.unlink(temp_path)

    def test_explicit_path_overrides_env_var(self):
        """Test that explicit config_path parameter takes precedence over env var."""
        # Create two config files
        env_config = {"FAST_LLM": "openai:gpt-3.5-turbo", "SMART_LLM": "openai:gpt-3.5-turbo", "STRATEGIC_LLM": "openai:gpt-3.5-turbo", "EMBEDDING": "openai:text-embedding-3-small"}
        explicit_config = {"FAST_LLM": "openai:gpt-4o", "SMART_LLM": "openai:gpt-4o", "STRATEGIC_LLM": "openai:gpt-4o", "EMBEDDING": "openai:text-embedding-3-small"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_env.json', delete=False) as f:
            json.dump(env_config, f)
            env_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_explicit.json', delete=False) as f:
            json.dump(explicit_config, f)
            explicit_path = f.name
        
        try:
            with patch.dict(os.environ, {"GPT_RESEARCHER_CONFIG_PATH": env_path}):
                config = Config(config_path=explicit_path)
                
                # Should use the explicit path, not the env var
                assert config.config_path == explicit_path
                assert config.fast_llm_model == "gpt-4o"
        finally:
            os.unlink(env_path)
            os.unlink(explicit_path)

    def test_empty_env_var_uses_defaults(self):
        """Test that an empty string env var is treated as not set."""
        with patch.dict(os.environ, {"GPT_RESEARCHER_CONFIG_PATH": ""}):
            config = Config()
            
            # Empty string should be treated as None
            assert config.config_path is None

    def test_env_var_nonexistent_file_uses_defaults(self):
        """Test that non-existent file path falls back to defaults with warning."""
        nonexistent_path = "/nonexistent/config/path/config.json"
        
        with patch.dict(os.environ, {"GPT_RESEARCHER_CONFIG_PATH": nonexistent_path}):
            # Should not raise an error, just print a warning and use defaults
            config = Config()
            
            # Should still have the path stored, but use default config
            assert config.config_path == nonexistent_path

    def test_config_path_attribute_reflects_env_var(self):
        """Test that config_path attribute reflects the actual path used."""
        custom_config = {
            "FAST_LLM": "openai:gpt-4o",
            "SMART_LLM": "openai:gpt-4o", 
            "STRATEGIC_LLM": "openai:gpt-4o",
            "EMBEDDING": "openai:text-embedding-3-small"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_path = f.name
        
        try:
            with patch.dict(os.environ, {"GPT_RESEARCHER_CONFIG_PATH": temp_path}):
                config = Config()
                
                # The config_path attribute should reflect the env var path
                assert config.config_path == temp_path
        finally:
            os.unlink(temp_path)

    def test_backward_compatibility_explicit_none(self):
        """Test backward compatibility: passing None explicitly still works."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GPT_RESEARCHER_CONFIG_PATH", None)
            
            # This should work exactly as before
            config = Config(config_path=None)
            
            assert config.config_path is None

    def test_backward_compatibility_explicit_path(self):
        """Test backward compatibility: passing explicit path still works."""
        custom_config = {
            "FAST_LLM": "openai:gpt-4o",
            "SMART_LLM": "openai:gpt-4o",
            "STRATEGIC_LLM": "openai:gpt-4o", 
            "EMBEDDING": "openai:text-embedding-3-small"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_path = f.name
        
        try:
            # Even with env var set, explicit path should work
            with patch.dict(os.environ, {"GPT_RESEARCHER_CONFIG_PATH": "/some/other/path.json"}):
                config = Config(config_path=temp_path)
                
                assert config.config_path == temp_path
        finally:
            os.unlink(temp_path)


class TestConfigLoadConfig:
    """Test the load_config class method directly."""

    def test_load_config_with_none_returns_defaults(self):
        """Test load_config returns DEFAULT_CONFIG when called with None."""
        result = Config.load_config(None)
        assert result == DEFAULT_CONFIG

    def test_load_config_with_valid_path(self):
        """Test load_config loads and merges config from valid path."""
        custom_config = {
            "FAST_LLM": "anthropic:claude-3-sonnet",
            "SMART_LLM": "anthropic:claude-3-sonnet",
            "STRATEGIC_LLM": "anthropic:claude-3-sonnet",
            "EMBEDDING": "openai:text-embedding-3-small"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_path = f.name
        
        try:
            result = Config.load_config(temp_path)
            
            # Should have custom value
            assert result["FAST_LLM"] == "anthropic:claude-3-sonnet"
            # Should still have other default keys
            assert "RETRIEVER" in result
        finally:
            os.unlink(temp_path)

    def test_load_config_nonexistent_path_returns_defaults(self):
        """Test load_config returns defaults for non-existent path."""
        result = Config.load_config("/nonexistent/path/config.json")
        assert result == DEFAULT_CONFIG
