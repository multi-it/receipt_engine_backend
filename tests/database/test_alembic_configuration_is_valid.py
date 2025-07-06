import pytest
from alembic.config import Config
import os

def test_alembic_configuration_is_valid():
    """Test that alembic configuration is properly set up"""
    alembic_cfg = Config("alembic.ini")
    
    assert alembic_cfg.get_main_option("script_location") == "alembic"
    assert alembic_cfg.get_main_option("prepend_sys_path") == "."
    assert alembic_cfg.get_main_option("version_path_separator") == "os"
    assert alembic_cfg.get_main_option("path_separator") == "os"
    assert alembic_cfg.get_main_option("timezone") == "UTC"

def test_alembic_env_file_exists():
    """Test that alembic env.py file exists and is properly configured"""
    env_path = "alembic/env.py"
    assert os.path.exists(env_path)
    
    with open(env_path, 'r') as f:
        content = f.read()
        assert "from app.config import settings" in content
        assert "from app.database.connection import Base" in content
        assert "from app.database.models import UserModel, ReceiptModel, ReceiptItemModel" in content

def test_alembic_script_template_exists():
    """Test that alembic script template exists"""
    template_path = "alembic/script.py.mako"
    assert os.path.exists(template_path)
    
    with open(template_path, 'r') as f:
        content = f.read()
        assert "def upgrade() -> None:" in content
        assert "def downgrade() -> None:" in content

def test_alembic_versions_directory_exists():
    """Test that alembic versions directory exists"""
    versions_path = "alembic/versions"
    assert os.path.exists(versions_path)
    assert os.path.isdir(versions_path)
