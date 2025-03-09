#!/usr/bin/env python3
"""
PDF Unlock Script

This script unlocks password-protected PDF files using the pikepdf library.
Usage: python pdf_unlock.py input.pdf output.pdf password
"""

import sys
import os
import argparse
from typing import Optional, Tuple

try:
    import pikepdf
except ImportError:
    print("Error: pikepdf library is not installed.")
    print("Please install it using: pip install pikepdf")
    sys.exit(1)


def unlock_pdf(input_path: str, output_path: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Unlock a password-protected PDF file.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path where the unlocked PDF will be saved
        password: Password to unlock the PDF
        
    Returns:
        Tuple containing success status (bool) and error message (str) if any
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            return False, f"Input file not found: {input_path}"
            
        # Open the PDF with the provided password
        with pikepdf.open(input_path, password=password) as pdf:
            # Save without encryption
            pdf.save(output_path)
            
        return True, None
        
    except pikepdf.PasswordError:
        return False, "Incorrect password" if password else "PDF requires a password but none was provided"
    except pikepdf.PdfError as e:
        return False, f"PDF Error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Unlock password-protected PDF files")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("output", help="Path where the unlocked PDF will be saved")
    parser.add_argument("password", nargs='?', help="Password to unlock the PDF (if required)", default=None)
    
    args = parser.parse_args()
    
    print(f"Attempting to unlock PDF: {args.input}")
    success, error = unlock_pdf(args.input, args.output, args.password)
    
    if success:
        print(f"PDF successfully unlocked and saved to: {args.output}")
    else:
        print(f"Failed to unlock PDF: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()