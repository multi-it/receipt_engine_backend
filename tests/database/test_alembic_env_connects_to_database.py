import pytest
import os

def test_alembic_env_imports_are_correct():
    """Test that alembic env.py has correct imports"""
    env_path = "alembic/env.py"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check required imports
    assert "import asyncio" in content
    assert "from sqlalchemy.ext.asyncio import create_async_engine" in content
    assert "from alembic import context" in content
    assert "from app.config import settings" in content
    assert "from app.database.connection import Base" in content

def test_alembic_env_has_target_metadata():
    """Test that alembic env.py properly sets target_metadata"""
    env_path = "alembic/env.py"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check that target_metadata is set
    assert "target_metadata = Base.metadata" in content
    
    # Check that models are imported
    assert "from app.database.models import UserModel, ReceiptModel, ReceiptItemModel" in content

def test_alembic_env_has_async_functions():
    """Test that alembic env.py has async migration functions"""
    env_path = "alembic/env.py"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check async functions
    assert "async def run_migrations_online() -> None:" in content
    assert "create_async_engine(" in content

def test_alembic_config_file_structure():
    """Test that alembic.ini has proper structure"""
    config_path = "alembic.ini"
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check main sections
    assert "[alembic]" in content
    assert "[loggers]" in content
    assert "[handlers]" in content
    assert "[formatters]" in content
    
    # Check important settings
    assert "script_location = alembic" in content
    assert "prepend_sys_path = ." in content
    assert "timezone = UTC" in content
    assert "path_separator = os" in content

def test_alembic_env_handles_both_modes():
    """Test that alembic env.py handles both online and offline modes"""
    env_path = "alembic/env.py"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check that both modes are handled
    assert "if context.is_offline_mode():" in content
    assert "run_migrations_offline()" in content
    
    # Check offline mode function
    assert "def run_migrations_offline() -> None:" in content
    
    # Check online mode function
    assert "async def run_migrations_online() -> None:" in content
    
    # Check event loop handling
    assert "asyncio.get_running_loop()" in content
