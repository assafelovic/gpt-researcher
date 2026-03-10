"""
Research Knowledge Tracker for GPT-Researcher
Tracks research findings with confidence and lifecycle
"""

from enum import Enum
from typing import Dict, List, Optional
import time
import uuid

class Phase(Enum):
    SPROUT = "sprout"
    GREEN_LEAF = "green_leaf"
    YELLOW_LEAF = "yellow_leaf"
    RED_LEAF = "red_leaf"
    SOIL = "soil"

class Finding:
    """A research finding with confidence tracking"""
    
    def __init__(self, content: str, source: str, priority: str = "P2"):
        self.id = str(uuid.uuid4())[:8]
        self.content = content
        self.source = source
        self.priority = priority
        self.confidence = 0.7
        self.phase = Phase.SPROUT
        self.created_at = time.time()
        self.access_count = 0
        self.references: List[str] = []
    
    def boost(self):
        """Boost confidence on access"""
        self.access_count += 1
        self.confidence = min(1.0, self.confidence + 0.03)
        if self.confidence >= 0.8:
            self.phase = Phase.GREEN_LEAF
    
    def add_reference(self, ref: str):
        """Add a reference"""
        self.references.append(ref)
        self.confidence = min(1.0, self.confidence + 0.02)

class ResearchTracker:
    """
    Tracks research findings with lifecycle management.
    Based on Memory-Like-A-Tree concept.
    """
    
    def __init__(self):
        self.findings: Dict[str, Finding] = {}
        self.research_id: Optional[str] = None
    
    def add_finding(self, content: str, source: str, 
                   priority: str = "P2") -> Finding:
        """Add a new research finding"""
        finding = Finding(content, source, priority)
        self.findings[finding.id] = finding
        return finding
    
    def access(self, finding_id: str) -> bool:
        """Access a finding"""
        if finding_id not in self.findings:
            return False
        self.findings[finding_id].boost()
        return True
    
    def add_reference(self, finding_id: str, reference: str) -> bool:
        """Add reference to finding"""
        if finding_id not in self.findings:
            return False
        self.findings[finding_id].add_reference(reference)
        return True
    
    def get_high_confidence(self, threshold: float = 0.8) -> List[Finding]:
        """Get findings above confidence threshold"""
        return [
            f for f in self.findings.values()
            if f.confidence >= threshold
        ]
    
    def get_status(self) -> Dict:
        """Get research status"""
        phases = {}
        for f in self.findings.values():
            p = f.phase.value
            phases[p] = phases.get(p, 0) + 1
        return {
            'total_findings': len(self.findings),
            'phases': phases,
            'avg_confidence': sum(f.confidence for f in self.findings.values()) / max(1, len(self.findings))
        }
    
    def decay_all(self):
        """Apply decay to all findings"""
        for f in self.findings.values():
            decay = {'P0': 0, 'P1': 0.004, 'P2': 0.008}.get(f.priority, 0.008)
            f.confidence = max(0, f.confidence - decay)
            if f.confidence >= 0.8:
                f.phase = Phase.GREEN_LEAF
            elif f.confidence >= 0.5:
                f.phase = Phase.YELLOW_LEAF
            elif f.confidence >= 0.3:
                f.phase = Phase.RED_LEAF
            else:
                f.phase = Phase.SOIL
