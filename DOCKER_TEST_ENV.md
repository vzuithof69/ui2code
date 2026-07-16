# UI2Code Docker Test Environment

## Overview

This Dockerfile creates a reproducible Debian-based test environment for UI2Code with full PySide6/Qt support.

## Quick Start

### Build the Image

```bash
cd /workspace/project/ui2code
docker build -t ui2code-test:latest .
```

### Run Tests

```bash
# Run all tests (headless)
docker run --rm ui2code-test:latest

# Run with interactive shell
docker run --rm -it ui2code-test:latest bash

# Run specific test
docker run --rm ui2code-test:latest python tools/test_import.py
```

### Run GUI Tests with Xvfb

```bash
# Xvfb provides virtual framebuffer for GUI testing
docker run --rm ui2code-test:latest xvfb-run -a python tools/test_gui.py
```

## Included System Libraries

### Core Qt/PySide6 Dependencies

```dockerfile
libegl1          # EGL library for OpenGL rendering
libgl1           # OpenGL library
libdbus-1-3      # D-Bus IPC library
libfontconfig1   # Font configuration library
libxkbcommon-x11-0  # X11 keyboard handling
libxcb-cursor0   # XCB cursor support
```

### Additional XCB Libraries

```dockerfile
libxcb-icccm4    # XCB ICCCM support
libxcb-image0    # XCB image utilities
libxcb-keysyms1  # XCB keysym support
libxcb-randr0    # XCB RandR extension
libxcb-render-util0  # XCB render utilities
libxcb-shape0    # XCB shape extension
libxcb-xfixes0   # XCB XFIXES extension
libxcb-xinerama0 # XCB Xinerama support
```

### Supporting Libraries

```dockerfile
libxkbcommon0    # XKB common library
libglib2.0-0     # GLib 2.0
libglx0          # GLX library
libopengl0       # OpenGL support
libglx-mesa0     # Mesa GLX implementation
```

### Testing Tools

```dockerfile
xvfb             # X Virtual Framebuffer for headless testing
xauth            # X11 authorization
```

## Manual Installation (Alternative)

If not using Docker, install dependencies manually:

```bash
# Update package lists
sudo apt-get update

# Install minimal required packages
sudo apt-get install -y --no-install-recommends \
    libegl1 \
    libgl1 \
    libdbus-1-3 \
    libfontconfig1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

# Install PySide6
pip install -r requirements.txt

# Verify installation
python -c "import PySide6; print('PySide6 OK')"
```

## Verify Library Completeness

Check for missing libraries:

```bash
# Find PySide6 installation
PYSIDE6_PATH=$(python -c "import PySide6; import os; print(os.path.dirname(PySide6.__file__))")

# Check for missing libraries
ldd $PYSIDE6_PATH/QtWidgets.abi3.so | grep "not found"
```

If any libraries are missing, install them:

```bash
apt-get install -y <missing-package-name>
```

## Testing

### Import Test

```bash
python tools/test_import.py
```

Expected output:
```
Testing UI2Code module imports...
----------------------------------------
Importing engine.ui2code_core...
  ✓ UI2CodeCore imported successfully
...
All imports successful!
```

### Headless GUI Test (Offscreen)

```bash
QT_QPA_PLATFORM=offscreen python tools/test_gui.py
```

### GUI Test with Xvfb

```bash
xvfb-run -a python tools/test_gui.py
```

Expected output:
```
Testing UI2Code GUI creation (headless mode)...
----------------------------------------
Creating QApplication...
  ✓ QApplication created
...
All GUI tests passed!
```

## Troubleshooting

### "libEGL.so.1: cannot open shared object file"

Install EGL library:
```bash
apt-get install libegl1
```

### "libdbus-1.so.3: cannot open shared object file"

Install D-Bus library:
```bash
apt-get install libdbus-1-3
```

### "could not find Qt platform plugin 'offscreen'"

Ensure PySide6 is properly installed:
```bash
pip install --force-reinstall PySide6
```

### "ImportError: libxkbcommon-x11.so.0"

Install XKB library:
```bash
apt-get install libxkbcommon-x11-0
```

### GUI Test Fails with "QApplication" Error

Set offscreen platform:
```bash
export QT_QPA_PLATFORM=offscreen
python tools/test_gui.py
```

Or use Xvfb:
```bash
xvfb-run -a python tools/test_gui.py
```

## Docker Build Optimization

### Reduce Image Size

The Dockerfile uses `--no-install-recommends` to minimize package installation. Additional optimization:

```dockerfile
# Multi-stage build example
FROM python:3.12-slim-bookworm as builder
# ... build steps ...

FROM python:3.12-slim-bookworm
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# ... copy only necessary files ...
```

### Cache Layers

Order Dockerfile commands from least to most frequently changing:
1. System packages (apt-get)
2. Python packages (pip)
3. Application code (COPY)

## Environment Variables

```bash
QT_QPA_PLATFORM=offscreen    # Use offscreen platform for headless testing
DISPLAY=:99                  # X11 display for Xvfb
PYTHONDONTWRITEBYTECODE=1    # Don't write .pyc files
PYTHONUNBUFFERED=1          # Unbuffered Python output
```

## Security Notes

- Run as non-root user in production
- Don't mount sensitive directories
- Use read-only filesystem where possible
- Regularly update base image and dependencies

## Version Compatibility

- **Base Image:** Debian 12 (Bookworm)
- **Python:** 3.12
- **PySide6:** 6.5.0+ (from requirements.txt)
- **Qt:** 6.x (bundled with PySide6)

## Support

For issues:
1. Check missing libraries with `ldd`
2. Verify Qt platform plugins: `python -c "from PySide6.QtGui import QGuiApplication; print(QGuiApplication.platformName())"`
3. Review logs in `logs/` directory
4. Create issue on GitHub with full error output
