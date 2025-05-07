#!/bin/bash

# Check if USB path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/usb"
    exit 1
fi

USB_PATH="$1"

# Create necessary directories
mkdir -p "$USB_PATH/cybercrate"
mkdir -p "$USB_PATH/cybercrate/templates"
mkdir -p "$USB_PATH/cybercrate/example_crates"
mkdir -p "$USB_PATH/cybercrate/progress_backups"

# Copy main files
cp main.py "$USB_PATH/cybercrate/"
cp crate_builder.py "$USB_PATH/cybercrate/"
cp requirements.txt "$USB_PATH/cybercrate/"
cp -r templates/* "$USB_PATH/cybercrate/templates/"
cp -r example_crates/* "$USB_PATH/cybercrate/example_crates/"

# Create a fresh progress.yaml file
cat > "$USB_PATH/cybercrate/progress.yaml" << 'EOF'
modules: {}
EOF

# Create virtual environment on USB
cd "$USB_PATH/cybercrate"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create a launcher script
cat > "$USB_PATH/cybercrate/start_cybercrate.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
EOF

# Create reset progress script
cat > "$USB_PATH/cybercrate/reset_progress.sh" << 'EOF'
#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROGRESS_FILE="$SCRIPT_DIR/progress.yaml"
BACKUP_DIR="$SCRIPT_DIR/progress_backups"

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
cat > "$PROGRESS_FILE" << 'EOF'
modules: {}
EOF

echo "Progress has been reset to default state (all tasks pending)"
echo "A backup of your previous progress has been saved in the progress_backups directory"
EOF

# Make scripts executable
chmod +x "$USB_PATH/cybercrate/start_cybercrate.sh"
chmod +x "$USB_PATH/cybercrate/reset_progress.sh"

echo "CyberCrate has been set up on your USB drive at $USB_PATH/cybercrate"
echo "To start CyberCrate, run: ./start_cybercrate.sh"
echo "To reset progress, run: ./reset_progress.sh" 