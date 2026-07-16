# UI2Code Test Environment
# Debian-based custom sandbox for UI2Code with Qt/PySide6 support

FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen
ENV DISPLAY=:99

# Install system dependencies for PySide6/Qt
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1 \
    libgl1 \
    libdbus-1-3 \
    libfontconfig1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxkbcommon0 \
    libglib2.0-0 \
    libglx0 \
    libopengl0 \
    libglx-mesa0 \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /workspace/project/ui2code

# Copy project files
COPY requirements.txt .
COPY ui/ ./ui/
COPY engine/ ./engine/
COPY tools/ ./tools/
COPY config/ ./config/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Verify PySide6 installation
RUN python -c "import PySide6; print('PySide6 version:', PySide6.__version__)"

# Check for missing libraries using ldd
RUN python -c "from PySide6 import QtWidgets; import os; print(QtWidgets.__file__)" && \
    ldd $(python -c "from PySide6 import QtWidgets; import os; print(os.path.dirname(QtWidgets.__file__))")/QtWidgets.abi3.so | grep "not found" || echo "No missing libraries"

# Create logs directory
RUN mkdir -p logs

# Default command: run tests
CMD ["bash", "-c", "python tools/test_import.py && QT_QPA_PLATFORM=offscreen python tools/test_gui.py"]
