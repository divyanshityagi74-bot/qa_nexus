"""
environment_resolver.py
=======================
Loader layer — reads environment JSON and substitutes {{variables}}
in all three Postman collection files.

Resolved values are used internally by the generator only.
Generated test methods always reference config.BASE_URL — never hardcoded URLs.

Called by: src/nodes/resolve_environment.py (LangGraph node)
"""

import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def resolve(
    environment_path: str,
    internal_collection_path: str,
    external_collection_path: str,
    consumer_collection_path: str,
    auth_collection_path: str,
) -> dict:
    """
    Reads environment JSON and substitutes all {{variables}}
    in all four collection files.

    Args:
        environment_path:           path to dev.json or staging.json or test.json
        internal_collection_path:   path to internal_am_api.json
        external_collection_path:   path to external_am_api.json
        consumer_collection_path:   path to consumer_am_api.json
        auth_collection_path:       path to demo_examples.json

    Returns:
        dict with keys:
            resolved_internal, resolved_external,
            resolved_consumer, resolved_auth,
            env_name, variables
    """

    # ── Read environment file ────────────────────────────────
    env_path = Path(environment_path)
    if not env_path.exists():
        raise FileNotFoundError(
            f"Environment file not found: {environment_path}"
        )

    with open(env_path, encoding="utf-8") as f:
        env_data = json.load(f)

    # Build variable map from Postman env format
    # values array contains {key, value, enabled} objects
    variables = {
        item["key"]: item["value"]
        for item in env_data.get("values", [])
        if item.get("enabled", True)
    }

    env_name = env_data.get("name", "default")

    logger.info(
        f"Environment loaded: {env_name} — "
        f"{len(variables)} variable(s) found"
    )

    # ── Resolve each collection ───────────────────────────────
    resolved_internal = _resolve_collection(
        internal_collection_path, variables, "internal"
    )
    resolved_external = _resolve_collection(
        external_collection_path, variables, "external"
    )
    resolved_consumer = _resolve_collection(
        consumer_collection_path, variables, "consumer"
    )
    resolved_auth = _resolve_collection(
        auth_collection_path, variables, "auth"
    )

    return {
        "resolved_internal": resolved_internal,
        "resolved_external": resolved_external,
        "resolved_consumer": resolved_consumer,
        "resolved_auth":     resolved_auth,
        "env_name":          env_name,
        "variables":         variables,
    }


def _resolve_collection(
    collection_path: str,
    variables: dict,
    label: str,
) -> dict:
    """
    Reads a single Postman collection JSON and substitutes
    all {{variable}} placeholders with real values.

    Args:
        collection_path: path to the collection JSON file
        variables:       key-value map from environment file
        label:           name used for logging (internal/external etc)

    Returns:
        Resolved collection as Python dict
    """
    path = Path(collection_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Collection file not found: {collection_path}"
        )

    with open(path, encoding="utf-8") as f:
        raw_collection = json.load(f)

    # Serialise to string — substitute all {{variable}} occurrences
    collection_str = json.dumps(raw_collection)

    substitution_count = 0
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder in collection_str:
            collection_str = collection_str.replace(placeholder, value)
            substitution_count += 1

    resolved = json.loads(collection_str)

    # Check for any remaining unresolved placeholders
    remaining = collection_str.count("{{")
    if remaining > 0:
        logger.warning(
            f"{label} collection: {remaining} placeholder(s) "
            f"could not be resolved — variable missing from env file"
        )
    else:
        logger.info(
            f"{label} collection resolved — "
            f"{substitution_count} substitution(s) made"
        )

    return resolved