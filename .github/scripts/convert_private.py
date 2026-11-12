#!/usr/bin/env python3
"""Convert the ClickHouse Cloud dashboard into a ClickHouse Private dashboard.

ClickHouse Private has no ClickHouse_ServiceInfo metric and no meaningful control plane ID.
Services are identified by their Kubernetes namespace and the `app` pod label
(`c-<service-name>-server`). The namespace is selectable because it is not guaranteed
to follow the `ns-<service-name>` convention.
"""

import json
import sys
from pathlib import Path

PANELS_TO_REMOVE = {3, 78, 79, 82, 83}
CLOUD_SELECTOR = 'clickhouse_service="$service_id"'
PRIVATE_SELECTOR = 'namespace="$namespace", app="c-$service_name-server"'
LEFTOVER_MARKERS = ("clickhouse_service", "$service_id", "ClickHouse_ServiceInfo")

SERVER_SERIES = 'ClickHouseAsyncMetrics_Uptime{app_kubernetes_io_name="clickhouse-server"}'
NAMESPACED_SERVER_SERIES = (
    'ClickHouseAsyncMetrics_Uptime{app_kubernetes_io_name="clickhouse-server", namespace="$namespace"}'
)
DATASOURCE_REF = {"type": "prometheus", "uid": "${datasource}"}


def query_variable(name, label, definition, regex=""):
    """Build a Grafana Prometheus label_values query variable."""
    return {
        "current": {},
        "datasource": DATASOURCE_REF,
        "definition": definition,
        "description": "",
        "label": label,
        "name": name,
        "options": [],
        "query": {
            "qryType": 1,
            "query": definition,
            "refId": "PrometheusVariableQueryEditor-VariableQuery",
        },
        "refresh": 1,
        "regex": regex,
        "sort": 1,
        "type": "query",
    }


PRIVATE_VARIABLES = [
    query_variable("namespace", "Namespace", f"label_values({SERVER_SERIES},namespace)"),
    query_variable(
        "service_name",
        "Service Name",
        f"label_values({NAMESPACED_SERVER_SERIES},app)",
        regex="/^c-(.+)-server$/",
    ),
]


def replace_labels(obj):
    """Rewrite selectors in expr fields and instance legends in legendFormat fields, recursively."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "expr" and isinstance(value, str):
                obj[key] = value.replace(CLOUD_SELECTOR, PRIVATE_SELECTOR)
            elif key == "legendFormat" and isinstance(value, str):
                obj[key] = value.replace("{{instance}}", "{{pod}}")
            else:
                obj[key] = replace_labels(value)
    elif isinstance(obj, list):
        return [replace_labels(item) for item in obj]
    return obj


def replace_variables(templating_list):
    """Swap the Cloud service variables for Private namespace/service variables, keeping the rest."""
    kept = [var for var in templating_list if var.get("name") not in ("service_name", "service_id")]
    return PRIVATE_VARIABLES + kept


def check_no_cloud_leftovers(data):
    """Fail if any Cloud-only label, variable, or metric survived the conversion."""
    serialized = json.dumps(data)
    found = [marker for marker in LEFTOVER_MARKERS if marker in serialized]
    if found:
        sys.exit(
            f"Error: converted dashboard still references Cloud-only identifiers {found}; "
            "update convert_private.py to handle the new dashboard.json content"
        )


def convert(data):
    """Return the Private variant of a Cloud dashboard dict."""
    data["panels"] = [panel for panel in data["panels"] if panel.get("id") not in PANELS_TO_REMOVE]
    data = replace_labels(data)
    data["templating"]["list"] = replace_variables(data["templating"]["list"])
    data["title"] = f"{data['title']} (ClickHouse Private)"
    data["uid"] = f"{data['uid']}-private"
    check_no_cloud_leftovers(data)
    return data


def main():
    """Read the Cloud dashboard, convert it, and write the Private dashboard."""
    if len(sys.argv) != 3:
        sys.exit(
            "Usage: python3 convert_private.py <input_file> <output_file>\n"
            "Example: python3 convert_private.py dashboard.json dashboard_private.json"
        )

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    try:
        data = json.loads(input_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Error: input file {input_file} does not exist")
    except json.JSONDecodeError as e:
        sys.exit(f"Error: unable to parse {input_file} as JSON - {e}")

    data = convert(data)
    output_file.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Converted {input_file} -> {output_file} ({len(data['panels'])} panels)")


if __name__ == "__main__":
    main()
