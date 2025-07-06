import pytest
import subprocess
import sys
import tempfile
import shutil
import os

def test_migration_upgrade_works():
    """Test that alembic can upgrade database schema"""
    # Use aiosqlite for async SQLite support
    test_db_url = "sqlite+aiosqlite:///./test_migrations.db"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy necessary files
        if os.path.exists("alembic"):
            shutil.copytree("alembic", os.path.join(temp_dir, "alembic"))
        if os.path.exists("alembic.ini"):
            shutil.copy("alembic.ini", temp_dir)
        if os.path.exists("app"):
            shutil.copytree("app", os.path.join(temp_dir, "app"))
        
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Use subprocess to run alembic upgrade
            result = subprocess.run([
                sys.executable, "-c",
                f"""
import sys
sys.path.insert(0, '.')
from alembic.config import Config
from alembic import command
try:
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', '{test_db_url}')
    command.upgrade(alembic_cfg, 'head')
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {{e}}')
                """
            ], capture_output=True, text=True, timeout=30)
            
            success = "SUCCESS" in result.stdout
            error_msg = result.stderr if result.stderr else result.stdout
            
            assert success, f"Migration upgrade failed: {error_msg}"
            
        finally:
            os.chdir(old_cwd)

def test_alembic_config_database_url_setting():
    """Test that alembic config can be set with database URL"""
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    test_url = "postgresql://test:test@localhost/test_db"
    
    alembic_cfg.set_main_option("sqlalchemy.url", test_url)
    
    assert alembic_cfg.get_main_option("sqlalchemy.url") == test_url
