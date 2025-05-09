#!/bin/bash

# Get the directory where this script is located (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Check if USB path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/usb"
    exit 1
fi

USB_PATH="$1"

# Create necessary directories
mkdir -p "$USB_PATH/cybercrate/src/core"
mkdir -p "$USB_PATH/cybercrate/src/utils"
mkdir -p "$USB_PATH/cybercrate/templates"
mkdir -p "$USB_PATH/cybercrate/modules/crates"
mkdir -p "$USB_PATH/cybercrate/data/progress"
mkdir -p "$USB_PATH/cybercrate/data/backups"
mkdir -p "$USB_PATH/cybercrate/cheatsheets"
mkdir -p "$USB_PATH/cybercrate/tools/portable/nmap"
mkdir -p "$USB_PATH/cybercrate/tools/portable/h8mail"

# Copy core application files
cp "$PROJECT_ROOT/src/core/main.py" "$USB_PATH/cybercrate/src/core/"
cp "$PROJECT_ROOT/src/core/crate_builder.py" "$USB_PATH/cybercrate/src/core/"

# Copy utils (if any)
if [ -d "$PROJECT_ROOT/src/utils" ]; then
    cp -r "$PROJECT_ROOT/src/utils"/* "$USB_PATH/cybercrate/src/utils/"
fi

# Copy templates
cp -r "$PROJECT_ROOT/templates"/* "$USB_PATH/cybercrate/templates/"

# Copy all module crates and their content
cp -r "$PROJECT_ROOT/modules/crates"/* "$USB_PATH/cybercrate/modules/crates/"

# Copy requirements.txt
cp "$PROJECT_ROOT/requirements.txt" "$USB_PATH/cybercrate/"

# Create a fresh progress.yaml file in the correct location
cat > "$USB_PATH/cybercrate/data/progress/progress.yaml" << EOF
modules: {}
EOF

# Copy cheatsheets
if [ -d "$PROJECT_ROOT/cheatsheets" ]; then
    cp -r "$PROJECT_ROOT/cheatsheets"/* "$USB_PATH/cybercrate/cheatsheets/"
fi

# Copy all tools, including nmap and h8mail, with their LICENSE and README
cp -r "$PROJECT_ROOT/tools/portable/nmap"/* "$USB_PATH/cybercrate/tools/portable/nmap/"
cp -r "$PROJECT_ROOT/tools/portable/h8mail"/* "$USB_PATH/cybercrate/tools/portable/h8mail/"

# Remove any log files and scan history databases from the tools on the USB
find "$USB_PATH/cybercrate/tools/portable/" -type f \( -name "*.log" -o -name "*.sqlite" \) -delete

# Create virtual environment on USB
cd "$USB_PATH/cybercrate"
# Create venv if it doesn't exist
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
# Upgrade pip to latest version
pip install --upgrade pip
pip install --upgrade -r requirements.txt
# Clear pip cache
pip cache purge

# Create a launcher script
cat > "$USB_PATH/cybercrate/start_cybercrate.sh" << EOF
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python3 src/core/main.py
EOF

# Create reset progress script
cat > "$USB_PATH/cybercrate/reset_progress.sh" << RESET_EOF
#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROGRESS_FILE="$SCRIPT_DIR/data/progress/progress.yaml"
BACKUP_DIR="$SCRIPT_DIR/data/backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup of current progress if it exists
if [ -f "$PROGRESS_FILE" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/progress_$TIMESTAMP.yaml"
    cp "$PROGRESS_FILE" "$BACKUP_FILE"
    echo "Created backup of current progress at: $BACKUP_FILE"
fi

# Create fresh progress file
cat > "$PROGRESS_FILE" << PROGRESS_EOF
modules: {}
PROGRESS_EOF

echo "Progress has been reset to default state (all tasks pending)"
echo "A backup of your previous progress has been saved in the data/backups directory"
RESET_EOF

# Make scripts executable
chmod +x "$USB_PATH/cybercrate/start_cybercrate.sh"
chmod +x "$USB_PATH/cybercrate/reset_progress.sh"

# Remove AppleDouble files from the USB
find "$USB_PATH/cybercrate" -name '._*' -delete

echo "CyberCrate has been set up on your USB drive at $USB_PATH/cybercrate"
echo "To start CyberCrate, run: ./start_cybercrate.sh"
echo "To reset progress, run: ./reset_progress.sh" 