"""
Enhanced dual curation system with multi-stage quality assessment and intelligent filtering
"""
import logging
from typing import List, Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class CurationStrategy(Enum):
    """Curation strategy types"""
    RELEVANCE_FIRST = "relevance_first"  # Primary: relevance, Secondary: quality
    QUALITY_FIRST = "quality_first"  # Primary: quality, Secondary: relevance
    BALANCED = "balanced"  # Equal weight to both
    STRICT = "strict"  # Must pass both with high scores
    ADAPTIVE = "adaptive"  # Adjust based on source availability


@dataclass
class SourceMetadata:
    """Metadata for source evaluation"""
    source_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    relevance_score: float = 0.0
    quality_score: float = 0.0
    credibility_score: float = 0.0
    freshness_score: float = 0.0
    diversity_score: float = 0.0
    combined_score: float = 0.0
    curation_stage: str = "uncurated"
    timestamp: datetime = field(default_factory=datetime.now)
    rejection_reason: Optional[str] = None
    curator_notes: List[str] = field(default_factory=list)


class DualCuratorManager:
    """Enhanced dual curation manager with comprehensive source assessment."""

    def __init__(self, researcher, strategy: CurationStrategy = CurationStrategy.BALANCED):
        """
        Initialize the dual curator manager.
        
        Args:
            researcher: The GPTResearcher instance
            strategy: Curation strategy to use
        """
        self.researcher = researcher
        self.primary_curator = researcher.source_curator  # Existing curator
        self.secondary_curator = None
        self.strategy = strategy
        self.curation_history: List[Dict] = []
        self.source_metadata: Dict[str, SourceMetadata] = {}
        self.quality_thresholds = self._initialize_thresholds()

    def _initialize_thresholds(self) -> Dict[str, float]:
        """Initialize quality thresholds based on strategy."""
        if self.strategy == CurationStrategy.STRICT:
            return {
                'relevance': 0.7,
                'quality': 0.7,
                'credibility': 0.6,
                'freshness': 0.5,
                'combined': 0.7
            }
        elif self.strategy == CurationStrategy.BALANCED:
            return {
                'relevance': 0.6,
                'quality': 0.5,
                'credibility': 0.5,
                'freshness': 0.4,
                'combined': 0.55
            }
        else:  # Adaptive or custom strategies
            return {
                'relevance': 0.5,
                'quality': 0.4,
                'credibility': 0.4,
                'freshness': 0.3,
                'combined': 0.45
            }

    async def curate_sources(
        self,
        research_data: List[Any],
        min_sources: int = 3,
        max_sources: Optional[int] = None,
        custom_criteria: Optional[Dict] = None
    ) -> List[Any]:
        """
        Apply enhanced dual curation with comprehensive quality assessment.
        
        Args:
            research_data: Raw research data
            min_sources: Minimum number of sources to retain
            max_sources: Maximum number of sources to retain
            custom_criteria: Custom curation criteria
            
        Returns:
            Curated research data after multi-stage curation
        """
        if not research_data:
            return []

        # Check if dual curation is enabled
        if not getattr(self.researcher.cfg, 'dual_curation', False):
            # Single curation fallback
            return await self._single_curation(research_data)

        try:
            # Initialize metadata for all sources
            self._initialize_source_metadata(research_data)

            # Stage 1: Primary curation (relevance-based)
            stage1_results = await self._primary_curation_stage(research_data)

            # Stage 2: Secondary curation (quality-based)
            stage2_results = await self._secondary_curation_stage(stage1_results)

            # Stage 3: Diversity and balance optimization
            stage3_results = await self._diversity_optimization_stage(stage2_results)

            # Stage 4: Final selection based on strategy
            final_results = await self._final_selection_stage(
                stage3_results,
                min_sources,
                max_sources,
                custom_criteria
            )

            # Log curation statistics
            self._log_curation_statistics(research_data, final_results)

            return final_results

        except Exception as e:
            logger.error(f"Error in enhanced dual curation: {e}")
            # Fallback to simple curation
            return await self._single_curation(research_data)

    async def _single_curation(self, research_data: List[Any]) -> List[Any]:
        """Fallback single curation when dual curation is disabled or fails."""
        try:
            return await self.primary_curator.curate_sources(research_data)
        except:
            # Ultimate fallback - return top N sources
            return research_data[:min(10, len(research_data))]

    async def _primary_curation_stage(self, sources: List[Any]) -> List[Any]:
        """
        Primary curation stage focusing on relevance.
        
        Args:
            sources: Input sources
            
        Returns:
            Sources passing primary curation
        """
        if self.researcher.verbose:
            await self._stream_output(
                "first_curation_start",
                f"🔍 Starting primary curation of {len(sources)} sources..."
            )

        # Use existing primary curator
        curated = await self.primary_curator.curate_sources(sources)

        # Update metadata with relevance scores
        for source in curated:
            source_id = self._get_source_id(source)
            if source_id in self.source_metadata:
                # Estimate relevance score based on curation result
                self.source_metadata[source_id].relevance_score = 0.7  # Base score for passing
                self.source_metadata[source_id].curation_stage = "primary_passed"

        if self.researcher.verbose:
            await self._stream_output(
                "first_curation_complete",
                f"✅ Primary curation complete: {len(sources)} → {len(curated)} sources"
            )

        return curated

    async def _secondary_curation_stage(self, sources: List[Any]) -> List[Any]:
        """
        Secondary curation stage focusing on quality and credibility.
        
        Args:
            sources: Sources from primary curation
            
        Returns:
            Sources passing secondary curation
        """
        if not sources:
            return []

        if self.researcher.verbose:
            await self._stream_output(
                "second_curation_start",
                f"🎯 Starting secondary quality assessment of {len(sources)} sources..."
            )

        # Apply secondary curator if available
        if self.secondary_curator:
            curated = await self._apply_secondary_curator(sources)
        else:
            # Apply built-in quality assessment
            curated = await self._apply_quality_assessment(sources)

        # Update metadata
        for source in curated:
            source_id = self._get_source_id(source)
            if source_id in self.source_metadata:
                self.source_metadata[source_id].curation_stage = "secondary_passed"

        if self.researcher.verbose:
            await self._stream_output(
                "second_curation_complete",
                f"✅ Secondary curation complete: {len(sources)} → {len(curated)} sources"
            )

        return curated

    async def _apply_secondary_curator(self, sources: List[Any]) -> List[Any]:
        """Apply external secondary curator if configured."""
        try:
            if hasattr(self.secondary_curator, 'curate_sources'):
                return await self.secondary_curator.curate_sources(sources)
            elif callable(self.secondary_curator):
                return await self.secondary_curator(sources)
            else:
                logger.warning("Secondary curator not callable, using quality assessment")
                return await self._apply_quality_assessment(sources)
        except Exception as e:
            logger.error(f"Secondary curator failed: {e}")
            return await self._apply_quality_assessment(sources)

    async def _apply_quality_assessment(self, sources: List[Any]) -> List[Any]:
        """
        Built-in quality assessment for sources.
        
        Args:
            sources: Sources to assess
            
        Returns:
            Quality-filtered sources
        """
        assessed_sources = []

        for source in sources:
            scores = await self._calculate_quality_scores(source)
            source_id = self._get_source_id(source)

            if source_id in self.source_metadata:
                metadata = self.source_metadata[source_id]
                metadata.quality_score = scores['quality']
                metadata.credibility_score = scores['credibility']
                metadata.freshness_score = scores['freshness']

                # Calculate combined score based on strategy
                metadata.combined_score = self._calculate_combined_score(metadata)

                # Filter based on thresholds
                if metadata.combined_score >= self.quality_thresholds['combined']:
                    assessed_sources.append(source)
                else:
                    metadata.rejection_reason = f"Combined score {metadata.combined_score:.2f} below threshold"

        return assessed_sources

    async def _calculate_quality_scores(self, source: Any) -> Dict[str, float]:
        """Calculate quality scores for a source."""
        scores = {
            'quality': 0.5,  # Default scores
            'credibility': 0.5,
            'freshness': 0.5
        }

        try:
            # Extract source information
            source_text = str(source)

            # Quality indicators
            quality_indicators = [
                'research', 'study', 'analysis', 'report', 'journal',
                'university', 'institute', 'foundation', 'organization'
            ]
            quality_count = sum(1 for ind in quality_indicators if ind in source_text.lower())
            scores['quality'] = min(1.0, 0.3 + (quality_count * 0.1))

            # Credibility indicators
            credibility_indicators = [
                '.edu', '.gov', '.org', 'peer-reviewed', 'published',
                'verified', 'official', 'authoritative'
            ]
            cred_count = sum(1 for ind in credibility_indicators if ind in source_text.lower())
            scores['credibility'] = min(1.0, 0.4 + (cred_count * 0.15))

            # Freshness (simplified - would need actual date parsing)
            current_year = datetime.now().year
            if str(current_year) in source_text or str(current_year - 1) in source_text:
                scores['freshness'] = 0.9
            elif str(current_year - 2) in source_text:
                scores['freshness'] = 0.7
            else:
                scores['freshness'] = 0.5

        except Exception as e:
            logger.debug(f"Error calculating quality scores: {e}")

        return scores

    async def _diversity_optimization_stage(self, sources: List[Any]) -> List[Any]:
        """
        Optimize source diversity to avoid echo chambers.
        
        Args:
            sources: Sources from secondary curation
            
        Returns:
            Diversity-optimized source list
        """
        if len(sources) <= 3:
            return sources  # Too few sources to optimize

        if self.researcher.verbose:
            await self._stream_output(
                "diversity_optimization",
                f"🌈 Optimizing source diversity for {len(sources)} sources..."
            )

        # Group sources by domain/type
        source_groups = self._group_sources_by_domain(sources)

        # Select diverse sources
        diverse_sources = []
        sources_per_group = max(1, len(sources) // len(source_groups)) if source_groups else 1

        for group_name, group_sources in source_groups.items():
            # Take top sources from each group
            selected = group_sources[:sources_per_group]
            diverse_sources.extend(selected)

            # Update diversity scores
            for source in selected:
                source_id = self._get_source_id(source)
                if source_id in self.source_metadata:
                    # Higher diversity score for sources from smaller groups
                    self.source_metadata[source_id].diversity_score = 1.0 / len(source_groups)

        return diverse_sources

    def _group_sources_by_domain(self, sources: List[Any]) -> Dict[str, List[Any]]:
        """Group sources by domain or type."""
        groups = {}

        for source in sources:
            # Simplified domain extraction
            domain = "general"
            source_str = str(source).lower()

            if any(term in source_str for term in ['.edu', 'university', 'academic']):
                domain = "academic"
            elif any(term in source_str for term in ['.gov', 'government', 'official']):
                domain = "government"
            elif any(term in source_str for term in ['news', 'media', 'press']):
                domain = "news"
            elif any(term in source_str for term in ['blog', 'medium', 'substack']):
                domain = "blog"
            elif any(term in source_str for term in ['.org', 'organization', 'foundation']):
                domain = "organization"

            if domain not in groups:
                groups[domain] = []
            groups[domain].append(source)

        return groups

    async def _final_selection_stage(
        self,
        sources: List[Any],
        min_sources: int,
        max_sources: Optional[int],
        custom_criteria: Optional[Dict]
    ) -> List[Any]:
        """
        Final selection stage based on strategy and constraints.
        
        Args:
            sources: Sources from diversity optimization
            min_sources: Minimum sources required
            max_sources: Maximum sources allowed
            custom_criteria: Custom selection criteria
            
        Returns:
            Final selected sources
        """
        if not sources:
            return []

        # Sort sources by combined score
        scored_sources = []
        for source in sources:
            source_id = self._get_source_id(source)
            if source_id in self.source_metadata:
                score = self.source_metadata[source_id].combined_score
                scored_sources.append((score, source))

        scored_sources.sort(reverse=True, key=lambda x: x[0])

        # Apply constraints
        selected = [source for _, source in scored_sources]

        # Ensure minimum sources
        if len(selected) < min_sources and self.strategy == CurationStrategy.ADAPTIVE:
            # Relax thresholds if needed
            await self._relax_thresholds_and_reselect(sources, min_sources)

        # Apply maximum constraint
        if max_sources and len(selected) > max_sources:
            selected = selected[:max_sources]

        # Apply custom criteria if provided
        if custom_criteria:
            selected = self._apply_custom_criteria(selected, custom_criteria)

        # Update final metadata
        for source in selected:
            source_id = self._get_source_id(source)
            if source_id in self.source_metadata:
                self.source_metadata[source_id].curation_stage = "final_selected"

        return selected

    async def _relax_thresholds_and_reselect(self, sources: List[Any], min_sources: int):
        """Relax quality thresholds if minimum sources not met."""
        logger.info("Relaxing thresholds to meet minimum source requirement")

        # Reduce all thresholds by 20%
        for key in self.quality_thresholds:
            self.quality_thresholds[key] *= 0.8

        # Re-evaluate sources with relaxed thresholds
        # This would trigger a partial re-curation with new thresholds

    def _apply_custom_criteria(self, sources: List[Any], criteria: Dict) -> List[Any]:
        """Apply custom filtering criteria."""
        filtered = sources

        if 'exclude_domains' in criteria:
            excluded = criteria['exclude_domains']
            filtered = [s for s in filtered if not any(d in str(s) for d in excluded)]

        if 'require_keywords' in criteria:
            keywords = criteria['require_keywords']
            filtered = [s for s in filtered if any(k in str(s).lower() for k in keywords)]

        return filtered

    def _calculate_combined_score(self, metadata: SourceMetadata) -> float:
        """Calculate combined score based on curation strategy."""
        if self.strategy == CurationStrategy.RELEVANCE_FIRST:
            weights = {
                'relevance': 0.5,
                'quality': 0.2,
                'credibility': 0.2,
                'freshness': 0.1
            }
        elif self.strategy == CurationStrategy.QUALITY_FIRST:
            weights = {
                'relevance': 0.2,
                'quality': 0.4,
                'credibility': 0.3,
                'freshness': 0.1
            }
        else:  # BALANCED or other
            weights = {
                'relevance': 0.3,
                'quality': 0.3,
                'credibility': 0.25,
                'freshness': 0.15
            }

        score = (
            weights['relevance'] * metadata.relevance_score +
            weights['quality'] * metadata.quality_score +
            weights['credibility'] * metadata.credibility_score +
            weights['freshness'] * metadata.freshness_score
        )

        # Add diversity bonus if available
        if metadata.diversity_score > 0:
            score += metadata.diversity_score * 0.1

        return min(1.0, score)

    def _initialize_source_metadata(self, sources: List[Any]):
        """Initialize metadata for all sources."""
        for source in sources:
            source_id = self._get_source_id(source)
            if source_id not in self.source_metadata:
                self.source_metadata[source_id] = SourceMetadata(
                    source_id=source_id,
                    url=self._extract_url(source),
                    title=self._extract_title(source)
                )

    def _get_source_id(self, source: Any) -> str:
        """Generate unique ID for a source."""
        source_str = str(source)
        return hashlib.md5(source_str.encode()).hexdigest()[:16]

    def _extract_url(self, source: Any) -> Optional[str]:
        """Extract URL from source if available."""
        source_str = str(source)
        # Simplified URL extraction
        if 'http' in source_str:
            start = source_str.find('http')
            end = source_str.find(' ', start)
            if end == -1:
                end = len(source_str)
            return source_str[start:end]
        return None

    def _extract_title(self, source: Any) -> Optional[str]:
        """Extract title from source if available."""
        # This would need proper implementation based on source structure
        return None

    def _log_curation_statistics(self, original: List[Any], final: List[Any]):
        """Log curation statistics for analysis."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'original_count': len(original),
            'final_count': len(final),
            'reduction_rate': 1 - (len(final) / len(original)) if original else 0,
            'strategy': self.strategy.value,
            'stage_metrics': self._calculate_stage_metrics()
        }

        self.curation_history.append(stats)

        if self.researcher.verbose:
            logger.info(f"Curation complete: {stats['original_count']} → {stats['final_count']} sources "
                       f"({stats['reduction_rate']:.1%} reduction)")

    def _calculate_stage_metrics(self) -> Dict[str, int]:
        """Calculate metrics for each curation stage."""
        metrics = {
            'uncurated': 0,
            'primary_passed': 0,
            'secondary_passed': 0,
            'final_selected': 0
        }

        for metadata in self.source_metadata.values():
            stage = metadata.curation_stage
            if stage in metrics:
                metrics[stage] += 1

        return metrics

    async def _stream_output(self, event_type: str, message: str):
        """Stream output if websocket available."""
        if self.researcher.verbose:
            logger.info(message)

        if hasattr(self.researcher, 'websocket') and self.researcher.websocket:
            try:
                from ..actions.utils import stream_output
                await stream_output(
                    "logs",
                    event_type,
                    message,
                    self.researcher.websocket
                )
            except ImportError:
                pass

    def set_secondary_curator(self, curator_agent):
        """Set the secondary curator agent."""
        self.secondary_curator = curator_agent
        if hasattr(self.researcher.cfg, 'secondary_curator_agent'):
            self.researcher.cfg.secondary_curator_agent = curator_agent

    def set_strategy(self, strategy: CurationStrategy):
        """Change curation strategy."""
        self.strategy = strategy
        self.quality_thresholds = self._initialize_thresholds()

    def get_curation_report(self) -> Dict[str, Any]:
        """Get comprehensive curation report."""
        return {
            'total_sources_processed': len(self.source_metadata),
            'stage_metrics': self._calculate_stage_metrics(),
            'average_scores': self._calculate_average_scores(),
            'rejection_reasons': self._get_rejection_summary(),
            'curation_history': self.curation_history[-10:]  # Last 10 curations
        }

    def _calculate_average_scores(self) -> Dict[str, float]:
        """Calculate average scores across all sources."""
        if not self.source_metadata:
            return {}

        totals = {
            'relevance': 0,
            'quality': 0,
            'credibility': 0,
            'freshness': 0,
            'combined': 0
        }

        count = len(self.source_metadata)
        for metadata in self.source_metadata.values():
            totals['relevance'] += metadata.relevance_score
            totals['quality'] += metadata.quality_score
            totals['credibility'] += metadata.credibility_score
            totals['freshness'] += metadata.freshness_score
            totals['combined'] += metadata.combined_score

        return {k: v / count for k, v in totals.items()}

    def _get_rejection_summary(self) -> Dict[str, int]:
        """Get summary of rejection reasons."""
        reasons = {}
        for metadata in self.source_metadata.values():
            if metadata.rejection_reason:
                reason = metadata.rejection_reason.split(':')[0]  # Get reason category
                reasons[reason] = reasons.get(reason, 0) + 1
        return reasons