#!/usr/bin/env python3
"""
Setup script for Personal Finance Intelligence API.
Run this to set up your development environment.
"""
import os
import sys
import subprocess
from pathlib import Path


def run_command(command, shell=False):
    """Run a shell command and return success status"""
    try:
        subprocess.run(command, check=True, shell=shell)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("=" * 60)
    print("Personal Finance Intelligence API - Setup")
    print("=" * 60)
    print()

    # Check Python version
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 10):
        print("   ❌ Python 3.10 or higher is required!")
        print(f"   Current version: {sys.version}")
        return False

    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    print()

    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        if run_command([sys.executable, "-m", "venv", "venv"]):
            print("   ✅ Virtual environment created")
        else:
            print("   ❌ Failed to create virtual environment")
            return False
        print()
    else:
        print("📦 Virtual environment already exists")
        print()

    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    # Install dependencies
    print("📥 Installing dependencies...")
    if run_command([str(pip_path), "install", "-r", "requirements.txt"]):
        print("   ✅ Dependencies installed")
    else:
        print("   ❌ Failed to install dependencies")
        return False
    print()

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("⚙️  Creating .env file...")
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("   ✅ .env file created")
            print("   ⚠️  Remember to add your OpenRouter API key to .env")
        else:
            print("   ⚠️  .env.example not found, skipping")
        print()
    else:
        print("⚙️  .env file already exists")
        print()

    # Summary
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print("1. Activate the virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print()
    print("2. (Optional) Add your OpenRouter API key to .env")
    print()
    print("3. Start the server:")
    print("   python run.py")
    print()
    print("4. Visit http://localhost:8000/docs")
    print()
    print("5. Run tests:")
    print("   python test_api.py")
    print()

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)
