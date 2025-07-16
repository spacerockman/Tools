#!/usr/bin/env python3
"""
Fallback PDF Watermark Remover
Works with basic libraries when PyMuPDF/pikepdf have compatibility issues
"""

import sys
import os
import re
import tempfile
from typing import Optional, Tuple, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FallbackWatermarkRemover:
    """Fallback watermark removal using text processing and PDF stream manipulation"""
    
    def __init__(self):
        self.common_watermark_patterns = [
            rb'watermark',
            rb'confidential',
            rb'draft',
            rb'sample',
            rb'preview',
            rb'demo',
            rb'trial',
            rb'evaluation',
            rb'copyright',
            rb'proprietary',
            rb'internal use',
            rb'not for distribution',
            rb'www\.',
            rb'\.com',
            rb'\.org',
            rb'\.net'
        ]
    
    def remove_watermarks(self, input_path: str, output_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Remove watermarks using fallback method
        """
        try:
            stats = {
                'text_watermarks_removed': 0,
                'image_watermarks_removed': 0,
                'transparent_objects_removed': 0,
                'background_objects_removed': 0,
                'total_pages_processed': 0,
                'techniques_used': ['Fallback Text Processing']
            }
            
            # Try to process PDF content streams
            success, error = self._process_pdf_streams(input_path, output_path, stats)
            
            if success:
                logger.info(f"Fallback watermark removal completed. Stats: {stats}")
                return True, None, stats
            else:
                # If processing fails, just copy the file
                import shutil
                shutil.copy2(input_path, output_path)
                stats['techniques_used'] = ['File Copy (No Processing)']
                return True, "Watermark removal skipped - using original file", stats
                
        except Exception as e:
            logger.error(f"Fallback watermark removal failed: {str(e)}")
            # Last resort - copy the original file
            try:
                import shutil
                shutil.copy2(input_path, output_path)
                return True, f"Watermark removal failed, using original file: {str(e)}", {}
            except Exception as copy_error:
                return False, f"Complete failure: {str(copy_error)}", {}
    
    def _process_pdf_streams(self, input_path: str, output_path: str, stats: Dict) -> Tuple[bool, Optional[str]]:
        """Process PDF content streams to remove watermarks (SAFE MODE)"""
        try:
            with open(input_path, 'rb') as input_file:
                pdf_content = input_file.read()
            
            # Basic PDF structure validation
            if not pdf_content.startswith(b'%PDF-'):
                return False, "Not a valid PDF file"
            
            # Validate PDF structure before processing
            if not self._validate_pdf_structure(pdf_content):
                logger.warning("PDF structure validation failed - copying original file")
                import shutil
                shutil.copy2(input_path, output_path)
                return True, "PDF structure complex - watermark removal skipped for safety"
            
            # Process content streams safely
            modified_content = self._clean_pdf_content(pdf_content, stats)
            
            # Validate the modified content
            if not self._validate_pdf_structure(modified_content):
                logger.warning("Modified PDF failed validation - using original file")
                import shutil
                shutil.copy2(input_path, output_path)
                return True, "Watermark removal would damage PDF - using original file"
            
            # Write cleaned content
            with open(output_path, 'wb') as output_file:
                output_file.write(modified_content)
            
            return True, None
            
        except Exception as e:
            logger.error(f"PDF stream processing failed: {str(e)} - copying original file")
            try:
                import shutil
                shutil.copy2(input_path, output_path)
                return True, f"Processing failed, using original file: {str(e)}"
            except Exception as copy_error:
                return False, f"Complete failure: {str(copy_error)}"
    
    def _clean_pdf_content(self, content: bytes, stats: Dict) -> bytes:
        """Clean PDF content by removing watermark-related elements (SAFE MODE)"""
        modified_content = content
        
        try:
            # SAFE MODE: Only remove obvious text watermarks in content streams
            # Don't modify PDF structure or critical elements
            
            # Only look for watermarks in content streams (between 'stream' and 'endstream')
            stream_pattern = rb'stream\s*\n(.*?)\nendstream'
            
            def clean_stream_content(match):
                stream_content = match.group(1)
                original_content = stream_content
                
                # Only remove obvious watermark text patterns from text content
                for pattern in self.common_watermark_patterns:
                    # Only remove if it's clearly text content (has Tj or TJ operators)
                    if b'Tj' in stream_content or b'TJ' in stream_content:
                        # Look for the pattern in parentheses (PDF text strings)
                        text_pattern = rb'\(' + pattern + rb'\)'
                        matches = re.findall(text_pattern, stream_content, re.IGNORECASE)
                        if matches:
                            # Replace only the text content, keep the operators
                            stream_content = re.sub(text_pattern, b'()', stream_content, flags=re.IGNORECASE)
                            stats['text_watermarks_removed'] += len(matches)
                            logger.info(f"Safely removed {len(matches)} text watermarks: {pattern}")
                
                return b'stream\n' + stream_content + b'\nendstream'
            
            # Apply safe cleaning only to content streams
            modified_content = re.sub(stream_pattern, clean_stream_content, modified_content, flags=re.DOTALL)
            
            # Count pages processed (rough estimate)
            page_count = len(re.findall(rb'/Type\s*/Page\b', modified_content))
            stats['total_pages_processed'] = max(1, page_count)
            
            # If no changes were made, return original content
            if modified_content == content:
                logger.info("No watermarks found or removed - PDF unchanged")
            
        except Exception as e:
            logger.warning(f"Content cleaning error: {str(e)} - returning original content")
            return content  # Return original if any error occurs
        
        return modified_content
    
    def _is_suspicious_xobject_content(self, xobject_content: bytes) -> bool:
        """Check if XObject content might be a watermark"""
        try:
            # Look for small images or forms that might be watermarks
            if b'/Subtype/Image' in xobject_content:
                # Check for small dimensions (likely watermarks)
                width_match = re.search(rb'/Width\s+(\d+)', xobject_content)
                height_match = re.search(rb'/Height\s+(\d+)', xobject_content)
                
                if width_match and height_match:
                    width = int(width_match.group(1))
                    height = int(height_match.group(1))
                    
                    # Very small or very large images might be watermarks
                    if (width < 100 and height < 100) or (width > 2000 or height > 2000):
                        return True
            
            # Check for Form XObjects (often used for watermarks)
            if b'/Subtype/Form' in xobject_content:
                return True
                
        except Exception:
            pass
        
        return False
    
    def _validate_pdf_structure(self, content: bytes) -> bool:
        """Validate basic PDF structure to ensure file integrity"""
        try:
            # Check PDF header
            if not content.startswith(b'%PDF-'):
                return False
            
            # Check for PDF trailer
            if b'trailer' not in content:
                return False
            
            # Check for xref table
            if b'xref' not in content:
                return False
            
            # Check for EOF marker
            if not content.rstrip().endswith(b'%%EOF'):
                return False
            
            # Check for basic PDF objects
            required_patterns = [
                rb'/Type\s*/Catalog',  # Document catalog
                rb'/Type\s*/Pages',    # Pages object
            ]
            
            for pattern in required_patterns:
                if not re.search(pattern, content):
                    logger.warning(f"Missing required PDF structure: {pattern}")
                    return False
            
            # Check that we don't have corrupted object references
            # Look for malformed object definitions
            obj_pattern = rb'\d+\s+\d+\s+obj'
            endobj_pattern = rb'endobj'
            
            obj_count = len(re.findall(obj_pattern, content))
            endobj_count = len(re.findall(endobj_pattern, content))
            
            # Should have matching obj/endobj pairs
            if abs(obj_count - endobj_count) > 2:  # Allow small discrepancy
                logger.warning(f"Mismatched obj/endobj pairs: {obj_count} vs {endobj_count}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"PDF validation error: {str(e)}")
            return False


def remove_watermarks(input_path: str, output_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Main function to remove watermarks from PDF using safe fallback method
    """
    # For now, use SAFE MODE by default to prevent file corruption
    # Advanced libraries can be enabled later when compatibility is confirmed
    
    logger.info("Using SAFE MODE watermark remover to prevent file corruption")
    remover = FallbackWatermarkRemover()
    
    try:
        success, error, stats = remover.remove_watermarks(input_path, output_path)
        
        # Always verify the output file is valid
        if success and os.path.exists(output_path):
            # Quick validation of output file
            try:
                with open(output_path, 'rb') as f:
                    output_content = f.read(1024)  # Read first 1KB
                    if not output_content.startswith(b'%PDF-'):
                        logger.error("Output file is not a valid PDF - using original")
                        import shutil
                        shutil.copy2(input_path, output_path)
                        return True, "Watermark removal failed validation - using original file", {}
            except Exception as e:
                logger.error(f"Output validation failed: {str(e)} - using original")
                import shutil
                shutil.copy2(input_path, output_path)
                return True, f"Output validation failed - using original file: {str(e)}", {}
        
        return success, error, stats
        
    except Exception as e:
        # Last resort - just copy the original file
        logger.error(f"All watermark removal failed: {str(e)} - copying original file")
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            return True, f"Watermark removal failed, using original file: {str(e)}", {'techniques_used': ['File Copy Only']}
        except Exception as copy_error:
            return False, f"Complete failure: {str(copy_error)}", {}


def main():
    """Command line interface for fallback watermark removal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fallback PDF watermark remover')
    parser.add_argument('input', help='Input PDF file')
    parser.add_argument('output', help='Output PDF file (watermarks removed)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    print(f"Removing watermarks from {args.input} (fallback method)...")
    success, error, stats = remove_watermarks(args.input, args.output)
    
    if success:
        print(f"✅ Processing completed!")
        print(f"📁 Output saved to: {args.output}")
        if error:
            print(f"⚠️  Note: {error}")
        print(f"📊 Processing Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Processing failed: {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()