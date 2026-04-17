# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for user admin role target tools.

Tests cover: reading app and group targets for an existing role assignment.
Write operations (assign/unassign targets) are tested in a guarded cycle
that restores state after each test.

The first_user_with_role fixture skips automatically if no users with
admin role assignments exist in the org.
"""

from __future__ import annotations

import pytest

from okta_mcp_server.tools.users.user_role_targets import (
    assign_group_target_to_user_role,
    get_user_role_targets,
    list_user_app_role_targets,
    list_user_group_role_targets,
    unassign_group_target_from_user_role,
)


# ---------------------------------------------------------------------------
# list_user_app_role_targets
# ---------------------------------------------------------------------------

class TestListUserAppRoleTargets:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx, first_user_with_role):
        user_id, role_id = first_user_with_role
        result = await list_user_app_role_targets(
            ctx=real_ctx, user_id=user_id, role_assignment_id=role_id
        )
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_app_target_shape(self, real_ctx, first_user_with_role):
        """App targets must have at minimum an id or name field."""
        user_id, role_id = first_user_with_role
        result = await list_user_app_role_targets(
            ctx=real_ctx, user_id=user_id, role_assignment_id=role_id
        )
        assert "error" not in result, result.get("error")
        for target in result["items"]:
            if isinstance(target, dict):
                assert target.get("id") or target.get("name"), (
                    f"App target missing id and name: {target}"
                )

    @pytest.mark.asyncio
    async def test_invalid_user_returns_error(self, real_ctx):
        result = await list_user_app_role_targets(
            ctx=real_ctx, user_id="invalid-user-000", role_assignment_id="role-000"
        )
        assert isinstance(result, dict)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_limit_param_accepted(self, real_ctx, first_user_with_role):
        user_id, role_id = first_user_with_role
        result = await list_user_app_role_targets(
            ctx=real_ctx, user_id=user_id, role_assignment_id=role_id, limit=5
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")


# ---------------------------------------------------------------------------
# list_user_group_role_targets
# ---------------------------------------------------------------------------

class TestListUserGroupRoleTargets:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx, first_user_with_role):
        user_id, role_id = first_user_with_role
        result = await list_user_group_role_targets(
            ctx=real_ctx, user_id=user_id, role_assignment_id=role_id
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_group_target_shape(self, real_ctx, first_user_with_role):
        """Group targets must have an id field."""
        user_id, role_id = first_user_with_role
        result = await list_user_group_role_targets(
            ctx=real_ctx, user_id=user_id, role_assignment_id=role_id
        )
        assert "error" not in result
        for target in result["items"]:
            if isinstance(target, dict):
                assert target.get("id"), f"Group target missing id: {target}"

    @pytest.mark.asyncio
    async def test_invalid_user_returns_error(self, real_ctx):
        result = await list_user_group_role_targets(
            ctx=real_ctx, user_id="invalid-user-000", role_assignment_id="role-000"
        )
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_user_role_targets (combined view)
# ---------------------------------------------------------------------------

class TestGetUserRoleTargets:
    @pytest.mark.asyncio
    async def test_get_targets_returns_response(self, real_ctx, first_user_with_role):
        user_id, role_id = first_user_with_role
        result = await get_user_role_targets(
            ctx=real_ctx, user_id=user_id, role_id=role_id
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_invalid_user_returns_error(self, real_ctx):
        result = await get_user_role_targets(
            ctx=real_ctx, user_id="invalid-user-000", role_id="USER_ADMIN"
        )
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# Group target assign/unassign cycle
# ---------------------------------------------------------------------------

class TestGroupRoleTargetCycle:
    @pytest.mark.asyncio
    async def test_assign_and_unassign_group_target(self, real_ctx, first_user_with_role, first_group_id):
        """Assign a group target then immediately remove it — net-zero change."""
        user_id, role_id = first_user_with_role

        # Check if the group is already a target (skip if so, to avoid state mutation)
        existing = await list_user_group_role_targets(
            ctx=real_ctx, user_id=user_id, role_assignment_id=role_id
        )
        assert "error" not in existing
        existing_ids = {
            t.get("id") for t in existing["items"] if isinstance(t, dict)
        }
        if first_group_id in existing_ids:
            pytest.skip("Group is already a target — skipping to avoid state change")

        # Assign
        assigned = await assign_group_target_to_user_role(
            ctx=real_ctx,
            user_id=user_id,
            role_assignment_id=role_id,
            group_id=first_group_id,
        )
        assert isinstance(assigned, dict)
        assert "error" not in assigned, f"assign failed: {assigned.get('error')}"

        try:
            # Verify it appears in the list
            after = await list_user_group_role_targets(
                ctx=real_ctx, user_id=user_id, role_assignment_id=role_id
            )
            assert "error" not in after
            after_ids = {t.get("id") for t in after["items"] if isinstance(t, dict)}
            assert first_group_id in after_ids, "Group not found in targets after assign"
        finally:
            # Unassign — restore original state
            removed = await unassign_group_target_from_user_role(
                ctx=real_ctx,
                user_id=user_id,
                role_assignment_id=role_id,
                group_id=first_group_id,
            )
            assert "error" not in removed, f"unassign failed: {removed.get('error')}"
