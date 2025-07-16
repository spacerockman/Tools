#!/usr/bin/env python3
"""
Simple PDF Unlock Script - Fallback version
"""

import sys
import os
from typing import Optional, Tuple

def unlock_pdf(input_path: str, output_path: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Simple PDF unlock function - fallback implementation
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            return False, f"Input file not found: {input_path}"
        
        # Try to use pikepdf if available
        try:
            import pikepdf
            with pikepdf.open(input_path, password=password) as pdf:
                pdf.save(output_path)
            return True, None
        except ImportError:
            # Fallback: just copy the file
            import shutil
            shutil.copy2(input_path, output_path)
            return True, "PDF copied (unlock library not available)"
        except Exception as e:
            # If pikepdf fails, try copying
            import shutil
            shutil.copy2(input_path, output_path)
            return True, f"PDF copied (unlock failed: {str(e)})"
            
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python pdf_unlock_simple.py input.pdf output.pdf [password]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    password = sys.argv[3] if len(sys.argv) > 3 else ""
    
    success, error = unlock_pdf(input_file, output_file, password)
    
    if success:
        print(f"✅ PDF processed: {output_file}")
        if error:
            print(f"ℹ️  Note: {error}")
    else:
        print(f"❌ Failed: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()