"""
Translation Tool - OCR and translate text from camera

Uses EasyOCR for text extraction and Google Translate for translation.
"""

import cv2
import logging
import numpy as np
from typing import Dict, Optional
import easyocr
from googletrans import Translator

logger = logging.getLogger(__name__)


class TranslationTool:
    """Tool for OCR and translation from camera snapshots."""
    
    def __init__(self):
        """Initialize translation tool."""
        self.camera_manager = None  # Will be set by orchestrator
        self.reader = None  # Lazy load EasyOCR
        self.translator = Translator()
        logger.info("Translation Tool initialized")
    
    def _get_reader(self):
        """Lazy load EasyOCR reader."""
        if self.reader is None:
            logger.info("Loading EasyOCR reader (this may take a moment)...")
            self.reader = easyocr.Reader(['en'], gpu=False)  # English by default
            logger.info("✅ EasyOCR reader loaded")
        return self.reader
    
    async def extract_text(self, image) -> Dict:
        """
        Extract text from image using EasyOCR.
        
        Args:
            image: numpy array (OpenCV format)
            
        Returns:
            Dictionary with success status and extracted text
        """
        try:
            reader = self._get_reader()
            
            # EasyOCR expects RGB, OpenCV uses BGR
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extract text
            logger.info("Extracting text from image...")
            results = reader.readtext(rgb_image)
            
            if not results:
                return {
                    "success": False,
                    "error": "No text detected in the image"
                }
            
            # Combine all detected text
            extracted_text = " ".join([text for (bbox, text, prob) in results])
            
            logger.info(f"✅ Extracted text: {extracted_text[:100]}...")
            
            return {
                "success": True,
                "text": extracted_text,
                "confidence": sum([prob for (_, _, prob) in results]) / len(results)
            }
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def translate_text(self, text: str, target_lang: str = "es") -> Dict:
        """
        Translate text using Google Translate.
        
        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'es', 'fr', 'de')
            
        Returns:
            Dictionary with success status and translated text
        """
        try:
            logger.info(f"Translating to {target_lang}...")
            
            # Translate (googletrans 4.0.2 is async)
            translation = await self.translator.translate(text, dest=target_lang)
            
            logger.info(f"✅ Translation: {translation.text[:100]}...")
            
            return {
                "success": True,
                "original": text,
                "translated": translation.text,
                "source_lang": translation.src,
                "target_lang": target_lang
            }
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def translate_from_camera(self, target_lang: str = "es") -> Dict:
        """
        Complete workflow: capture, OCR, translate.
        
        Args:
            target_lang: Target language code
            
        Returns:
            Dictionary with success status and translation result
        """
        try:
            from agents.camera_manager import CameraManager
            
            # Get camera frame
            if self.camera_manager is None:
                self.camera_manager = CameraManager()
            
            frame = self.camera_manager.get_frame()
            
            if frame is None:
                return {
                    "success": False,
                    "error": "Could not capture camera frame"
                }
            
            # Extract text
            ocr_result = await self.extract_text(frame)
            
            if not ocr_result.get("success"):
                return ocr_result
            
            # Translate (async in googletrans 4.0.2)
            translation_result = await self.translate_text(
                ocr_result["text"],
                target_lang
            )
            
            if not translation_result.get("success"):
                return translation_result
            
            # Combine results
            return {
                "success": True,
                "original_text": ocr_result["text"],
                "translated_text": translation_result["translated"],
                "source_lang": translation_result["source_lang"],
                "target_lang": target_lang,
                "confidence": ocr_result.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error in translation workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_translation_response(self, result: Dict) -> str:
        """Format translation result into natural language response."""
        if not result.get('success'):
            return f"I'm sorry, I couldn't translate the text. {result.get('error', '')}"
        
        original = result.get('original_text', '')
        translated = result.get('translated_text', '')
        target_lang = result.get('target_lang', 'target language')
        
        # Language name mapping (expanded)
        lang_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ja': 'Japanese',
            'zh-cn': 'Chinese',
            'zh': 'Chinese',
            'ko': 'Korean',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish'
        }
        
        lang_name = lang_names.get(target_lang, target_lang)
        
        if original:
            response = f"I detected the text: '{original[:100]}{'...' if len(original) > 100 else ''}'. "
        else:
            response = "I detected some text. "
        
        response += f"In {lang_name}, it says: '{translated}'"
        
        return response
