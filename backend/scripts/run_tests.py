#!/usr/bin/env python3
"""
Test runner script for the Vogelring backend

This script provides a convenient way to run different types of tests
with proper environment setup and reporting.

Usage:
    python run_tests.py [--type TYPE] [--coverage] [--verbose]

Options:
    --type TYPE     Type of tests to run: all, api, database, migration (default: all)
    --coverage      Run tests with coverage reporting
    --verbose       Run tests with verbose output
    --help          Show this help message
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install -r requirements-test.txt")
        return False


def install_test_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    cmd = ["uv", "sync", "--extra", "test"]
    return run_command(cmd, "Installing test dependencies")


def run_tests(test_type="all", coverage=False, verbose=False):
    """Run tests based on type"""

    # Base pytest command
    cmd = ["uv", "run", "pytest"]

    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Exclude boto3-dependent tests by default
    cmd.extend(["-k", "not (test_dynamodb_migration_mock or test_s3_migration_mock)"])

    # Add test selection based on type
    if test_type == "api":
        cmd.extend(["tests/test_api_*.py"])
        description = "API endpoint tests"
    elif test_type == "database":
        cmd.extend(["tests/test_database_*.py"])
        description = "Database integration tests"
    elif test_type == "migration":
        cmd.extend(["tests/test_migration_*.py"])
        description = "Migration script tests (excluding AWS-dependent tests)"
    elif test_type == "all":
        cmd.append("tests/")
        description = "All tests (excluding AWS-dependent tests)"
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False

    return run_command(cmd, description)


def check_environment():
    """Check if the environment is set up correctly"""
    print("Checking environment...")

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Make sure you're in the backend directory.")
        return False

    # Check if src directory exists
    if not Path("src").exists():
        print("❌ src directory not found.")
        return False

    # Check if tests directory exists
    if not Path("tests").exists():
        print("❌ tests directory not found.")
        return False

    print("✅ Environment check passed")
    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Run tests for the Vogelring backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py --type api         # Run only API tests
    python run_tests.py --coverage         # Run with coverage
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --type database --coverage --verbose
        """,
    )

    parser.add_argument(
        "--type",
        choices=["all", "api", "database", "migration"],
        default="all",
        help="Type of tests to run (default: all)",
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage reporting"
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Run tests with verbose output"
    )

    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running tests",
    )

    args = parser.parse_args()

    print("🧪 Vogelring Backend Test Runner")
    print("=" * 40)

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)

    # Run tests
    success = run_tests(
        test_type=args.type, coverage=args.coverage, verbose=args.verbose
    )

    if success:
        print("\n🎉 All tests completed successfully!")
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
