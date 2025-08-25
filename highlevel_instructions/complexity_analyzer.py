"""
Enhanced complexity analyzer with multi-dimensional analysis and adaptive recommendations
"""
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ComplexityDimension(Enum):
    """Enumeration of complexity dimensions"""
    CONTROVERSY = "controversy_level"
    PERSPECTIVES = "multiple_perspectives"
    LEGAL_CERTAINTY = "legal_certainty"
    NOVELTY = "novelty"
    TECHNICAL = "technical_complexity"
    SCOPE = "scope_breadth"
    DATA_AVAILABILITY = "data_availability"
    INTERDISCIPLINARY = "interdisciplinary_nature"
    TEMPORAL = "temporal_relevance"
    REGULATORY = "regulatory_complexity"


@dataclass
class ComplexityMetrics:
    """Data class for complexity metrics"""
    controversy_level: float = 5.0
    multiple_perspectives: float = 5.0
    legal_certainty: float = 5.0
    novelty: float = 5.0
    technical_complexity: float = 5.0
    scope_breadth: float = 5.0
    data_availability: float = 5.0
    interdisciplinary_nature: float = 5.0
    temporal_relevance: float = 5.0
    regulatory_complexity: float = 5.0
    overall_complexity: float = 5.0
    confidence_score: float = 0.5


@dataclass
class ResearchRecommendations:
    """Data class for research recommendations"""
    recommended_min_words: int
    recommended_max_words: int
    suggested_iterations: int
    special_attention_areas: List[str]
    recommended_report_type: str
    research_depth: str
    source_diversity_needed: str
    fact_checking_rigor: str
    rationale: str


