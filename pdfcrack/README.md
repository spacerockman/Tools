# PDF Unlock Tool

A simple Python utility to unlock password-protected PDF files.

## Requirements

- Python 3.6 or higher
- pikepdf library

## Installation

1. Clone or download this repository
2. Install the required dependency:

```
pip install pikepdf
```

## Usage

```
python pdf_unlock.py input.pdf output.pdf password
```

Where:
- `input.pdf` is the path to your password-protected PDF file
- `output.pdf` is the path where the unlocked PDF will be saved
- `password` is the password to unlock the PDF

## Example

```
python pdf_unlock.py protected.pdf unlocked.pdf mypassword123
```

## Error Handling

The script handles various error scenarios:
- Input file not found
- Incorrect password
- Invalid PDF format
- Other unexpected errors

## How It Works

The script uses the pikepdf library to open the password-protected PDF file and save it without encryption.