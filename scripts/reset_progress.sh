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