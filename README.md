# CyberCrate

CyberCrate is a portable, USB-based learning platform that delivers cybersecurity labs and tracks student progress without requiring installation or network access.

## Features

- **ModuleBox System**: Self-contained learning modules delivered via USB
- **Progress Tracking**: Local YAML-based progress tracking
- **Offline Web UI**: Simple, self-contained web interface
- **Zero Installation**: Runs directly from USB
- **Content Integrity**: Hash verification for module contents

## Project Structure

```
CyberCrate/
├── main.py              # Main launcher application
├── crate_builder.py     # Tool for creating .crate modules
├── skill_sheet.py       # Progress tracking system
├── utils.py            # Utility functions
├── templates/          # Web UI templates
└── example_crates/     # Sample module crates
```

## ModuleBox Format (.crate)

A .crate file is a ZIP archive containing:
- `manifest.json`: Module metadata and content verification
- `content/`: Module resources (tools, scripts, images)
- `instructions/`: Lab documentation
- `config/`: Configuration files

## Usage

1. Insert USB drive
2. Run `main.py`
3. Select a module to begin
4. Track progress through the web interface
5. Export progress as needed

## Creating Modules

Use `crate_builder.py` to create new modules:
```bash
python crate_builder.py create --name "Module Name" --path /path/to/content
```

## Progress Tracking

Progress is stored in `progress.yaml` and can be:
- Viewed through the web interface
- Exported for submission
- Imported from previous sessions

## Requirements

- Python 3.8+
- No additional installation required
- Works offline