class ComplexityAnalyzer:
    """Enhanced analyzer for topic complexity with adaptive recommendations."""

    def __init__(self, config):
        """
        Initialize the complexity analyzer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.cache = {}
        self.analysis_history = []

    async def analyze_complexity(
        self,
        query: str,
        context: Optional[List[str]] = None,
        force_analysis: bool = False,
        include_comparative: bool = True
    ) -> Dict[str, Any]:
        """
        Perform enhanced complexity analysis with caching and comparative analysis.
        
        Args:
            query: The research query
            context: Optional research context
            force_analysis: Force new analysis even if cached
            include_comparative: Include comparative complexity analysis
            
        Returns:
            Comprehensive complexity analysis with recommendations
        """
        # Check cache unless forced
        cache_key = self._generate_cache_key(query, context)
        if not force_analysis and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            cached_result['from_cache'] = True
            return cached_result

        # Check if complexity analysis is enabled
        if not self._is_complexity_analysis_enabled():
            return self._get_default_complexity()

        try:
            # Perform parallel analyses for comprehensive assessment
            analyses = await asyncio.gather(
                self._analyze_primary_complexity(query, context),
                self._analyze_domain_specifics(query) if include_comparative else self._get_empty_domain_analysis(),
                self._analyze_research_feasibility(query, context),
                return_exceptions=True
            )

            # Process results
            primary_analysis = analyses[0] if not isinstance(analyses[0], Exception) else {}
            domain_analysis = analyses[1] if not isinstance(analyses[1], Exception) else {}
            feasibility_analysis = analyses[2] if not isinstance(analyses[2], Exception) else {}

            # Combine analyses
            combined_result = self._combine_analyses(
                primary_analysis,
                domain_analysis,
                feasibility_analysis,
                query
            )

            # Cache the result
            self.cache[cache_key] = combined_result
            self.analysis_history.append({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'complexity': combined_result.get('overall_complexity', 5)
            })

            return combined_result

        except Exception as e:
            logger.error(f"Error in enhanced complexity analysis: {e}")
            return self._get_default_complexity()

    async def _analyze_primary_complexity(self, query: str, context: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze primary complexity dimensions."""
        try:
            from ..utils.llm import create_chat_completion

            analysis_prompt = self._create_enhanced_complexity_prompt(query, context)

            response = await create_chat_completion(
                model=self.config.smart_llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert research analyst specializing in topic complexity assessment and research planning."
                    },
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent analysis
                llm_provider=self.config.smart_llm_provider,
                max_tokens=1500,
                llm_kwargs=self.config.llm_kwargs,
            )

            # Parse and validate response
            complexity_data = json.loads(response)
            return self._validate_and_enhance_complexity_data(complexity_data)

        except Exception as e:
            logger.error(f"Primary complexity analysis failed: {e}")
            return {}

    async def _analyze_domain_specifics(self, query: str) -> Dict[str, Any]:
        """Analyze domain-specific complexity factors."""
        try:
            from ..utils.llm import create_chat_completion

            domain_prompt = f"""
Identify domain-specific complexity factors for this research topic:

Topic: {query}

Analyze:
1. Domain category (scientific, legal, business, social, technical, etc.)
2. Required expertise level (beginner, intermediate, expert, specialist)
3. Typical research challenges in this domain
4. Data/source availability in this domain
5. Common methodological approaches

Respond in JSON format:
{{
    "domain_category": "category",
    "expertise_required": "level",
    "domain_challenges": ["challenge1", "challenge2"],
    "data_availability": "high/medium/low",
    "methodological_considerations": ["consideration1", "consideration2"]
}}
"""

            response = await create_chat_completion(
                model=self.config.fast_llm_model,  # Use faster model for domain analysis
                messages=[
                    {"role": "system", "content": "You are a domain classification expert."},
                    {"role": "user", "content": domain_prompt}
                ],
                temperature=0.3,
                llm_provider=self.config.fast_llm_provider,
                max_tokens=500,
                llm_kwargs=self.config.llm_kwargs,
            )

            return json.loads(response)

        except Exception as e:
            logger.error(f"Domain analysis failed: {e}")
            return self._get_empty_domain_analysis()

    async def _analyze_research_feasibility(self, query: str, context: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze research feasibility and resource requirements."""
        try:
            # Estimate based on query characteristics
            query_length = len(query.split())
            has_specific_terms = any(term in query.lower() for term in [
                'specific', 'detailed', 'comprehensive', 'in-depth', 'thorough'
            ])
            has_comparative = any(term in query.lower() for term in [
                'compare', 'versus', 'vs', 'difference', 'contrast'
            ])
            has_temporal = any(term in query.lower() for term in [
                'history', 'evolution', 'timeline', 'development', 'future'
            ])

            # Calculate feasibility scores
            scope_score = min(10, query_length * 0.5 + (5 if has_specific_terms else 0))
            research_depth = 'deep' if has_specific_terms else 'standard'
            time_requirement = 'extended' if has_temporal else 'normal'

            return {
                'scope_score': scope_score,
                'research_depth': research_depth,
                'time_requirement': time_requirement,
                'requires_comparison': has_comparative,
                'requires_historical': has_temporal,
                'estimated_sources_needed': 10 + int(scope_score * 2)
            }

        except Exception as e:
            logger.error(f"Feasibility analysis failed: {e}")
            return {}

    def _create_enhanced_complexity_prompt(self, query: str, context: Optional[List[str]]) -> str:
        """Create enhanced prompt for complexity analysis."""
        context_text = "\n".join(context[:5]) if context else "No additional context provided."

        return f"""
Analyze the complexity of this research topic comprehensively:

Topic: {query}

Context Preview: {context_text}

Evaluate these enhanced dimensions (0-10 scale):

CORE COMPLEXITY FACTORS:
1. Controversy level: Degree of debate, disagreement, or conflicting viewpoints
2. Multiple perspectives: Number of distinct stakeholder views or theoretical frameworks
3. Legal/Regulatory certainty: Clarity and stability of applicable laws/regulations (10 = very clear)
4. Novelty: How emerging or cutting-edge the topic is
5. Technical complexity: Level of specialized knowledge required

ADDITIONAL FACTORS:
6. Scope breadth: How broad vs. narrow the topic is
7. Data availability: Ease of finding reliable sources (10 = abundant sources)
8. Interdisciplinary nature: Degree of cross-field knowledge required
9. Temporal relevance: Time-sensitivity or historical span required
10. Regulatory complexity: Intricacy of compliance/regulatory aspects

RECOMMENDATIONS:
Based on your analysis, provide:
- Word count range (considering complexity)
- Number of research iterations needed
- Critical areas requiring special attention
- Suggested research methodology
- Fact-checking rigor level needed

Respond in this exact JSON format:
{{
    "controversy_level": 0-10,
    "multiple_perspectives": 0-10,
    "legal_certainty": 0-10,
    "novelty": 0-10,
    "technical_complexity": 0-10,
    "scope_breadth": 0-10,
    "data_availability": 0-10,
    "interdisciplinary_nature": 0-10,
    "temporal_relevance": 0-10,
    "regulatory_complexity": 0-10,
    "overall_complexity": 0-10,
    "confidence_score": 0-1,
    "recommended_min_words": number,
    "recommended_max_words": number,
    "suggested_iterations": number,
    "special_attention_areas": ["area1", "area2", "area3"],
    "recommended_methodology": "qualitative/quantitative/mixed",
    "fact_checking_rigor": "standard/enhanced/maximum",
    "rationale": "Detailed explanation of the complexity assessment and recommendations"
}}
"""

    def _validate_and_enhance_complexity_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate, normalize, and enhance complexity data."""
        # Create metrics object
        metrics = ComplexityMetrics()

        # Update metrics with provided data
        for field in metrics.__dataclass_fields__:
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    # Normalize to 0-10 range
                    normalized = max(0, min(10, value))
                    setattr(metrics, field, normalized)

        # Calculate overall complexity if not provided
        if 'overall_complexity' not in data or data['overall_complexity'] == 5:
            metrics.overall_complexity = self._calculate_overall_complexity(metrics)

        # Calculate confidence score based on data completeness
        provided_fields = sum(1 for f in metrics.__dataclass_fields__ if f in data)
        total_fields = len(metrics.__dataclass_fields__)
        metrics.confidence_score = provided_fields / total_fields

        # Create recommendations based on complexity
        recommendations = self._generate_recommendations(metrics, data)

        # Combine metrics and recommendations
        result = asdict(metrics)
        result.update(asdict(recommendations))

        # Add additional metadata
        result['analysis_timestamp'] = datetime.now().isoformat()
        result['analysis_version'] = '2.0'

        return result

    def _calculate_overall_complexity(self, metrics: ComplexityMetrics) -> float:
        """Calculate weighted overall complexity score."""
        weights = {
            'controversy_level': 0.15,
            'multiple_perspectives': 0.15,
            'technical_complexity': 0.20,
            'scope_breadth': 0.10,
            'data_availability': 0.10,  # Inverted - low availability = high complexity
            'interdisciplinary_nature': 0.10,
            'novelty': 0.10,
            'regulatory_complexity': 0.10
        }

        weighted_sum = 0
        for field, weight in weights.items():
            value = getattr(metrics, field, 5)
            # Invert data_availability (high availability = low complexity)
            if field == 'data_availability':
                value = 10 - value
            weighted_sum += value * weight

        return round(weighted_sum, 1)

    def _generate_recommendations(self, metrics: ComplexityMetrics, raw_data: Dict) -> ResearchRecommendations:
        """Generate adaptive recommendations based on complexity metrics."""
        overall = metrics.overall_complexity

        # Adaptive word count based on complexity
        if overall < 3:
            min_words, max_words = 800, 1500
        elif overall < 5:
            min_words, max_words = 1500, 3000
        elif overall < 7:
            min_words, max_words = 2500, 5000
        else:
            min_words, max_words = 4000, 8000

        # Override with provided values if valid
        if 'recommended_min_words' in raw_data:
            min_words = max(500, min(10000, raw_data['recommended_min_words']))
        if 'recommended_max_words' in raw_data:
            max_words = max(min_words + 500, min(15000, raw_data['recommended_max_words']))

        # Adaptive iterations based on complexity factors
        iterations = 1
        if metrics.controversy_level > 7 or metrics.multiple_perspectives > 7:
            iterations += 1
        if metrics.scope_breadth > 7:
            iterations += 1
        if metrics.technical_complexity > 8:
            iterations += 1
        iterations = min(5, max(1, raw_data.get('suggested_iterations', iterations)))

        # Special attention areas
        attention_areas = raw_data.get('special_attention_areas', [])
        if not attention_areas:
            attention_areas = self._identify_attention_areas(metrics)

        # Determine report type and depth
        if metrics.technical_complexity > 7:
            report_type = 'technical_report'
            research_depth = 'deep'
        elif metrics.controversy_level > 7:
            report_type = 'analytical_report'
            research_depth = 'comprehensive'
        else:
            report_type = 'standard_report'
            research_depth = 'standard'

        # Source diversity requirements
        if metrics.multiple_perspectives > 7:
            source_diversity = 'maximum'
        elif metrics.multiple_perspectives > 5:
            source_diversity = 'high'
        else:
            source_diversity = 'standard'

        # Fact-checking rigor
        fact_checking = raw_data.get('fact_checking_rigor', 'standard')
        if metrics.controversy_level > 7 or metrics.regulatory_complexity > 7:
            fact_checking = 'maximum'
        elif overall > 6:
            fact_checking = 'enhanced'

        return ResearchRecommendations(
            recommended_min_words=min_words,
            recommended_max_words=max_words,
            suggested_iterations=iterations,
            special_attention_areas=attention_areas,
            recommended_report_type=report_type,
            research_depth=research_depth,
            source_diversity_needed=source_diversity,
            fact_checking_rigor=fact_checking,
            rationale=raw_data.get('rationale', self._generate_rationale(metrics))
        )

    def _identify_attention_areas(self, metrics: ComplexityMetrics) -> List[str]:
        """Identify areas needing special attention based on metrics."""
        areas = []

        if metrics.controversy_level > 7:
            areas.append("Balanced representation of conflicting viewpoints")
        if metrics.technical_complexity > 7:
            areas.append("Technical accuracy and expert validation")
        if metrics.regulatory_complexity > 7:
            areas.append("Regulatory compliance and legal accuracy")
        if metrics.multiple_perspectives > 7:
            areas.append("Stakeholder perspective mapping")
        if metrics.data_availability < 3:
            areas.append("Limited source availability - require thorough search")
        if metrics.novelty > 7:
            areas.append("Emerging topic - verify cutting-edge information")
        if metrics.temporal_relevance > 7:
            areas.append("Historical context and timeline accuracy")

        return areas[:5]  # Limit to top 5 areas

    def _generate_rationale(self, metrics: ComplexityMetrics) -> str:
        """Generate explanation for the complexity assessment."""
        overall = metrics.overall_complexity

        if overall < 3:
            level = "low complexity"
            approach = "straightforward research approach"
        elif overall < 5:
            level = "moderate complexity"
            approach = "balanced research approach"
        elif overall < 7:
            level = "substantial complexity"
            approach = "comprehensive research approach"
        else:
            level = "high complexity"
            approach = "intensive research approach"

        factors = []
        if metrics.controversy_level > 7:
            factors.append("high controversy")
        if metrics.technical_complexity > 7:
            factors.append("technical depth")
        if metrics.scope_breadth > 7:
            factors.append("broad scope")

        factor_text = f" due to {', '.join(factors)}" if factors else ""

        return f"This topic exhibits {level}{factor_text}, requiring a {approach} with careful attention to accuracy and completeness."

    def _combine_analyses(
        self,
        primary: Dict,
        domain: Dict,
        feasibility: Dict,
        query: str
    ) -> Dict[str, Any]:
        """Combine multiple analyses into comprehensive result."""
        combined = primary.copy() if primary else self._get_default_complexity()

        # Enhance with domain analysis
        if domain:
            combined['domain_analysis'] = domain

        # Enhance with feasibility analysis
        if feasibility:
            combined['feasibility_analysis'] = feasibility
            # Adjust recommendations based on feasibility
            if feasibility.get('requires_comparison'):
                combined['suggested_iterations'] = max(2, combined.get('suggested_iterations', 1))
            if feasibility.get('requires_historical'):
                combined['recommended_max_words'] = max(3000, combined.get('recommended_max_words', 2000))

        # Add query metadata
        combined['query'] = query
        combined['query_word_count'] = len(query.split())

        return combined

    def _is_complexity_analysis_enabled(self) -> bool:
        """Check if complexity analysis is enabled in configuration."""
        complexity_factors = getattr(self.config, 'complexity_factors', {})
        return complexity_factors.get('controversy_detection', False) or \
               complexity_factors.get('enable_complexity_analysis', False)

    def _generate_cache_key(self, query: str, context: Optional[List[str]]) -> str:
        """Generate cache key for complexity analysis."""
        context_str = str(context[:3]) if context else ""
        return f"{query}:{context_str}"

    def _get_empty_domain_analysis(self) -> Dict[str, Any]:
        """Return empty domain analysis structure."""
        return {
            "domain_category": "general",
            "expertise_required": "intermediate",
            "domain_challenges": [],
            "data_availability": "medium",
            "methodological_considerations": []
        }

    def _get_default_complexity(self) -> Dict[str, Any]:
        """Return enhanced default complexity analysis."""
        metrics = ComplexityMetrics()
        recommendations = ResearchRecommendations(
            recommended_min_words=getattr(self.config, 'total_words', 2000),
            recommended_max_words=getattr(self.config, 'total_words', 2000) * 2,
            suggested_iterations=1,
            special_attention_areas=[],
            recommended_report_type='standard_report',
            research_depth='standard',
            source_diversity_needed='standard',
            fact_checking_rigor='standard',
            rationale="Default complexity assessment - analysis disabled or failed"
        )

        result = asdict(metrics)
        result.update(asdict(recommendations))
        result['analysis_timestamp'] = datetime.now().isoformat()
        result['analysis_version'] = '2.0'
        result['from_cache'] = False

        return result

    def get_complexity_history(self) -> List[Dict]:
        """Get history of complexity analyses performed."""
        return self.analysis_history

    def clear_cache(self):
        """Clear the complexity analysis cache."""
        self.cache.clear()
        logger.info("Complexity analysis cache cleared")