import subprocess
import sys

def check_command(cmd, version_flag='--version'):
    """Check if command is available and return version info."""
    try:
        result = subprocess.run(
            [cmd, version_flag],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        version_line = result.stdout.splitlines()[0].strip()
        return True, version_line
    except subprocess.TimeoutExpired:
        return False, f"Timeout executing {cmd}"
    except subprocess.CalledProcessError as e:
        return False, f"Command failed with code {e.returncode}"
    except FileNotFoundError:
        return False, f"Command not found"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    checks = [
        ('python3', '--version'),
        ('dbt', '--version'),
        ('rclone', '--version'),
        ('influx', '--version'),
        ('duckdb', '--version'),
        ('git', '--version'),
        ('jq', '--version'),
        ('curl', '--version'),
        ('sqlfluff', '--version')
    ]
    
    print("🔍 Testing development environment...")
    all_ok = True
    
    for cmd, flag in checks:
        success, output = check_command(cmd, flag)
        if success:
            print(f"✅ {cmd}: {output}")
        else:
            print(f"❌ {cmd}: {output}")
            all_ok = False
    
    if all_ok:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
