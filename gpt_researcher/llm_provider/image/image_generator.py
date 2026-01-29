"""Image generation provider for GPT Researcher.

This module provides image generation capabilities using Google's Gemini/Imagen
models via the google.genai SDK.

Supported models:
- Gemini image models (free tier): models/gemini-2.5-flash-image
- Imagen models (requires billing): imagen-4.0-generate-001
"""

import asyncio
import base64
import hashlib
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ImageGeneratorProvider:
    """Provider for generating images using Google's Gemini/Imagen models.
    
    Attributes:
        model_name: The model to use for image generation.
        api_key: Google API key for authentication.
        output_dir: Directory to save generated images.
    """
    
    # Gemini models use generate_content with inline_data response
    GEMINI_IMAGE_MODELS = [
        "models/gemini-2.5-flash-image",
        "gemini-2.5-flash-image",
        "gemini-2.0-flash-exp-image-generation",
        "gemini-3-pro-image-preview",
    ]
    
    # Imagen models use generate_images (requires billing)
    IMAGEN_MODELS = [
        "imagen-4.0-generate-001",
        "imagen-4.0-fast-generate-001",
        "imagen-4.0-ultra-generate-001",
    ]
    
    DEFAULT_MODEL = "models/gemini-2.5-flash-image"
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        output_dir: str = "outputs",
    ):
        """Initialize the ImageGeneratorProvider.
        
        Args:
            model_name: The model to use. Defaults to models/gemini-2.5-flash-image.
            api_key: Google API key. If not provided, reads from GOOGLE_API_KEY env var.
            output_dir: Base directory for outputs (images will be in output_dir/images/).
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.output_dir = Path(output_dir)
        self._client = None
        
        # Determine model type
        self._is_imagen = any(m in self.model_name.lower() for m in ['imagen'])
        
        if not self.api_key:
            logger.warning(
                "No Google API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY "
                "environment variable to enable image generation."
            )
    
    def _ensure_client(self):
        """Ensure the Google GenAI client is initialized."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized image generation with model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "google-genai package is required for image generation. "
                    "Install with: pip install google-genai"
                )
            except Exception as e:
                logger.error(f"Failed to initialize image generation client: {e}")
                raise
    
    def _ensure_output_dir(self, research_id: str = "") -> Path:
        """Ensure the output directory exists and return the path."""
        # Use same structure as PDF/DOCX: outputs/images/{research_id}/
        if research_id:
            output_path = self.output_dir / "images" / research_id
        else:
            output_path = self.output_dir / "images"
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def _generate_image_filename(self, prompt: str, index: int = 0) -> str:
        """Generate a unique filename for the image based on prompt hash."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"img_{prompt_hash}_{index}.png"
    
    def _crop_to_landscape(self, image_bytes: bytes, target_ratio: float = 16/9) -> bytes:
        """Crop a square image to landscape format (16:9 by default).
        
        This ensures images fit well in article/report layouts.
        
        Args:
            image_bytes: Raw image bytes.
            target_ratio: Target width/height ratio (default 16:9 ≈ 1.78).
            
        Returns:
            Cropped image bytes in PNG format.
        """
        try:
            from PIL import Image
            import io
            
            # Open the image
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            # If already landscape or wider, return as-is
            if width / height >= target_ratio:
                return image_bytes
            
            # Calculate new dimensions for landscape crop
            # Keep full width, reduce height
            new_height = int(width / target_ratio)
            
            # Center crop vertically
            top = (height - new_height) // 2
            bottom = top + new_height
            
            # Crop the image
            cropped = img.crop((0, top, width, bottom))
            
            # Save to bytes
            output = io.BytesIO()
            cropped.save(output, format='PNG', optimize=True)
            output.seek(0)
            
            logger.info(f"Cropped image from {width}x{height} to {width}x{new_height} (landscape)")
            return output.getvalue()
            
        except ImportError:
            logger.warning("PIL not available for image cropping, returning original")
            return image_bytes
        except Exception as e:
            logger.warning(f"Failed to crop image to landscape: {e}")
            return image_bytes
    
    def _build_enhanced_prompt(self, prompt: str, context: str = "", style: str = "dark") -> str:
        """Build an enhanced prompt with explicit styling instructions.
        
        Args:
            prompt: Base image prompt.
            context: Additional context from research.
            style: Image style - "dark" (matches app theme), "light", or "auto".
            
        Returns:
            Enhanced prompt string with styling instructions.
        """
        # Style-specific color palettes
        if style == "dark":
            # Dark mode matching the GPT Researcher app theme
            style_instructions = """
