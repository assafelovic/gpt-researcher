import json
from typing import Dict, Any
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str
    email: str
    age: int
    is_active: bool

def generate_structured_json(schema: BaseModel, data: Dict[str, Any]) -> str:
    """
    Generate structured JSON output based on provided schema
    
    Args:
        schema: Pydantic model defining the schema structure
        data: Dictionary containing the data to be structured
    
    Returns:
        str: JSON string with structured data
    """
    try:
        # Create instance of schema with provided data
        structured_data = schema(**data)
        # Convert to JSON string
        return json.dumps(structured_data.dict(), indent=2)
    except Exception as e:
        return f"Error generating JSON: {str(e)}"

# Example usage
if __name__ == "__main__":
    sample_data = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "is_active": True
    }
    
    json_output = generate_structured_json(UserSchema, sample_data)
    print("Structured JSON Output:")
    print(json_output)
