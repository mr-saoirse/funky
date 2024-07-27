"""a map to json schema types for serialization"""

EMBEDDING_LENGTH_OPEN_AI = 1536

PYTHON_TO_JSON_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}
