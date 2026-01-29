"""Image generator skill for GPT Researcher.

This module provides the ImageGenerator class that handles generating
contextually relevant images for research reports using AI image generation.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ..actions.utils import stream_output
from ..llm_provider.image import ImageGeneratorProvider
from ..utils.llm import create_chat_completion

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates contextually relevant images for research reports.
    
    This class analyzes report content to identify sections that would
    benefit from visual illustrations and generates images using AI
    image generation models.
    
    Attributes:
        researcher: The parent GPTResearcher instance.
        image_provider: The image generation provider.
        max_images: Maximum number of images to generate per report.
    """
    
    def __init__(self, researcher):
        """Initialize the ImageGenerator.
        
        Args:
            researcher: The GPTResearcher instance that owns this generator.
        """
        self.researcher = researcher
        self.cfg = researcher.cfg
        self.image_provider = None
        self.max_images = getattr(self.cfg, 'image_generation_max_images', 3)
        self.generated_images: List[Dict[str, Any]] = []
        
        # Initialize image provider if configured
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the image generation provider from config."""
        model = getattr(self.cfg, 'image_generation_model', None)
        enabled = getattr(self.cfg, 'image_generation_enabled', False)
        
        if model and enabled:
            try:
                self.image_provider = ImageGeneratorProvider(model_name=model)
                if self.image_provider.is_available():
                    logger.info(f"Image generation enabled with model: {model}")
                else:
                    logger.warning("Image generation provider not available (missing API key?)")
                    self.image_provider = None
            except Exception as e:
                logger.error(f"Failed to initialize image provider: {e}")
                self.image_provider = None
    
    def is_enabled(self) -> bool:
        """Check if image generation is enabled and available.
        
        Returns:
            True if image generation can be used.
        """
        return self.image_provider is not None and self.image_provider.is_available()

    async def plan_and_generate_images(
        self,
        context: str,
        query: str,
        research_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Plan and pre-generate images based on research context.
        
        This method analyzes the research context to identify 2-3 concepts
        that would benefit from visual illustrations, then generates them
        in parallel BEFORE report writing begins.
        
        Args:
            context: The accumulated research context.
            query: The main research query.
            research_id: Optional research ID for file organization.
            
        Returns:
            List of generated image info dictionaries with URLs ready to embed.
        """
        if not self.is_enabled():
            logger.info("Image generation is not enabled, skipping pre-generation")
            return []
        
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "image_planning",
                "🎨 Analyzing research context for visualization opportunities...",
                self.researcher.websocket,
            )
        
        # Step 1: Use LLM to identify best visualization opportunities
        image_concepts = await self._plan_image_concepts(context, query)
        
        if not image_concepts:
            logger.info("No suitable visualization opportunities identified")
            return []
        
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "image_concepts_identified",
                f"🖼️ Identified {len(image_concepts)} visualization concepts, generating images...",
                self.researcher.websocket,
            )
        
        # Step 2: Generate all images in parallel
        image_style = getattr(self.cfg, 'image_generation_style', 'dark')
        
        async def generate_single_image(concept: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
            """Generate a single image from a concept."""
            try:
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "image_generating",
                        f"🖼️ Generating image {index + 1}/{len(image_concepts)}: {concept['title'][:50]}...",
                        self.researcher.websocket,
                    )
                
                images = await self.image_provider.generate_image(
                    prompt=concept['prompt'],
                    context=concept.get('context', ''),
                    research_id=research_id,
                    num_images=1,
                    style=image_style,
                )
                
                if images:
                    image_info = images[0]
                    image_info['title'] = concept['title']
                    image_info['section_hint'] = concept.get('section_hint', '')
                    return image_info
                    
            except Exception as e:
                logger.error(f"Failed to generate image for '{concept['title']}': {e}")
            return None
        
        # Generate all images in parallel
        tasks = [generate_single_image(concept, i) for i, concept in enumerate(image_concepts)]
        results = await asyncio.gather(*tasks)
        
        # Filter out failed generations
        generated_images = [img for img in results if img is not None]
        self.generated_images = generated_images
        
        if self.researcher.verbose:
            if generated_images:
                await stream_output(
                    "logs",
                    "images_ready",
                    f"✅ {len(generated_images)} images ready for report embedding",
                    self.researcher.websocket,
                )
            else:
                await stream_output(
                    "logs",
                    "images_failed",
                    "⚠️ No images could be generated",
                    self.researcher.websocket,
                )
        
        return generated_images

    async def _plan_image_concepts(
        self,
        context: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Use LLM to identify the best visualization opportunities from research context.
        
        Args:
            context: The research context to analyze.
            query: The main research query.
            
        Returns:
            List of image concept dictionaries with title, prompt, and section_hint.
        """
        # Truncate context if too long
        max_context_length = 6000
        truncated_context = context[:max_context_length] if len(context) > max_context_length else context
        
        planning_prompt = f"""Analyze this research context and identify 2-3 concepts that would significantly benefit from professional diagram/infographic illustrations.

RESEARCH QUERY: {query}

RESEARCH CONTEXT:
{truncated_context}

For each visualization opportunity, provide:
1. title: A short descriptive title (e.g., "System Architecture", "Comparison Chart")
2. prompt: A detailed image generation prompt describing exactly what to visualize, including layout and key elements (minimum 30 words)
3. section_hint: Which section of the report this image relates to

Focus on:
- Architecture/system diagrams
- Process flows and workflows
- Comparison charts
- Data visualizations
- Conceptual illustrations

IMPORTANT: Return ONLY a valid JSON array. No markdown, no explanation.

Example output:
[
  {{
    "title": "System Architecture Overview",
    "prompt": "A layered architecture diagram showing the frontend application on top, connecting to an API gateway in the middle, which routes to microservices at the bottom. Use clean boxes with connecting arrows, modern tech aesthetic.",
    "section_hint": "Architecture"
  }}
]

Return 2-3 visualization concepts as a JSON array:"""

        try:
            response = await create_chat_completion(
                model=self.cfg.fast_llm_model,
                messages=[
                    {"role": "system", "content": "You are a visualization expert. Return only valid JSON arrays."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.4,
                llm_provider=self.cfg.fast_llm_provider,
                max_tokens=1000,
                llm_kwargs=self.cfg.llm_kwargs,
                cost_callback=self.researcher.add_costs,
            )
            
            # Parse JSON response
            response = response.strip()
            # Remove markdown code blocks if present
            if response.startswith("```"):
                response = re.sub(r'^```(?:json)?\n?', '', response)
                response = re.sub(r'\n?```$', '', response)
            
            concepts = json.loads(response)
            
            # Validate and limit to max_images
            valid_concepts = []
            for concept in concepts[:self.max_images]:
                if isinstance(concept, dict) and 'title' in concept and 'prompt' in concept:
                    valid_concepts.append(concept)
            
            logger.info(f"Planned {len(valid_concepts)} image concepts")
            return valid_concepts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse image planning response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during image planning: {e}")
            return []

    async def analyze_report_for_images(
        self,
        report: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Analyze a report to identify sections that would benefit from images.
        
        Uses LLM to identify 2-3 key concepts or sections in the report
        that would be enhanced by visual illustrations.
        
        Args:
            report: The markdown report text.
            query: The original research query.
            
        Returns:
            List of dictionaries with section info and suggested image prompts.
        """
        if not self.is_enabled():
            return []
        
        # Extract sections from the report
        sections = self._extract_sections(report)
        
        if not sections:
            logger.warning("No sections found in report for image analysis")
            return []
        
        # Use LLM to identify best sections for images
        try:
            analysis_prompt = self._build_analysis_prompt(query, sections)
            
            response = await create_chat_completion(
                model=self.cfg.fast_llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying content that would benefit from visual illustrations."},
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.3,
                llm_provider=self.cfg.fast_llm_provider,
                stream=False,
                websocket=None,
                max_tokens=1500,
                llm_kwargs=self.cfg.llm_kwargs,
            )
            
            # Parse the response
            image_suggestions = self._parse_analysis_response(response, sections)
            return image_suggestions[:self.max_images]
            
        except Exception as e:
            logger.error(f"Error analyzing report for images: {e}")
            return []
    
    def _extract_sections(self, report: str) -> List[Dict[str, Any]]:
        """Extract sections from a markdown report.
        
        Args:
            report: The markdown report text.
            
        Returns:
            List of section dictionaries with header, content, and position.
        """
        sections = []
        lines = report.split('\n')
        current_section = None
        current_content = []
        section_start = 0
        
        for i, line in enumerate(lines):
            # Check for headers (## or ###)
            header_match = re.match(r'^(#{2,3})\s+(.+)$', line)
            
            if header_match:
                # Save previous section
                if current_section:
                    sections.append({
                        "header": current_section,
                        "content": '\n'.join(current_content).strip(),
                        "start_line": section_start,
                        "end_line": i - 1,
                    })
                
                # Start new section
                current_section = header_match.group(2)
                current_content = []
                section_start = i
            elif current_section:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            sections.append({
                "header": current_section,
                "content": '\n'.join(current_content).strip(),
                "start_line": section_start,
                "end_line": len(lines) - 1,
            })
        
        return sections
    
    def _build_analysis_prompt(
        self,
        query: str,
        sections: List[Dict[str, Any]],
    ) -> str:
        """Build prompt for LLM to analyze which sections need images.
        
        Args:
            query: The research query.
            sections: List of extracted sections.
            
        Returns:
            The analysis prompt string.
        """
        sections_text = "\n\n".join([
            f"### Section {i+1}: {s['header']}\n{s['content'][:500]}..."
            for i, s in enumerate(sections)
        ])
        
        return f"""Analyze the following research report sections and identify which {self.max_images} sections would benefit MOST from a visual illustration or diagram.

RESEARCH TOPIC: {query}

REPORT SECTIONS:
{sections_text}

For each recommended section, provide:
1. The section number (1-indexed)
2. A specific, detailed image prompt that would create an informative illustration
3. A brief explanation of why this section benefits from visualization

IMPORTANT:
- Choose sections where visual representation would genuinely aid understanding
- Focus on concepts, processes, comparisons, or data that are inherently visual
- Avoid sections that are purely textual analysis or conclusions
- The image prompt should be specific enough to generate a relevant, professional illustration
- Do NOT suggest images for introduction or conclusion sections

Respond in JSON format:
{{
    "suggestions": [
        {{
            "section_number": 1,
            "section_header": "Section Title",
            "image_prompt": "Detailed prompt for generating an informative illustration...",
            "reason": "Why this section benefits from visualization"
        }}
    ]
}}

Return ONLY the JSON, no additional text."""
    
    def _parse_analysis_response(
        self,
        response: str,
        sections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Parse the LLM's analysis response.
        
        Args:
            response: The LLM response text.
            sections: The original sections list.
            
        Returns:
            List of image suggestion dictionaries.
        """
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning("No JSON found in analysis response")
                return []
            
            data = json.loads(json_match.group())
            suggestions = data.get("suggestions", [])
            
            # Enrich with section data
            enriched = []
            for s in suggestions:
                section_num = s.get("section_number", 0) - 1  # Convert to 0-indexed
                if 0 <= section_num < len(sections):
                    section = sections[section_num]
                    enriched.append({
                        "section_header": section["header"],
                        "section_content": section["content"][:1000],
                        "image_prompt": s.get("image_prompt", ""),
                        "reason": s.get("reason", ""),
                        "insert_after_line": section["start_line"],
                    })
            
            return enriched
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis JSON: {e}")
            return []
    
    async def generate_images_for_report(
        self,
        report: str,
        query: str,
        research_id: str = "",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate images and embed them in the report.
        
        This is the main method that orchestrates the full image generation
        workflow for a research report.
        
        Args:
            report: The markdown report text.
            query: The original research query.
            research_id: Optional research ID for file organization.
            
        Returns:
            Tuple of (modified report with embedded images, list of generated images).
        """
        if not self.is_enabled():
            logger.info("Image generation is not enabled, skipping")
            return report, []
        
        # Notify about image generation starting
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "image_generation_start",
                "🎨 Analyzing report for image generation opportunities...",
                self.researcher.websocket,
            )
        
        # Analyze report for image opportunities
        suggestions = await self.analyze_report_for_images(report, query)
        
        if not suggestions:
            logger.info("No sections identified for image generation")
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "image_generation_skip",
                    "📝 No sections identified that would benefit from images",
                    self.researcher.websocket,
                )
            return report, []
        
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "image_generation_analyzing",
                f"🔍 Found {len(suggestions)} sections that would benefit from images",
                self.researcher.websocket,
            )
        
        # Generate images for each suggestion
        generated_images = []
        for i, suggestion in enumerate(suggestions):
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "image_generating",
                    f"🖼️ Generating image {i+1}/{len(suggestions)}: {suggestion['section_header'][:50]}...",
                    self.researcher.websocket,
                )
            
            try:
                images = await self.image_provider.generate_image(
                    prompt=suggestion["image_prompt"],
                    context=suggestion["section_content"],
                    research_id=research_id,
                    num_images=1,
                )
                
                if images:
                    image_info = images[0]
                    image_info["section_header"] = suggestion["section_header"]
                    generated_images.append(image_info)
                    
                    if self.researcher.verbose:
                        await stream_output(
                            "logs",
                            "image_generated",
                            f"✅ Image generated for: {suggestion['section_header'][:50]}",
                            self.researcher.websocket,
                        )
            except Exception as e:
                logger.error(f"Failed to generate image for section '{suggestion['section_header']}': {e}")
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "image_generation_error",
                        f"⚠️ Failed to generate image: {str(e)[:100]}",
                        self.researcher.websocket,
                    )
        
        # Embed images in the report
        if generated_images:
            report = self._embed_images_in_report(report, generated_images, suggestions)
            self.generated_images = generated_images
            
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "image_generation_complete",
                    f"🎉 Successfully generated and embedded {len(generated_images)} images",
                    self.researcher.websocket,
                )
                
                # Send generated images through WebSocket
                await stream_output(
                    "generated_images",
                    "inline_images",
                    json.dumps([{"url": img["url"], "alt": img["alt_text"]} for img in generated_images]),
                    self.researcher.websocket,
                    True,
                    generated_images,
                )
        
        return report, generated_images
    
    def _embed_images_in_report(
        self,
        report: str,
        images: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]],
    ) -> str:
        """Embed generated images into the report markdown.
        
        Args:
            report: The original report markdown.
            images: List of generated image info.
            suggestions: Original suggestions with section info.
            
        Returns:
            Modified report with embedded images.
        """
        lines = report.split('\n')
        
        # Create a mapping of section headers to images
        section_to_image = {}
        for img, sug in zip(images, suggestions):
            section_to_image[sug["section_header"]] = img
        
        # Find section headers and insert images after them
        modified_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            modified_lines.append(line)
            
            # Check if this is a header that needs an image
            header_match = re.match(r'^(#{2,3})\s+(.+)$', line)
            if header_match:
                header_text = header_match.group(2)
                if header_text in section_to_image:
                    img = section_to_image[header_text]
                    # Insert image after the header with a blank line
                    image_markdown = f"\n![{img['alt_text']}]({img['url']})\n"
                    modified_lines.append(image_markdown)
            
            i += 1
        
        return '\n'.join(modified_lines)
    
    def get_generated_images(self) -> List[Dict[str, Any]]:
        """Get the list of generated images.
        
        Returns:
            List of generated image info dictionaries.
        """
        return self.generated_images

    async def process_image_placeholders(
        self,
        report: str,
        query: str,
        research_id: str = "",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process [IMAGE: description] placeholders in the report and generate images.
        
        This method finds all image placeholders in the report, generates images
        for each one, and replaces the placeholders with actual markdown images.
        
        Args:
            report: The markdown report text with [IMAGE: ...] placeholders.
            query: The original research query (used for context).
            research_id: Optional research ID for file organization.
            
        Returns:
            Tuple of (modified report with images embedded, list of generated images).
        """
        if not self.is_enabled():
            # If image generation is not enabled, just remove the placeholders
            report = re.sub(r'\[IMAGE:\s*[^\]]+\]', '', report)
            return report, []
        
        # Find all image placeholders
        placeholder_pattern = r'\[IMAGE:\s*([^\]]+)\]'
        placeholders = list(re.finditer(placeholder_pattern, report))
        
        if not placeholders:
            logger.info("No image placeholders found in report")
            return report, []
        
        # Limit to max_images
        placeholders = placeholders[:self.max_images]
        
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "image_placeholders_found",
                f"🎨 Found {len(placeholders)} image placeholders to process",
                self.researcher.websocket,
            )
        
        generated_images = []
        replacements = []  # List of (original_text, replacement_text) tuples
        
        for i, match in enumerate(placeholders):
            image_description = match.group(1).strip()
            original_text = match.group(0)
            
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "image_generating",
                    f"🖼️ Generating image {i+1}/{len(placeholders)}: {image_description[:60]}...",
                    self.researcher.websocket,
                )
            
            try:
                # Get image style from config (default to "dark" for app theme)
                image_style = getattr(self.cfg, 'image_generation_style', 'dark')
                logger.info(f"Using image style: {image_style}")
                
                # Generate the image with dark mode styling
                images = await self.image_provider.generate_image(
                    prompt=image_description,
                    context=query,  # Use query as context
                    research_id=research_id,
                    num_images=1,
                    style=image_style,
                )
                
                if images:
                    image_info = images[0]
                    image_info["description"] = image_description
                    generated_images.append(image_info)
                    
                    # Create markdown replacement with absolute path for PDF compatibility
                    # Use the absolute URL for proper rendering in PDF/DOCX
                    markdown_image = f"\n\n![{image_info['alt_text']}]({image_info['url']})\n\n"
                    replacements.append((original_text, markdown_image))
                    
                    if self.researcher.verbose:
                        await stream_output(
                            "logs",
                            "image_generated",
                            f"✅ Generated: {image_description[:40]}...",
                            self.researcher.websocket,
                        )
                else:
                    # Remove placeholder if image generation failed
                    replacements.append((original_text, ""))
                    logger.warning(f"No image generated for: {image_description[:50]}")
                    
            except Exception as e:
                logger.error(f"Failed to generate image for '{image_description[:50]}': {e}")
                # Remove the failed placeholder
                replacements.append((original_text, ""))
                
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "image_generation_error",
                        f"⚠️ Failed to generate: {str(e)[:80]}",
                        self.researcher.websocket,
                    )
        
        # Apply all replacements
        modified_report = report
        for original, replacement in replacements:
            modified_report = modified_report.replace(original, replacement, 1)
        
        self.generated_images = generated_images
        
        if generated_images and self.researcher.verbose:
            await stream_output(
                "logs",
                "image_generation_complete",
                f"🎉 Successfully generated {len(generated_images)} inline images",
                self.researcher.websocket,
            )
            
            # Send generated images through WebSocket
            await stream_output(
                "generated_images",
                "inline_images",
                json.dumps([{"url": img["url"], "alt": img["alt_text"]} for img in generated_images]),
                self.researcher.websocket,
                True,
                generated_images,
            )
        
        return modified_report, generated_images