STYLE REQUIREMENTS - DARK MODE THEME:
- Dark background (#0d1117 or similar deep charcoal/navy)
- Primary accent color: Teal/Cyan (#14b8a6, #0d9488)
- Secondary colors: Slate grays (#374151, #4b5563), subtle purple accents
- Glowing, neon-like effects for highlights and important elements
- Modern, tech-forward, futuristic aesthetic
- Clean lines with subtle gradients
- High contrast elements that pop against dark background
- Sleek, minimalist design with visual depth
- Icons and diagrams with luminous teal outlines
- Professional infographic style suitable for tech/research context"""
        elif style == "light":
            style_instructions = """
STYLE REQUIREMENTS - LIGHT MODE:
- Clean white or light gray background
- Primary colors: Deep blue (#1e40af), teal (#0d9488)
- Professional, corporate aesthetic
- Subtle shadows for depth
- High readability with dark text elements
- Modern flat design with occasional gradients"""
        else:
            style_instructions = """
STYLE REQUIREMENTS - PROFESSIONAL:
- Sophisticated color palette (teals, blues, grays)
- Clean, modern design
- High contrast for readability
- Professional infographic style"""

        styled_prompt = f"""Create a professional, high-quality illustration for a research report.

SUBJECT: {prompt}

{style_instructions}

TECHNICAL REQUIREMENTS:
- No text, labels, or watermarks in the image
- Clear visual hierarchy
- Well-balanced composition
- Suitable for both digital viewing and printing
- Vector-style or clean photorealistic rendering
- Resolution and detail appropriate for report embedding

AVOID:
- Cartoonish or childish styles
- Cluttered or busy designs  
- Bright white backgrounds (for dark mode)
- Low quality or pixelated elements
- Generic stock photo aesthetics"""

        if context:
            styled_prompt += f"\n\nRESEARCH CONTEXT: {context[:300]}"
        
        return styled_prompt
    
    async def generate_image(
        self,
        prompt: str,
        context: str = "",
        research_id: str = "",
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        style: str = "dark",
    ) -> List[Dict[str, Any]]:
        """Generate images based on a prompt and optional context.
        
        Args:
            prompt: The image generation prompt.
            context: Additional context to improve image relevance.
            research_id: Research ID for organizing output.
            aspect_ratio: Aspect ratio for the image (Imagen only).
            num_images: Number of images to generate.
            style: Image style - "dark", "light", or "auto".
            
        Returns:
            List of dictionaries containing image info with absolute paths.
        """
        if not self.api_key:
            logger.warning("No API key configured for image generation")
            return []
        
        self._ensure_client()
        output_path = self._ensure_output_dir(research_id)
        
        # Build enhanced prompt with styling
        logger.info(f"Building image prompt with style: {style}")
        full_prompt = self._build_enhanced_prompt(prompt, context, style)
        logger.debug(f"Full prompt (first 500 chars): {full_prompt[:500]}")
        
        try:
            if self._is_imagen:
                return await self._generate_with_imagen(full_prompt, output_path, num_images, aspect_ratio, research_id)
            else:
                return await self._generate_with_gemini(full_prompt, output_path, num_images, research_id, prompt)
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            return []
    
    async def _generate_with_gemini(
        self,
        full_prompt: str,
        output_path: Path,
        num_images: int,
        research_id: str,
        original_prompt: str,
    ) -> List[Dict[str, Any]]:
        """Generate images using Gemini models via generate_content."""
        generated_images = []
        
        for i in range(num_images):
            try:
                # Gemini image models use generate_content
                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=self.model_name,
                    contents=full_prompt,
                )
                
                # Debug: Log response structure
                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        logger.debug(f"Response has {len(candidate.content.parts)} parts")
                        for idx, part in enumerate(candidate.content.parts):
                            has_inline = hasattr(part, 'inline_data') and part.inline_data
                            has_text = hasattr(part, 'text') and part.text
                            logger.debug(f"Part {idx}: inline_data={has_inline}, text={has_text}")
                
                # Extract image from response parts
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Found image data
                            image_data = part.inline_data.data
                            mime_type = getattr(part.inline_data, 'mime_type', 'image/png')
                            
                            # Determine file extension
                            ext = 'png' if 'png' in mime_type else 'jpg'
                            filename = self._generate_image_filename(original_prompt, i)
                            filepath = output_path / filename
                            
                            # Write image data (may be base64 encoded)
                            if isinstance(image_data, str):
                                image_bytes = base64.b64decode(image_data)
                            else:
                                image_bytes = image_data
                            
                            # Note: Keeping original square format from Gemini
                            # To enable landscape cropping, uncomment:
                            # image_bytes = self._crop_to_landscape(image_bytes)
                            
                            with open(filepath, 'wb') as f:
                                f.write(image_bytes)
                            
                            # Use both absolute path (for PDF) and web URL (for frontend)
                            absolute_path = filepath.resolve()
                            web_url = f"/outputs/images/{research_id}/{filename}" if research_id else f"/outputs/images/{filename}"
                            
                            generated_images.append({
                                "path": str(absolute_path),  # Absolute path for PDF generation
                                "url": web_url,  # Web URL for frontend display
                                "absolute_url": str(absolute_path),  # For PDF compatibility
                                "prompt": original_prompt,
                                "alt_text": self._generate_alt_text(original_prompt),
                            })
                            
                            logger.info(f"Generated image saved to: {filepath}")
                            break  # Only take first image per iteration
                    else:
                        # No inline_data found - check if there's text (model refused)
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'text') and part.text:
                                logger.warning(f"Model returned text instead of image: {part.text[:200]}")
                                break
                            
            except Exception as e:
                logger.error(f"Error generating image {i}: {e}", exc_info=True)
                continue
        
        return generated_images
    
    async def _generate_with_imagen(
        self,
        full_prompt: str,
        output_path: Path,
        num_images: int,
        aspect_ratio: str,
        research_id: str,
    ) -> List[Dict[str, Any]]:
        """Generate images using Imagen models via generate_images."""
        from google.genai import types
        
        generated_images = []
        
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_images,
                model=self.model_name,
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=num_images,
                    aspect_ratio=aspect_ratio,
                ),
            )
            
            if response and response.generated_images:
                for i, gen_image in enumerate(response.generated_images):
                    filename = self._generate_image_filename(full_prompt, i)
                    filepath = output_path / filename
                    
                    # Extract image bytes
                    if hasattr(gen_image, 'image') and hasattr(gen_image.image, 'image_bytes'):
                        image_bytes = gen_image.image.image_bytes
                    elif hasattr(gen_image, 'image_bytes'):
                        image_bytes = gen_image.image_bytes
                    else:
                        logger.warning("Could not extract image bytes")
                        continue
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                    
                    # Use both absolute path (for PDF) and web URL (for frontend)
                    absolute_path = filepath.resolve()
                    web_url = f"/outputs/images/{research_id}/{filename}" if research_id else f"/outputs/images/{filename}"
                    
                    generated_images.append({
                        "path": str(absolute_path),
                        "url": web_url,
                        "absolute_url": str(absolute_path),
                        "prompt": full_prompt,
                        "alt_text": self._generate_alt_text(full_prompt),
                    })
                    
                    logger.info(f"Generated image saved to: {filepath}")
                    
        except Exception as e:
            logger.error(f"Imagen generation failed: {e}", exc_info=True)
        
        return generated_images
    
    def _generate_alt_text(self, prompt: str) -> str:
        """Generate accessible alt text from the prompt."""
        # Clean and truncate for alt text
        clean_prompt = prompt.replace('\n', ' ').strip()
        # Extract just the core subject
        if len(clean_prompt) > 120:
            clean_prompt = clean_prompt[:117] + "..."
        return f"Illustration: {clean_prompt}"
    
    def is_available(self) -> bool:
        """Check if image generation is available."""
        if not self.api_key:
            return False
        try:
            self._ensure_client()
            return True
        except Exception as e:
            logger.warning(f"Image generation not available: {e}")
            return False
    
    @classmethod
    def from_config(cls, config) -> Optional["ImageGeneratorProvider"]:
        """Create an ImageGeneratorProvider from a Config object."""
        model = getattr(config, 'image_generation_model', None)
        enabled = getattr(config, 'image_generation_enabled', False)
        
        if not enabled:
            return None
        
        return cls(model_name=model or cls.DEFAULT_MODEL)
