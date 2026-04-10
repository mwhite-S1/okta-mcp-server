# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for policy tools.

Calls the real tool functions end-to-end with a live Okta client.
No SDK mocking — these tests catch deserialization failures, wrong SDK method
names, and type mismatches that unit tests with AsyncMock cannot detect.
"""

from __future__ import annotations

import time

import pytest

from okta_mcp_server.tools.policies.policies import (
    get_policy,
    get_policy_rule,
    list_policies,
    list_policy_mappings,
    list_policy_rules,
    create_policy,
    delete_policy,
)


# ---------------------------------------------------------------------------
# list_policies
# ---------------------------------------------------------------------------

class TestListPolicies:
    @pytest.mark.asyncio
    async def test_access_policy_returns_list(self, real_ctx):
        result = await list_policies(ctx=real_ctx, type="ACCESS_POLICY")
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) > 0

    @pytest.mark.asyncio
    async def test_password_policy_returns_list(self, real_ctx):
        result = await list_policies(ctx=real_ctx, type="PASSWORD")
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_policy_shape(self, real_ctx):
        """Each returned policy must have the required fields."""
        result = await list_policies(ctx=real_ctx, type="ACCESS_POLICY")
        assert "error" not in result, result.get("error")
        for policy in result["items"]:
            assert "id" in policy, f"Missing 'id' in policy: {policy}"
            assert "name" in policy
            assert "type" in policy
            assert policy["type"] == "ACCESS_POLICY"
            assert "status" in policy

    @pytest.mark.asyncio
    async def test_limit_param_accepted(self, real_ctx):
        """Passing limit=20 must not raise a type error."""
        result = await list_policies(ctx=real_ctx, type="ACCESS_POLICY", limit=20)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_status_filter_active(self, real_ctx):
        result = await list_policies(ctx=real_ctx, type="ACCESS_POLICY", status="ACTIVE")
        assert "error" not in result, result.get("error")
        for policy in result["items"]:
            assert policy.get("status") == "ACTIVE"

    @pytest.mark.asyncio
    async def test_mfa_enroll_policy_type(self, real_ctx):
        result = await list_policies(ctx=real_ctx, type="MFA_ENROLL")
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_okta_sign_on_policy_type(self, real_ctx):
        result = await list_policies(ctx=real_ctx, type="OKTA_SIGN_ON")
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_pagination_metadata_present(self, real_ctx):
        """has_more must be a bool and next_cursor must be None or a string."""
        result = await list_policies(ctx=real_ctx, type="ACCESS_POLICY", limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)
        assert result.get("next_cursor") is None or isinstance(result.get("next_cursor"), str)
        assert isinstance(result.get("total_fetched"), int)

    @pytest.mark.asyncio
    async def test_cursor_fetches_next_page(self, real_ctx):
        """If has_more is True, the cursor must retrieve a different page."""
        first_page = await list_policies(ctx=real_ctx, type="ACCESS_POLICY", limit=20)
        assert "error" not in first_page, first_page.get("error")
        if not first_page.get("has_more"):
            pytest.skip("Only one page of ACCESS_POLICY policies — pagination not testable")

        cursor = first_page["next_cursor"]
        second_page = await list_policies(ctx=real_ctx, type="ACCESS_POLICY", limit=20, after=cursor)
        assert "error" not in second_page, second_page.get("error")
        assert isinstance(second_page["items"], list)

        first_ids = {p["id"] for p in first_page["items"]}
        second_ids = {p["id"] for p in second_page["items"]}
        assert not first_ids & second_ids, "Second page shares items with first page"


# ---------------------------------------------------------------------------
# get_policy
# ---------------------------------------------------------------------------

class TestGetPolicy:
    @pytest.mark.asyncio
    async def test_get_policy_returns_dict(self, real_ctx, first_access_policy_id):
        result = await get_policy(ctx=real_ctx, policy_id=first_access_policy_id)
        assert result is not None
        assert "error" not in result, result.get("error")
        assert result.get("id") == first_access_policy_id
        assert "name" in result
        assert "type" in result

    @pytest.mark.asyncio
    async def test_get_policy_invalid_id(self, real_ctx):
        result = await get_policy(ctx=real_ctx, policy_id="invalid-id-000")
        assert result is None or "error" in result


# ---------------------------------------------------------------------------
# list_policy_rules
# ---------------------------------------------------------------------------

class TestListPolicyRules:
    @pytest.mark.asyncio
    async def test_returns_rules_list(self, real_ctx, first_access_policy_id):
        result = await list_policy_rules(ctx=real_ctx, policy_id=first_access_policy_id)
        assert "error" not in result, result.get("error")
        assert "rules" in result
        assert isinstance(result["rules"], list)

    @pytest.mark.asyncio
    async def test_rule_shape(self, real_ctx, first_access_policy_id):
        """Each rule must have required fields including OS platform values."""
        result = await list_policy_rules(ctx=real_ctx, policy_id=first_access_policy_id)
        assert "error" not in result, result.get("error")
        for rule in result["rules"]:
            assert "id" in rule
            assert "name" in rule
            assert "status" in rule
            assert "actions" in rule

    @pytest.mark.asyncio
    async def test_all_access_policies_have_readable_rules(self, real_ctx):
        """Every ACCESS_POLICY in the org must return rules without error.

        This is the regression test for the MACOS/KnowledgeConstraint SDK enum
        bugs — rules with platform conditions referencing MACOS would previously
        blow up during deserialization.
        """
        policies_result = await list_policies(ctx=real_ctx, type="ACCESS_POLICY")
        assert "error" not in policies_result, policies_result.get("error")

        failures = []
        for policy in policies_result["items"]:
            pid = policy["id"]
            pname = policy["name"]
            rules_result = await list_policy_rules(ctx=real_ctx, policy_id=pid)
            if "error" in rules_result:
                failures.append(f"{pname} ({pid}): {rules_result['error']}")

        assert not failures, "list_policy_rules failed for:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# get_policy_rule
# ---------------------------------------------------------------------------

class TestGetPolicyRule:
    @pytest.mark.asyncio
    async def test_get_rule_matches_listed(self, real_ctx, first_access_policy_id):
        rules_result = await list_policy_rules(ctx=real_ctx, policy_id=first_access_policy_id)
        assert "error" not in rules_result, rules_result.get("error")
        rules = rules_result["rules"]
        if not rules:
            pytest.skip("No rules on first ACCESS_POLICY")

        rule_id = rules[0]["id"]
        rule = await get_policy_rule(ctx=real_ctx, policy_id=first_access_policy_id, rule_id=rule_id)
        assert rule is not None
        assert "error" not in rule, rule.get("error")
        assert rule.get("id") == rule_id


# ---------------------------------------------------------------------------
# list_policy_mappings
# ---------------------------------------------------------------------------

class TestListPolicyMappings:
    @pytest.mark.asyncio
    async def test_mappings_returns_without_error(self, real_ctx, first_access_policy_id):
        result = await list_policy_mappings(ctx=real_ctx, policy_id=first_access_policy_id)
        assert "error" not in result, result.get("error")
        assert "items" in result


# ---------------------------------------------------------------------------
# CRUD: create → get → delete
# ---------------------------------------------------------------------------

class TestPolicyCRUD:
    @pytest.mark.asyncio
    async def test_create_and_delete_access_policy(self, real_ctx):
        """Full create → read → delete cycle for ACCESS_POLICY."""
        ts = int(time.time())
        policy_data = {
            "type": "ACCESS_POLICY",
            "name": f"mcp-tool-test-{ts}",
            "status": "INACTIVE",
            "description": "Created by tool integration test — safe to delete",
        }

        created = await create_policy(ctx=real_ctx, policy_data=policy_data)
        assert created is not None, "create_policy returned None"
        assert "error" not in created, created.get("error")
        policy_id = created.get("id")
        assert policy_id, "Created policy has no id"

        try:
            fetched = await get_policy(ctx=real_ctx, policy_id=policy_id)
            assert fetched is not None
            assert fetched.get("id") == policy_id
            assert fetched.get("name") == f"mcp-tool-test-{ts}"
        finally:
            result = await delete_policy(ctx=real_ctx, policy_id=policy_id)
            assert "error" not in result, f"Cleanup delete failed: {result.get('error')}"
