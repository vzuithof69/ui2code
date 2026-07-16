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
import re
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


def check_executable_argument_antipattern(script_path: str) -> tuple[bool, list[str]]:
    """Check for the anti-pattern of storing executable+argument as single string.
    
    This prevents errors like:
        $pythonExe = "py -3.12"  # BAD - PowerShell treats as single executable
        & $pythonExe --version   # Fails: "py -3.12" is not recognized
    
    Correct pattern:
        $PyLauncher = (Get-Command py.exe).Source
        & $PyLauncher -3.12 --version  # Works - executable and args separated
    
    Args:
        script_path: Path to the PowerShell script to check.
        
    Returns:
        Tuple of (is_valid, list_of_issues).
    """
    script_path = os.path.abspath(script_path)
    issues = []
    
    if not os.path.exists(script_path):
        return False, [f"Script not found: {script_path}"]
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Pattern 1: Variable assignment with executable + argument as single string
    # e.g., $pythonExe = "py -3.12" or $cmd = 'python -m pip'
    # This is dangerous because & $var treats the whole string as executable
    executable_patterns = [
        r'\$\w+\s*=\s*["\']py\s+-\d+\.\d+["\']',  # $var = "py -3.12"
        r'\$\w+\s*=\s*["\']python\s+-\d+\.\d+["\']',  # $var = "python -3.12"
        r'\$\w+\s*=\s*["\']py\s+[^"\']*\d+\.\d+["\']',  # $var = "py -X.Y"
    ]
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        
        for pattern in executable_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    f"Line {line_num}: Executable+argument stored as single string.\n"
                    f"  Found: {line.strip()}\n"
                    f"  Fix: Use $PyLauncher = (Get-Command py.exe).Source\n"
                    f"       Then: & $PyLauncher -3.12 <args>"
                )
    
    # Pattern 2: Check for proper PyLauncher usage if py.exe is referenced
    # If script uses py.exe, it should use Get-Command pattern
    has_py_reference = 'py' in content.lower() and ('-3.12' in content or '-3.' in content)
    has_get_command = 'Get-Command' in content and 'py.exe' in content
    
    if has_py_reference and not has_get_command:
        # Check if there's a direct & py -3.12 usage (this is OK in some contexts)
        direct_py_usage = re.search(r'&\s*py\s+-\d+\.\d+', content)
        if direct_py_usage:
            issues.append(
                "Direct 'py -3.12' usage detected without PyLauncher abstraction.\n"
                "  Recommended: Use $PyLauncher = (Get-Command py.exe).Source\n"
                "             Then: & $PyLauncher -3.12 <args>"
            )
    
    return len(issues) == 0, issues


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
    syntax_results = []
    antipattern_results = []
    
    for script in scripts_to_check:
        script_path = project_root / script
        print(f"\nValidating: {script_path.name}")
        print(f"  Path: {script_path}")
        
        # Syntax validation
        is_valid, message = validate_powershell_syntax(str(script_path))
        
        if is_valid:
            print(f"  ✓ Syntax: {message}")
            syntax_results.append((script, True, message))
        else:
            print(f"  ✗ Syntax: {message}")
            syntax_results.append((script, False, message))
            all_valid = False
        
        # Anti-pattern check
        is_valid, issues = check_executable_argument_antipattern(str(script_path))
        
        if is_valid:
            print(f"  ✓ Anti-pattern check: No issues found")
            antipattern_results.append((script, True, []))
        else:
            print(f"  ✗ Anti-pattern check: {len(issues)} issue(s) found:")
            for issue in issues:
                print(f"    - {issue}")
            antipattern_results.append((script, False, issues))
            all_valid = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    # Syntax results
    print("\nSyntax Validation:")
    for script, is_valid, message in syntax_results:
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"  {status}: {script}")
        if not is_valid:
            print(f"    Error: {message}")
    
    # Anti-pattern results
    print("\nAnti-pattern Check:")
    for script, is_valid, issues in antipattern_results:
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"  {status}: {script}")
        if not is_valid:
            for issue in issues:
                print(f"    Issue: {issue}")
    
    print("=" * 60)
    
    if all_valid:
        print("All PowerShell scripts have valid syntax and no anti-patterns!")
        return 0
    else:
        print("One or more scripts have issues!")
        print("\nFix errors before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
