# H8mail OSINT Tool Integration

This module integrates the h8mail OSINT tool into CyberCrate, providing email reconnaissance capabilities.

## Features

- Email address reconnaissance
- Domain reconnaissance
- Breach database checking
- Leak database checking
- Scan history tracking
- Configurable API keys
- Modern web interface

## Requirements

- Python 3.7+
- Virtual environment support
- Internet connection for API access

## Installation

The module will automatically install h8mail and its dependencies when first used. No manual installation is required.

## Configuration

API keys can be configured in `config/settings.json`:

```json
{
    "api_keys": {
        "h8mail": "your_h8mail_key",
        "hunter": "your_hunter_key",
        "breachdirectory": "your_breachdirectory_key",
        "leakcheck": "your_leakcheck_key"
    }
}
```

## Usage

1. Access the h8mail tool through the CyberCrate web interface
2. Enter an email address or domain to scan
3. Select scan options (breach check, leak check, etc.)
4. Click "Run Scan" to start the reconnaissance
5. View results in the output panel
6. Access scan history in the history table

## Security Considerations

- API keys are stored securely in the configuration file
- All scans are logged for audit purposes
- Results are stored in a local SQLite database
- Temporary files are automatically cleaned up

## Troubleshooting

If you encounter issues:

1. Check the h8mail.log file for error messages
2. Verify your API keys are correctly configured
3. Ensure you have an active internet connection
4. Check that the virtual environment is properly set up

## License

This module is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

The h8mail tool itself is licensed under the BSD 3-Clause License. This wrapper is just a method of installing and managing h8mail within CyberCrate. For more information about h8mail, visit: https://github.com/khast3x/h8mail

## Contributing

Feel free to submit issues and enhancement requests! 