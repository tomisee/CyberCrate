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

# Copy main files
cp main.py "$USB_PATH/cybercrate/"
cp crate_builder.py "$USB_PATH/cybercrate/"
cp requirements.txt "$USB_PATH/cybercrate/"
cp -r templates/* "$USB_PATH/cybercrate/templates/"
cp -r example_crates/* "$USB_PATH/cybercrate/example_crates/"

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

chmod +x "$USB_PATH/cybercrate/start_cybercrate.sh"

echo "CyberCrate has been set up on your USB drive at $USB_PATH/cybercrate"
echo "To start CyberCrate, run: ./start_cybercrate.sh" 