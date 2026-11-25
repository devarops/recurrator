from conftest import _read_openapi_document, _read_response_schema

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _json_200_schemas(document):
    """Yield (method, path, schema) for every 200 response in the document."""
    for path, operations in document["paths"].items():
        for method, operation in operations.items():
            if method not in _HTTP_METHODS:
                continue
            for status, response in operation.get("responses", {}).items():
                if status == "200":
                    content = response.get("content", {})
                    media = content.get("application/json", {})
                    schema = media.get("schema", {})
                    yield method.upper(), path, schema


def _assert_schema_is_declared(schema, method, path):
    """Assert one 200 response declares the schema shape its type promises."""
    location = f"{method} {path}"
    assert schema, f"{location} declares an empty 200 schema"
    if schema.get("type") == "object":
        assert "properties" in schema, f"{location} declares an object schema without properties"
    elif schema.get("type") == "array":
        assert "items" in schema, f"{location} declares an array schema without items"


def test_openapi_declares_response_properties():
    """Every 200 response declares a non-empty, fully shaped schema."""
    document = _read_openapi_document()

    for method, path, schema in _json_200_schemas(document):
        _assert_schema_is_declared(schema, method, path)


def test_openapi_declares_task_contexts():
    """The task detail schema declares contexts as an array of strings."""
    schema = _read_response_schema(_read_openapi_document(), "/api/task/{task_id}")
    contexts = schema["properties"]["contexts"]
    assert contexts["type"] == "array"
    assert contexts["items"]["type"] == "string"


def test_openapi_declares_context_properties():
    """The context detail schema declares its fields and scopes as strings."""
    schema = _read_response_schema(_read_openapi_document(), "/api/context/{context_id}/")

    properties = schema["properties"]

    assert set(properties) >= {"id", "display_name", "description", "scopes"}
    assert properties["id"]["type"] == "string"
    assert properties["display_name"]["type"] == "string"
    assert properties["description"]["type"] == "string"
    assert properties["scopes"]["type"] == "array"
    assert properties["scopes"]["items"]["type"] == "string"


def test_openapi_declares_collection_items():
    """The collection and due variants declare their item types."""
    document = _read_openapi_document()

    for path in ("/api/context/", "/api/context/due/{reference_date}", "/api/context/due/"):
        schema = _read_response_schema(document, path)
        assert schema["type"] == "array", f"GET {path} is not declared as an array"
        assert schema["items"]["type"] == "string", f"GET {path} does not declare string items"

    for path in ("/api/task/", "/api/task/due/{reference_date}", "/api/task/due/"):
        schema = _read_response_schema(document, path)
        assert schema["type"] == "array", f"GET {path} is not declared as an array"
        assert schema["items"]["type"] == "integer", f"GET {path} does not declare integer items"
