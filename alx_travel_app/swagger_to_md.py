import json
import os
from collections import defaultdict

def clean_path_prefix(path):
    """Extract top-level resource like /bookings/, /listings/"""
    parts = path.strip("/").split("/")
    return parts[0] if parts else "general"

def generate_markdown_from_swagger(schema_path, output_path="api.md"):
    with open(schema_path, "r") as f:
        data = json.load(f)

    md = []
    info = data.get("info", {})
    title = info.get("title", "API Documentation")
    version = info.get("version", "")
    description = info.get("description", "")

    md.append(f"# {title}")
    md.append(f"\n**Version:** {version}  ")
    if description:
        md.append(f"**Description:** {description}\n")

    paths = data.get("paths", {})
    grouped = defaultdict(list)

    # Group endpoints by resource prefix
    for path, methods in paths.items():
        prefix = clean_path_prefix(path)
        grouped[prefix].append((path, methods))

    for resource, endpoints in grouped.items():
        md.append("\n---")
        md.append(f"\n## 📂 {resource.capitalize()}")

        for path, methods in endpoints:
            for method, details in methods.items():
                if not isinstance(details, dict):
                    continue

                summary = details.get("summary") or f"{method.upper()} {path}"
                desc = details.get("description", "")
                md.append(f"\n### `{method.upper()} {path}`")
                md.append(f"{summary if summary else ''}")
                if desc:
                    md.append(f"\n*{desc}*")

                # Parameters
                params = details.get("parameters", [])
                body_params = []
                query_params = []

                for param in params:
                    if param.get("in") == "body":
                        body_params.append(param)
                    elif param.get("in") == "query":
                        query_params.append(param)

                if query_params:
                    md.append("\n**Query Parameters:**")
                    for p in query_params:
                        md.append(f"- `{p.get('name')}`: {p.get('description', '')}")

                # Request Body
                if body_params:
                    for p in body_params:
                        md.append("\n**Request Body:**")
                        example = p.get("x-example") or p.get("example")
                        schema = p.get("schema", {})
                        if example:
                            md.append("```json\n" + json.dumps(example, indent=2) + "\n```")
                        elif "example" in schema:
                            md.append("```json\n" + json.dumps(schema['example'], indent=2) + "\n```")
                        else:
                            md.append("_No example provided._")

                # Responses
                responses = details.get("responses", {})
                if responses:
                    md.append("\n**Responses:**")
                    for code, resp in responses.items():
                        code_desc = resp.get("description", "")
                        md.append(f"- `{code}`: {code_desc}")

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"✅ Clean Markdown saved to {output_path}")
    print(f"📄 Preview: {os.path.abspath(output_path)}")

# Run it
generate_markdown_from_swagger("schema.json")
