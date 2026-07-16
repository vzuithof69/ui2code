#!/usr/bin/env python3
"""PowerShell script syntax validator.

Validates PowerShell scripts for syntax errors before commit.
This prevents broken scripts from being committed to the repository.

Usage:
    python tools/test_powershell_syntax.py [script1.ps1] [script2.ps1] ...
    
Returns:
    Exit code 0 if all scripts are valid, 1 if any have errors.
"""

import subprocess
import sys
import os
from pathlib import Path


def validate_powershell_syntax(script_path: str) -> tuple[bool, str]:
    """Validate PowerShell script syntax using PowerShell's parser.
    
    Args:
        script_path: Path to the PowerShell script to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    script_path = os.path.abspath(script_path)
    
    if not os.path.exists(script_path):
        return False, f"Script not found: {script_path}"
    
    # PowerShell syntax validation command
    # This parses the script without executing it
    ps_command = f"""
    $ErrorActionPreference = "Stop"
    try {{
        $null = [System.Management.Automation.PSParser]::Tokenize(
            (Get-Content -Path "{script_path}" -Raw),
            [ref]$null
        )
        Write-Host "VALID"
        exit 0
    }}
    catch {{
        Write-Host "ERROR: $($_.Exception.Message)"
        exit 1
    }}
    """
    
    try:
        # Try with pwsh (PowerShell Core) first
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-NonInteractive", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, "Syntax OK"
        else:
            return False, result.stderr.strip() or result.stdout.strip()
            
    except FileNotFoundError:
        # pwsh not found, try with Windows PowerShell
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Syntax OK"
            else:
                return False, result.stderr.strip() or result.stdout.strip()
                
        except FileNotFoundError:
            return False, "Neither pwsh nor powershell.exe found"
        except subprocess.TimeoutExpired:
            return False, "PowerShell validation timed out"
    except subprocess.TimeoutExpired:
        return False, "PowerShell validation timed out"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"


def main():
    """Main validation function."""
    print("=" * 60)
    print("PowerShell Syntax Validator")
    print("=" * 60)
    
    # Default scripts to check
    default_scripts = [
        "Start-UI2Code.ps1"
    ]
    
    # Get scripts from command line or use defaults
    scripts_to_check = sys.argv[1:] if len(sys.argv) > 1 else default_scripts
    
    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent
    all_valid = True
    results = []
    
    for script in scripts_to_check:
        script_path = project_root / script
        print(f"\nValidating: {script_path.name}")
        print(f"  Path: {script_path}")
        
        is_valid, message = validate_powershell_syntax(str(script_path))
        
        if is_valid:
            print(f"  ✓ {message}")
            results.append((script, True, message))
        else:
            print(f"  ✗ {message}")
            results.append((script, False, message))
            all_valid = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for script, is_valid, message in results:
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"{status}: {script}")
        if not is_valid:
            print(f"  Error: {message}")
    
    print("=" * 60)
    
    if all_valid:
        print("All PowerShell scripts have valid syntax!")
        return 0
    else:
        print("One or more scripts have syntax errors!")
        print("\nFix errors before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
