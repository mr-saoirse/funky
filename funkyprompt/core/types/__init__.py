"""a map to json schema types for serialization"""

PYTHON_TO_JSON_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}
