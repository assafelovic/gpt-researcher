# Adding Features Guide

## Table of Contents
- [The 8-Step Pattern](#the-8-step-pattern)
- [Image Generation Case Study](#image-generation-case-study)
- [Testing New Features](#testing-new-features)

---

## The 8-Step Pattern

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│1.CONFIG│ →  │2.PROVIDER│ → │3.SKILL │ →  │4.AGENT │
└────────┘    └────────┘    └────────┘    └────────┘
     ↓             ↓             ↓             ↓
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│5.PROMPTS│ → │6.WEBSOCKET│→ │7.FRONTEND│→ │8.DOCS  │
└────────┘    └────────┘    └────────┘    └────────┘
```

### Step 1: Add Configuration

**File:** `gpt_researcher/config/variables/default.py`

```python
DEFAULT_CONFIG: BaseConfig = {
    "MY_FEATURE_ENABLED": False,
    "MY_FEATURE_MODEL": "model-name",
    "MY_FEATURE_MAX_ITEMS": 3,
}
```

**File:** `gpt_researcher/config/variables/base.py`

```python
class BaseConfig(TypedDict):
    "MY_FEATURE_ENABLED": bool
    "MY_FEATURE_MODEL": Union[str, None]
    "MY_FEATURE_MAX_ITEMS": int
```

### Step 2: Create Provider

**File:** `gpt_researcher/llm_provider/my_feature/my_provider.py`

```python
class MyFeatureProvider:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("MY_API_KEY")
        self.model = model
    
    def is_enabled(self) -> bool:
        return bool(self.api_key and self.model)
    
    async def execute(self, input_data: str) -> Dict[str, Any]:
        # API implementation
        pass
```

Export in `gpt_researcher/llm_provider/__init__.py`.

### Step 3: Create Skill

**File:** `gpt_researcher/skills/my_feature.py`

```python
class MyFeatureSkill:
    def __init__(self, researcher):
        self.researcher = researcher
        self.config = researcher.cfg
        self.provider = MyFeatureProvider(...)
    
    def is_enabled(self) -> bool:
        return getattr(self.config, 'my_feature_enabled', False) and self.provider.is_enabled()
    
    async def execute(self, context: str, query: str) -> List[Dict]:
        if not self.is_enabled():
            return []
        
        await stream_output("logs", "my_feature_start", "🚀 Starting...", self.researcher.websocket)
        results = await self.provider.execute(context)
        await stream_output("logs", "my_feature_complete", "✅ Done", self.researcher.websocket)
        
        return results
```

Export in `gpt_researcher/skills/__init__.py`.

### Step 4: Integrate into Agent

**File:** `gpt_researcher/agent.py`

```python
def __init__(self, ...):
    if self.cfg.my_feature_enabled:
        from gpt_researcher.skills import MyFeatureSkill
        self.my_feature = MyFeatureSkill(self)
    else:
        self.my_feature = None
    self.my_feature_results = []

async def conduct_research(self, ...):
    # ... existing ...
    if self.my_feature and self.my_feature.is_enabled():
        self.my_feature_results = await self.my_feature.execute(self.context, self.query)
```

### Step 5: Update Prompts

**File:** `gpt_researcher/prompts.py`

```python
@staticmethod
def generate_my_feature_prompt(context: str, query: str) -> str:
    return f"""..."""
```

### Step 6: WebSocket Events

Already handled via `stream_output()` in skill.

### Step 7: Frontend (if needed)

**File:** `frontend/nextjs/hooks/useWebSocket.ts`

```typescript
if (data.content === 'my_feature_start') {
    setStatus('processing');
}
```

### Step 8: Documentation

Create `docs/docs/gpt-researcher/gptr/my_feature.md`.

---

## Image Generation Case Study

This section shows the **actual implementation** of the Image Generation feature as a reference.

### 1. Configuration Added

**File:** `gpt_researcher/config/variables/default.py`

```python
DEFAULT_CONFIG: BaseConfig = {
    # ... existing ...
    "IMAGE_GENERATION_MODEL": "models/gemini-2.5-flash-image",
    "IMAGE_GENERATION_MAX_IMAGES": 3,
    "IMAGE_GENERATION_ENABLED": False,
    "IMAGE_GENERATION_STYLE": "dark",  # dark, light, auto
}
```

### 2. Provider Created

**File:** `gpt_researcher/llm_provider/image/image_generator.py`

```python
class ImageGeneratorProvider:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model or "models/gemini-2.5-flash-image"
        self._client = None
    
    def is_enabled(self) -> bool:
        return bool(self.api_key and self.model)
    
    def _build_enhanced_prompt(self, prompt: str, context: str = "", style: str = "dark") -> str:
        """Add styling instructions to prompt."""
        if style == "dark":
            style_instructions = """
            Style: Dark mode professional infographic
            - Background: Dark (#0d1117)
            - Accents: Teal/cyan (#14b8a6)
            - Clean, modern, minimalist
            """
        # ... handle light, auto
        return f"{style_instructions}\n\nCreate: {prompt}\n\nContext: {context}"
    
    async def generate_image(
        self,
        prompt: str,
        context: str = "",
        research_id: str = "",
        style: str = "dark",
    ) -> List[Dict[str, Any]]:
        """Generate image using Gemini."""
        full_prompt = self._build_enhanced_prompt(prompt, context, style)
        
        # Call Gemini API
        response = await self._generate_with_gemini(full_prompt, output_path, ...)
        
        return [{"url": f"/outputs/images/{research_id}/img_{hash}.png", ...}]
```

### 3. Skill Created

**File:** `gpt_researcher/skills/image_generator.py`

```python
class ImageGenerator:
    def __init__(self, researcher):
        self.researcher = researcher
        self.config = researcher.cfg
        self.image_provider = ImageGeneratorProvider(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=getattr(self.config, 'image_generation_model', None),
        )
        self.max_images = getattr(self.config, 'image_generation_max_images', 3)
        self.style = getattr(self.config, 'image_generation_style', 'dark')
    
    def is_enabled(self) -> bool:
        enabled = getattr(self.config, 'image_generation_enabled', False)
        return enabled and self.image_provider.is_enabled()
    
    async def plan_and_generate_images(
        self,
        research_context: str,
        research_query: str,
        research_id: str,
        websocket: Any,
    ) -> List[Dict[str, Any]]:
        """
        1. Use LLM to identify visual concepts from context
        2. Generate images in parallel
        3. Return list of image metadata
        """
        # Stream progress
        await stream_output("logs", "image_planning", "🎨 Planning images...", websocket)
        
        # LLM identifies concepts
        concepts = await self._plan_image_concepts(research_context, research_query)
        
        # Generate images in parallel
        generated_images = []
        for i, concept in enumerate(concepts[:self.max_images]):
            await stream_output("logs", "image_generating", 
                f"🖼️ Generating image {i+1}/{len(concepts)}...", websocket)
            
            images = await self.image_provider.generate_image(
                prompt=concept["prompt"],
                context=concept.get("context", ""),
                research_id=research_id,
                style=self.style,
            )
            generated_images.extend(images)
        
        await stream_output("logs", "images_ready", 
            f"✅ Generated {len(generated_images)} images", websocket)
        
        return generated_images
```

### 4. Agent Integration

**File:** `gpt_researcher/agent.py`

```python
class GPTResearcher:
    def __init__(self, ...):
        # ... existing init ...
        
        # Initialize image generator if enabled
        if self.cfg.image_generation_enabled:
            from gpt_researcher.skills import ImageGenerator
            self.image_generator = ImageGenerator(self)
        else:
            self.image_generator = None
        
        self.available_images: List[Dict[str, Any]] = []
        self.research_id = self._generate_research_id(query)
    
    async def conduct_research(self, on_progress=None):
        # ... existing research ...
        
        self.context = await self.research_conductor.conduct_research()
        
        # Pre-generate images after research, before report writing
        if self.cfg.image_generation_enabled and self.image_generator and self.image_generator.is_enabled():
            self.available_images = await self.image_generator.plan_and_generate_images(
                research_context=self.context,
                research_query=self.query,
                research_id=self.research_id,
                websocket=self.websocket,
            )
        
        return self.context
    
    async def write_report(self, ...):
        report = await self.report_generator.write_report(
            # ... existing params ...
            available_images=self.available_images,  # Pass to report writer
        )
        return report
```

### 5. Prompt Updated

**File:** `gpt_researcher/prompts.py`

```python
@staticmethod
def generate_report_prompt(..., available_images: List[Dict[str, Any]] = []):
    image_instruction = ""
    if available_images:
        image_list = "\n".join([
            f"- Title: {img.get('title', 'Untitled')}\n  URL: {img['url']}"
            for img in available_images
        ])
        image_instruction = f"""
AVAILABLE IMAGES - Embed where relevant using ![Title](URL):
{image_list}
"""
    
    return f"""...(existing prompt)...
{image_instruction}
"""
```

---

## Testing New Features

```python
# tests/test_my_feature.py
import pytest
from gpt_researcher import GPTResearcher

@pytest.mark.asyncio
async def test_my_feature_disabled():
    """Test that feature is skipped when disabled."""
    researcher = GPTResearcher(query="test")
    # MY_FEATURE_ENABLED defaults to False
    assert researcher.my_feature is None

@pytest.mark.asyncio
async def test_my_feature_enabled(monkeypatch):
    """Test feature execution when enabled."""
    monkeypatch.setenv("MY_FEATURE_ENABLED", "true")
    monkeypatch.setenv("MY_API_KEY", "test-key")
    
    researcher = GPTResearcher(query="test")
    assert researcher.my_feature is not None
    assert researcher.my_feature.is_enabled()
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test
python -m pytest tests/test_my_feature.py -v

# With coverage
python -m pytest tests/ --cov=gpt_researcher
```
