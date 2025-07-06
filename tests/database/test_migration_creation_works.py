import pytest
import tempfile
import os
import shutil
import subprocess
import sys

def test_migration_creation_works():
    """Test that alembic can create migration files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy alembic files to temp directory
        shutil.copytree("alembic", os.path.join(temp_dir, "alembic"))
        shutil.copy("alembic.ini", temp_dir)
        
        # Copy app directory to temp directory for imports
        if os.path.exists("app"):
            shutil.copytree("app", os.path.join(temp_dir, "app"))
        
        # Change to temp directory
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Use subprocess to avoid import issues
            result = subprocess.run([
                sys.executable, "-c",
                """
import sys
sys.path.insert(0, '.')
from alembic.config import Config
from alembic import command
try:
    alembic_cfg = Config('alembic.ini')
    command.revision(alembic_cfg, message='test_migration', autogenerate=False)
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
                """
            ], capture_output=True, text=True, timeout=30)
            
            success = "SUCCESS" in result.stdout
            error_msg = result.stderr if result.stderr else result.stdout
            
            assert success, f"Migration creation failed: {error_msg}"
            
        finally:
            os.chdir(old_cwd)

def test_migration_file_template_format():
    """Test that migration file template has correct format"""
    template_path = "alembic/script.py.mako"
    
    with open(template_path, 'r') as f:
        content = f.read()
        
    # Check required template variables
    assert "${message}" in content
    assert "${up_revision}" in content
    assert "${down_revision | comma,n}" in content
    assert "${create_date}" in content
    
    # Check function signatures
    assert "def upgrade() -> None:" in content
    assert "def downgrade() -> None:" in content
    
    # Check revision identifiers
    assert "revision = ${repr(up_revision)}" in content
    assert "down_revision = ${repr(down_revision)}" in content
