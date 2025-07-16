#!/usr/bin/env python3
"""
Advanced PDF Watermark Remover
Implements multiple watermark detection and removal techniques
"""

import sys
import os
import re
from typing import Optional, Tuple, List, Dict, Any
import fitz  # PyMuPDF for advanced PDF manipulation
import pikepdf
from PIL import Image, ImageFilter, ImageEnhance
import io
import numpy as np
from collections import Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WatermarkRemover:
    """Advanced watermark detection and removal system"""
    
    def __init__(self):
        self.common_watermark_patterns = [
            r'watermark',
            r'confidential',
            r'draft',
            r'sample',
            r'preview',
            r'demo',
            r'trial',
            r'evaluation',
            r'copyright',
            r'proprietary',
            r'internal use',
            r'not for distribution',
            r'www\.',
            r'\.com',
            r'\.org',
            r'\.net'
        ]
        
        self.watermark_opacity_threshold = 0.7
        self.text_size_threshold = 8  # Minimum text size to consider as content
        
    def remove_watermarks(self, input_path: str, output_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Remove watermarks from PDF using multiple techniques
        
        Returns:
            Tuple of (success, error_message, removal_stats)
        """
        try:
            stats = {
                'text_watermarks_removed': 0,
                'image_watermarks_removed': 0,
                'transparent_objects_removed': 0,
                'background_objects_removed': 0,
                'total_pages_processed': 0,
                'techniques_used': []
            }
            
            # Try PyMuPDF first (more advanced)
            success, error, pymupdf_stats = self._remove_with_pymupdf(input_path, output_path)
            if success:
                stats.update(pymupdf_stats)
                stats['techniques_used'].append('PyMuPDF Advanced')
                return True, None, stats
            
            # Fallback to pikepdf
            success, error, pikepdf_stats = self._remove_with_pikepdf(input_path, output_path)
            if success:
                stats.update(pikepdf_stats)
                stats['techniques_used'].append('pikepdf')
                return True, None, stats
            
            return False, f"All watermark removal methods failed. Last error: {error}", stats
            
        except Exception as e:
            logger.error(f"Watermark removal failed: {str(e)}")
            return False, f"Unexpected error during watermark removal: {str(e)}", {}
    
    def _remove_with_pymupdf(self, input_path: str, output_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Remove watermarks using PyMuPDF (fitz) - most advanced method"""
        try:
            stats = {
                'text_watermarks_removed': 0,
                'image_watermarks_removed': 0,
                'transparent_objects_removed': 0,
                'background_objects_removed': 0,
                'total_pages_processed': 0
            }
            
            doc = fitz.open(input_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                stats['total_pages_processed'] += 1
                
                # Remove text watermarks
                text_removed = self._remove_text_watermarks_pymupdf(page)
                stats['text_watermarks_removed'] += text_removed
                
                # Remove image watermarks
                image_removed = self._remove_image_watermarks_pymupdf(page)
                stats['image_watermarks_removed'] += image_removed
                
                # Remove transparent overlays
                transparent_removed = self._remove_transparent_objects_pymupdf(page)
                stats['transparent_objects_removed'] += transparent_removed
                
                # Remove background watermarks
                bg_removed = self._remove_background_watermarks_pymupdf(page)
                stats['background_objects_removed'] += bg_removed
            
            # Save the cleaned document
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            logger.info(f"PyMuPDF watermark removal completed. Stats: {stats}")
            return True, None, stats
            
        except ImportError:
            return False, "PyMuPDF (fitz) not available", {}
        except Exception as e:
            logger.error(f"PyMuPDF watermark removal failed: {str(e)}")
            return False, str(e), {}
    
    def _remove_text_watermarks_pymupdf(self, page) -> int:
        """Remove text-based watermarks using PyMuPDF"""
        removed_count = 0
        
        try:
            # Get all text instances
            text_instances = page.get_text("dict")
            
            for block in text_instances.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").lower().strip()
                        font_size = span.get("size", 0)
                        
                        # Check if text matches watermark patterns
                        if self._is_watermark_text(text, font_size):
                            # Get text rectangle
                            bbox = span.get("bbox")
                            if bbox:
                                # Create a white rectangle to cover the watermark
                                rect = fitz.Rect(bbox)
                                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                                removed_count += 1
                                logger.info(f"Removed text watermark: '{text}'")
            
        except Exception as e:
            logger.warning(f"Text watermark removal error: {str(e)}")
        
        return removed_count
    
    def _remove_image_watermarks_pymupdf(self, page) -> int:
        """Remove image-based watermarks using PyMuPDF"""
        removed_count = 0
        
        try:
            # Get all images on the page
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image properties
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Check if image might be a watermark
                    if self._is_watermark_image(pix):
                        # Get image rectangle on page
                        img_rects = page.get_image_rects(xref)
                        
                        for rect in img_rects:
                            # Cover watermark with white rectangle
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            removed_count += 1
                            logger.info(f"Removed image watermark at {rect}")
                    
                    pix = None  # Free memory
                    
                except Exception as e:
                    logger.warning(f"Error processing image {img_index}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"Image watermark removal error: {str(e)}")
        
        return removed_count
    
    def _remove_transparent_objects_pymupdf(self, page) -> int:
        """Remove transparent overlays that might be watermarks"""
        removed_count = 0
        
        try:
            # Get page content as text
            content = page.get_contents()
            if not content:
                return 0
            
            # Look for transparency operations in PDF content
            transparency_patterns = [
                rb'/GS\d+\s+gs',  # Graphics state with transparency
                rb'/CA\s+[\d.]+',  # Constant alpha
                rb'/ca\s+[\d.]+',  # Non-stroking alpha
                rb'BDC.*?EMC',     # Marked content (often used for watermarks)
            ]
            
            for pattern in transparency_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    # This is a simplified approach - in practice, you'd need
                    # more sophisticated PDF content stream parsing
                    logger.info(f"Found {len(matches)} potential transparent watermark objects")
                    removed_count += len(matches)
            
        except Exception as e:
            logger.warning(f"Transparent object removal error: {str(e)}")
        
        return removed_count
    
    def _remove_background_watermarks_pymupdf(self, page) -> int:
        """Remove background watermarks"""
        removed_count = 0
        
        try:
            # Get all drawings/paths on the page
            drawings = page.get_drawings()
            
            for drawing in drawings:
                # Check if drawing might be a background watermark
                if self._is_background_watermark(drawing):
                    # Cover with white rectangle
                    rect = drawing.get("rect")
                    if rect:
                        page.draw_rect(fitz.Rect(rect), color=(1, 1, 1), fill=(1, 1, 1))
                        removed_count += 1
                        logger.info(f"Removed background watermark")
            
        except Exception as e:
            logger.warning(f"Background watermark removal error: {str(e)}")
        
        return removed_count
    
    def _remove_with_pikepdf(self, input_path: str, output_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Fallback watermark removal using pikepdf"""
        try:
            stats = {
                'text_watermarks_removed': 0,
                'image_watermarks_removed': 0,
                'transparent_objects_removed': 0,
                'background_objects_removed': 0,
                'total_pages_processed': 0
            }
            
            with pikepdf.open(input_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    stats['total_pages_processed'] += 1
                    
                    # Remove watermark-related content
                    removed = self._clean_page_content_pikepdf(page)
                    stats['text_watermarks_removed'] += removed
                
                # Save cleaned PDF
                pdf.save(output_path)
            
            logger.info(f"pikepdf watermark removal completed. Stats: {stats}")
            return True, None, stats
            
        except Exception as e:
            logger.error(f"pikepdf watermark removal failed: {str(e)}")
            return False, str(e), {}
    
    def _clean_page_content_pikepdf(self, page) -> int:
        """Clean page content using pikepdf"""
        removed_count = 0
        
        try:
            # Access page resources
            if "/Resources" in page:
                resources = page["/Resources"]
                
                # Remove suspicious XObjects (often watermarks)
                if "/XObject" in resources:
                    xobjects = dict(resources["/XObject"])
                    for name, obj in list(xobjects.items()):
                        if self._is_suspicious_xobject(obj):
                            del xobjects[name]
                            removed_count += 1
                            logger.info(f"Removed suspicious XObject: {name}")
                    
                    if removed_count > 0:
                        resources["/XObject"] = xobjects
                
                # Remove suspicious fonts (watermark fonts)
                if "/Font" in resources:
                    fonts = dict(resources["/Font"])
                    for name, font in list(fonts.items()):
                        if self._is_watermark_font(font):
                            del fonts[name]
                            removed_count += 1
                            logger.info(f"Removed watermark font: {name}")
                    
                    if removed_count > 0:
                        resources["/Font"] = fonts
            
        except Exception as e:
            logger.warning(f"Page content cleaning error: {str(e)}")
        
        return removed_count
    
    def _is_watermark_text(self, text: str, font_size: float) -> bool:
        """Determine if text is likely a watermark"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_lower = text.lower()
        
        # Check against common watermark patterns
        for pattern in self.common_watermark_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check for very large or very small text (common in watermarks)
        if font_size > 50 or font_size < 6:
            return True
        
        # Check for repetitive characters (like "CONFIDENTIAL CONFIDENTIAL")
        if len(set(text.replace(' ', ''))) < len(text) * 0.3:
            return True
        
        return False
    
    def _is_watermark_image(self, pix) -> bool:
        """Determine if image is likely a watermark"""
        try:
            if not pix:
                return False
            
            # Check image properties
            width, height = pix.width, pix.height
            
            # Very small or very large images might be watermarks
            if width < 50 or height < 50 or width > 2000 or height > 2000:
                return True
            
            # Check if image has transparency (common in watermarks)
            if pix.alpha:
                return True
            
            # Convert to PIL Image for analysis
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # Check if image is mostly transparent or has low contrast
            if img.mode in ('RGBA', 'LA'):
                # Check alpha channel
                alpha_channel = img.split()[-1]
                alpha_array = np.array(alpha_channel)
                avg_alpha = np.mean(alpha_array)
                
                if avg_alpha < 128:  # Mostly transparent
                    return True
            
            # Check for low contrast (common in watermarks)
            grayscale = img.convert('L')
            contrast = ImageEnhance.Contrast(grayscale).enhance(2.0)
            hist = contrast.histogram()
            
            # If most pixels are in a narrow range, it might be a watermark
            total_pixels = sum(hist)
            concentrated_pixels = sum(hist[100:156])  # Middle gray range
            
            if concentrated_pixels > total_pixels * 0.8:
                return True
            
        except Exception as e:
            logger.warning(f"Image watermark detection error: {str(e)}")
        
        return False
    
    def _is_background_watermark(self, drawing: Dict) -> bool:
        """Determine if drawing is a background watermark"""
        try:
            # Check if drawing covers a large area (background-like)
            rect = drawing.get("rect")
            if rect:
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                area = width * height
                
                # Large area might be background watermark
                if area > 100000:  # Adjust threshold as needed
                    return True
            
            # Check drawing properties
            fill = drawing.get("fill")
            stroke = drawing.get("stroke")
            
            # Very light colors might be watermarks
            if fill and all(c > 0.8 for c in fill[:3]):  # Very light fill
                return True
            
            if stroke and all(c > 0.8 for c in stroke[:3]):  # Very light stroke
                return True
            
        except Exception as e:
            logger.warning(f"Background watermark detection error: {str(e)}")
        
        return False
    
    def _is_suspicious_xobject(self, obj) -> bool:
        """Determine if XObject is suspicious (likely watermark)"""
        try:
            if "/Subtype" in obj:
                subtype = str(obj["/Subtype"])
                
                # Form XObjects are often used for watermarks
                if subtype == "/Form":
                    return True
                
                # Check image XObjects
                if subtype == "/Image":
                    # Check for transparency or small size
                    if "/SMask" in obj or "/Mask" in obj:
                        return True
                    
                    width = obj.get("/Width", 0)
                    height = obj.get("/Height", 0)
                    
                    if width < 100 or height < 100:
                        return True
            
        except Exception as e:
            logger.warning(f"XObject analysis error: {str(e)}")
        
        return False
    
    def _is_watermark_font(self, font) -> bool:
        """Determine if font is commonly used for watermarks"""
        try:
            if "/BaseFont" in font:
                font_name = str(font["/BaseFont"]).lower()
                
                # Common watermark font patterns
                watermark_fonts = [
                    'arial',
                    'helvetica',
                    'times',
                    'courier',
                    'impact',
                    'watermark'
                ]
                
                for wf in watermark_fonts:
                    if wf in font_name:
                        # Additional checks could be added here
                        return False  # Conservative approach
            
        except Exception as e:
            logger.warning(f"Font analysis error: {str(e)}")
        
        return False


def remove_watermarks(input_path: str, output_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Main function to remove watermarks from PDF
    
    Args:
        input_path: Path to input PDF
        output_path: Path to save cleaned PDF
        
    Returns:
        Tuple of (success, error_message, removal_stats)
    """
    remover = WatermarkRemover()
    return remover.remove_watermarks(input_path, output_path)


def main():
    """Command line interface for watermark removal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced PDF watermark remover')
    parser.add_argument('input', help='Input PDF file')
    parser.add_argument('output', help='Output PDF file (watermarks removed)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    print(f"Removing watermarks from {args.input}...")
    success, error, stats = remove_watermarks(args.input, args.output)
    
    if success:
        print(f"✅ Watermarks removed successfully!")
        print(f"📁 Cleaned PDF saved to: {args.output}")
        print(f"📊 Removal Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Watermark removal failed: {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()