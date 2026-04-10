# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for governance label tools: list, get, create, update, delete, assign."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.labels import (
    assign_governance_labels,
    create_governance_label,
    delete_governance_label,
    get_governance_label,
    list_governance_labels,
    update_governance_label,
)


PATCH_CLIENT = "okta_mcp_server.tools.governance.labels.get_okta_client"

LABEL_ID = "lbl0001testABCDEF"
LABEL_DICT = {
    "id": LABEL_ID,
    "name": "sensitivity",
    "values": [
        {"id": "lv001", "name": "High", "metadata": {"backgroundColor": "red"}},
        {"id": "lv002", "name": "Low", "metadata": {"backgroundColor": "green"}},
    ],
}


def _make_executor(body=None, execute_error=None, no_content=False):
    executor = AsyncMock()
    executor.create_request.return_value = (MagicMock(), None)
    if execute_error:
        executor.execute.return_value = (MagicMock(), execute_error)
    elif no_content:
        executor.execute.return_value = (None, None)
    else:
        resp = MagicMock()
        resp.get_body.return_value = body
        executor.execute.return_value = (resp, None)
    return executor


def _make_client(body=None, execute_error=None, no_content=False):
    executor = _make_executor(body=body, execute_error=execute_error, no_content=no_content)
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# list_governance_labels
# ---------------------------------------------------------------------------

class TestListGovernanceLabels:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_labels(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [LABEL_DICT]})
        mock_get_client.return_value = client

        result = await list_governance_labels(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["id"] == LABEL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_governance_labels(ctx=ctx_elicit_accept_true)

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_governance_labels(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_governance_labels(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_after_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_governance_labels(ctx=ctx_elicit_accept_true, after="cursor123")

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "after=cursor123" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_governance_labels(ctx=ctx_elicit_accept_true, limit=10)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "limit=10" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path_used(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_governance_labels(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v1/labels" in url_arg


# ---------------------------------------------------------------------------
# get_governance_label
# ---------------------------------------------------------------------------

class TestGetGovernanceLabel:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_label(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=LABEL_DICT)
        mock_get_client.return_value = client

        result = await get_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        assert result["id"] == LABEL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Label not found")
        mock_get_client.return_value = client

        result = await get_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path_used(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=LABEL_DICT)
        mock_get_client.return_value = client

        await get_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert LABEL_ID in url_arg


# ---------------------------------------------------------------------------
# create_governance_label
# ---------------------------------------------------------------------------

class TestCreateGovernanceLabel:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_label(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=LABEL_DICT)
        mock_get_client.return_value = client

        values = [{"name": "High", "metadata": {"backgroundColor": "red"}}]
        result = await create_governance_label(ctx=ctx_elicit_accept_true, name="sensitivity", values=values)

        assert result["id"] == LABEL_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Invalid label config")
        mock_get_client.return_value = client

        result = await create_governance_label(ctx=ctx_elicit_accept_true, name="bad", values=[])

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_governance_label(ctx=ctx_elicit_accept_true, name="test", values=[])

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_includes_name_and_values(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=LABEL_DICT)
        mock_get_client.return_value = client

        values = [{"name": "High"}]
        await create_governance_label(ctx=ctx_elicit_accept_true, name="sensitivity", values=values)

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["name"] == "sensitivity"
        assert body_arg["values"] == values


# ---------------------------------------------------------------------------
# update_governance_label
# ---------------------------------------------------------------------------

class TestUpdateGovernanceLabel:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_label(self, mock_get_client, ctx_elicit_accept_true):
        updated = {**LABEL_DICT, "name": "data-sensitivity"}
        client = _make_client(body=updated)
        mock_get_client.return_value = client

        ops = [{"op": "replace", "path": "/name", "value": "data-sensitivity"}]
        result = await update_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID, operations=ops)

        assert result["name"] == "data-sensitivity"
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "PATCH"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Label not found")
        mock_get_client.return_value = client

        result = await update_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID, operations=[])

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID, operations=[])

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_label_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=LABEL_DICT)
        mock_get_client.return_value = client

        await update_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID, operations=[])

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert LABEL_ID in url_arg


# ---------------------------------------------------------------------------
# assign_governance_labels
# ---------------------------------------------------------------------------

class TestAssignGovernanceLabels:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_assigns_labels(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"assignedCount": 1})
        mock_get_client.return_value = client

        result = await assign_governance_labels(
            ctx=ctx_elicit_accept_true,
            resource_orns=["orn:okta:apps:000:apps:0oa123"],
            label_value_ids=["lv001"],
        )

        assert "error" not in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        orns = ["orn:okta:apps:000:apps:0oa123"]
        ids = ["lv001", "lv002"]
        await assign_governance_labels(
            ctx=ctx_elicit_accept_true,
            resource_orns=orns,
            label_value_ids=ids,
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["resourceOrns"] == orns
        assert body_arg["labelValueIds"] == ids

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Resource not found")
        mock_get_client.return_value = client

        result = await assign_governance_labels(ctx=ctx_elicit_accept_true, resource_orns=[], label_value_ids=[])

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await assign_governance_labels(ctx=ctx_elicit_accept_true, resource_orns=[], label_value_ids=[])

        assert "error" in result
