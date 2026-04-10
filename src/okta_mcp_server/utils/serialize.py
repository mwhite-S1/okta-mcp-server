# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""
Serialization utilities for Okta SDK model objects.

The Okta Python SDK's as_dict() method returns Python dicts that may contain
enum instances (e.g. ApplicationSignOnMode.SAML_2_0) which are not JSON
serializable. This module provides helpers to recursively convert those values
to plain strings so the MCP framework can serialize them correctly.
"""

from enum import Enum
from typing import Any


def _serialize_value(value: Any) -> Any:
    """Recursively convert a value to a JSON-serializable form."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def to_dict(model: Any) -> dict:
    """Convert an Okta SDK model to a fully JSON-serializable dict.

    Supports both SDK v2 (as_dict) and SDK v3 (to_dict / model_dump) and
    recursively converts any enum values to their string .value equivalents.
    """
    if hasattr(model, "as_dict"):
        return _serialize_value(model.as_dict())
    if hasattr(model, "to_dict"):
        return _serialize_value(model.to_dict())
    if hasattr(model, "model_dump"):
        return _serialize_value(model.model_dump())
    return _serialize_value(model)
