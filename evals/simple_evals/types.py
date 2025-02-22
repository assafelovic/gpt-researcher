from typing import Dict, List, TypedDict, Optional, Any, Protocol

class SingleEvalResult(TypedDict):
    html: str
    score: float
    convo: List[Dict[str, str]]
    metrics: Dict[str, Any]

class EvalResult(TypedDict):
    score: float
    html: str
    single_results: List[SingleEvalResult]

class SamplerBase(Protocol):
    def _pack_message(self, content: str, role: str) -> Dict[str, str]:
        ...
    
    def __call__(self, messages: List[Dict[str, str]]) -> str:
        ...

class Eval(Protocol):
    def __call__(self, sampler: SamplerBase) -> EvalResult:
        ... 