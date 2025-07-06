import pytest
from alembic.config import Config
import os

def test_migration_downgrade_configuration():
    """Test that alembic downgrade configuration is properly set"""
    alembic_cfg = Config("alembic.ini")
    
    # Check that config can be loaded
    assert alembic_cfg.get_main_option("script_location") == "alembic"
    
    # Check that downgrade function exists in template
    template_path = "alembic/script.py.mako"
    with open(template_path, 'r') as f:
        content = f.read()
        assert "def downgrade() -> None:" in content

def test_migration_downgrade_template_has_proper_structure():
    """Test that migration template supports downgrade operations"""
    template_path = "alembic/script.py.mako"
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Check that downgrade function has proper docstring
    assert '"""Downgrade database schema."""' in content
    
    # Check that it has proper default behavior
    assert "${downgrades if downgrades else \"pass\"}" in content

def test_alembic_supports_offline_mode():
    """Test that alembic env.py supports offline mode"""
    env_path = "alembic/env.py"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check offline mode function exists
    assert "def run_migrations_offline() -> None:" in content
    assert "context.is_offline_mode()" in content
    
    # Check that it configures context properly
    assert "context.configure(" in content
    assert "literal_binds=True" in content
