from typing import Callable, List, TypeVar, Any
from tqdm import tqdm
import jinja2

T = TypeVar('T')
R = TypeVar('R')

# HTML template for rendering results
HTML_JINJA = """
<div class="eval-result mb-8 p-4 border rounded-lg">
    <div class="conversation space-y-4">
        {% for msg in prompt_messages %}
            <div class="message {{ msg.role }} p-3 {% if msg.role == 'user' %}bg-gray-100{% else %}bg-blue-50{% endif %} rounded">
                <div class="font-semibold">{{ msg.role|title }}</div>
                {{ msg.content }}
            </div>
        {% endfor %}
        <div class="message assistant p-3 bg-blue-50 rounded">
            <div class="font-semibold">Assistant</div>
            {{ next_message.content }}
        </div>
    </div>
    <div class="evaluation mt-4 p-3 bg-gray-50 rounded">
        <p class="font-bold">Score: <span class="{% if score > 0.5 %}text-green-600{% else %}text-red-600{% endif %}">{{ score }}</span></p>
        <p><span class="font-semibold">Correct Answer:</span> {{ correct_answer }}</p>
        <p><span class="font-semibold">Model Answer:</span> {{ extracted_answer }}</p>
    </div>
</div>
"""

jinja_env = jinja2.Environment(
    loader=jinja2.BaseLoader(),
    autoescape=True
)

def map_with_progress(fn: Callable[[T], R], items: List[T]) -> List[R]:
    """Map function over items with progress bar."""
    return [fn(item) for item in tqdm(items)]

def aggregate_results(results: List[Any]) -> Any:
    """Aggregate evaluation results."""
    total_score = sum(r.score for r in results) / len(results)
    combined_html = "".join(r.html for r in results)
    
    return {
        "score": total_score,
        "html": combined_html,
        "single_results": results
    } 