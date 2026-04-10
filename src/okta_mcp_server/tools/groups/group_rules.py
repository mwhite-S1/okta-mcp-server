# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Any, Dict, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DELETE_GROUP_RULE
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
async def list_group_rules(
    ctx: Context,
    limit: Optional[int] = 50,
    after: Optional[str] = None,
    search: Optional[str] = None,
    expand: Optional[str] = None,
) -> dict:
    """List all group rules for the Okta organization.

    Group rules dynamically add users to groups when they match defined conditions.
    Rules are created with INACTIVE status and must be explicitly activated.

    Parameters:
        limit (int, optional): Number of rules per page (1–200, default 50).
        after (str, optional): Pagination cursor for the next page.
        search (str, optional): Keyword to search rules by name.
        expand (str, optional): Set to "groupIdToGroupNameMap" to include group names.

    Returns:
        Dict with:
        - items: List of group rule objects
        - total_fetched: Count of rules returned
    """
    logger.info("Listing group rules")

    if limit is not None:
        limit = max(1, min(200, limit))

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if limit is not None:
            kwargs["limit"] = limit
        if after is not None:
            kwargs["after"] = after
        if search is not None:
            kwargs["search"] = search
        if expand is not None:
            kwargs["expand"] = expand

        rules, _, err = await client.list_group_rules(**kwargs)

        if err:
            logger.error(f"Okta API error listing group rules: {err}")
            return {"error": str(err)}

        items = [r.to_dict() for r in rules] if rules else []
        logger.info(f"Retrieved {len(items)} group rules")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing group rules: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_group_rule(ctx: Context, rule_data: Dict[str, Any]) -> dict:
    """Create a group rule that dynamically assigns users to a group based on conditions.

    Rules are created with INACTIVE status. Call activate_group_rule to enable them.

    Parameters:
        rule_data (dict, required): Rule definition containing:
            - name (str, required): Rule name (max 50 characters).
            - type (str, optional): Must be "group_rule" (default).
            - conditions (dict, optional): Conditions for the rule:
                - expression (dict): Okta expression language condition:
                    - type (str): Expression type (e.g. "urn:okta:expression:1.0")
                    - value (str): Expression string (e.g. 'user.department eq "Engineering"')
                - people (dict): People-based conditions with include/exclude user/group lists.
            - actions (dict, optional): Actions to take when conditions are met:
                - assignUserToGroups (dict): Contains groupIds (list of group IDs to assign).

    Example rule_data:
        {
            "name": "Engineering Group Rule",
            "type": "group_rule",
            "conditions": {
                "expression": {
                    "type": "urn:okta:expression:1.0",
                    "value": "user.department eq \\"Engineering\\""
                }
            },
            "actions": {
                "assignUserToGroups": {
                    "groupIds": ["00g1abc123"]
                }
            }
        }

    Returns:
        Dict containing the created group rule details.
    """
    logger.info(f"Creating group rule: {rule_data.get('name', 'unnamed')}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        rule, _, err = await client.create_group_rule(rule_data)

        if err:
            logger.error(f"Okta API error creating group rule: {err}")
            return {"error": str(err)}

        result = rule.to_dict()
        logger.info(f"Created group rule: {result.get('id', 'unknown')}")
        return result

    except Exception as e:
        logger.error(f"Exception creating group rule: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_rule_id", error_return_type="dict")
async def get_group_rule(ctx: Context, group_rule_id: str) -> dict:
    """Retrieve a specific group rule by ID.

    Parameters:
        group_rule_id (str, required): The ID of the group rule to retrieve.

    Returns:
        Dict containing the group rule details including name, status, conditions, and actions.
    """
    logger.info(f"Getting group rule: {group_rule_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        rule, _, err = await client.get_group_rule(group_rule_id)

        if err:
            logger.error(f"Okta API error getting group rule {group_rule_id}: {err}")
            return {"error": str(err)}

        return rule.to_dict()

    except Exception as e:
        logger.error(f"Exception getting group rule {group_rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_rule_id", error_return_type="dict")
async def replace_group_rule(ctx: Context, group_rule_id: str, rule_data: Dict[str, Any]) -> dict:
    """Replace (full update) a group rule by ID.

    The rule must be INACTIVE before it can be updated. The actions section
    (which groups users are assigned to) cannot be changed after creation.

    Parameters:
        group_rule_id (str, required): The ID of the group rule to replace.
        rule_data (dict, required): Complete updated rule definition. Follows the same
            structure as create_group_rule (name, type, conditions). The actions field
            is ignored by the API even if supplied.

    Returns:
        Dict containing the updated group rule details.
    """
    logger.info(f"Replacing group rule: {group_rule_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        rule, _, err = await client.replace_group_rule(group_rule_id, rule_data)

        if err:
            logger.error(f"Okta API error replacing group rule {group_rule_id}: {err}")
            return {"error": str(err)}

        result = rule.to_dict()
        logger.info(f"Replaced group rule: {group_rule_id}")
        return result

    except Exception as e:
        logger.error(f"Exception replacing group rule {group_rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_rule_id", error_return_type="dict")
async def delete_group_rule(
    ctx: Context,
    group_rule_id: str,
    remove_users: bool = False,
) -> dict:
    """Delete a group rule permanently.

    The user will be prompted for confirmation before deletion proceeds.
    If remove_users is True, users currently in the group due to this rule will
    also be removed from those groups.

    Parameters:
        group_rule_id (str, required): The ID of the group rule to delete.
        remove_users (bool, optional): If True, removes users from groups that were
            assigned by this rule. Default: False.

    Returns:
        Dict containing the result of the deletion.
    """
    logger.warning(f"Deletion requested for group rule {group_rule_id}")

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm deletion of group rule {group_rule_id}, please explicitly confirm. "
            f"Set remove_users={remove_users} to {'also remove' if remove_users else 'keep'} "
            f"group members assigned by this rule."
        ),
        "group_rule_id": group_rule_id,
        "remove_users": remove_users,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_GROUP_RULE.format(rule_id=group_rule_id),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for group rule {group_rule_id} — returning fallback prompt")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Group rule deletion cancelled for {group_rule_id}")
        return {"message": "Group rule deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.delete_group_rule(group_rule_id, remove_users=remove_users)

        if err:
            logger.error(f"Okta API error deleting group rule {group_rule_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deleted group rule: {group_rule_id}")
        return {"message": f"Group rule {group_rule_id} deleted successfully."}

    except Exception as e:
        logger.error(f"Exception deleting group rule {group_rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_rule_id", error_return_type="dict")
async def activate_group_rule(ctx: Context, group_rule_id: str) -> dict:
    """Activate a group rule.

    Once activated, the rule will evaluate conditions and automatically add matching
    users to the configured groups. The rule must be INACTIVE to activate.

    Parameters:
        group_rule_id (str, required): The ID of the group rule to activate.

    Returns:
        Dict confirming activation.
    """
    logger.info(f"Activating group rule: {group_rule_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.activate_group_rule(group_rule_id)

        if err:
            logger.error(f"Okta API error activating group rule {group_rule_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Activated group rule: {group_rule_id}")
        return {"message": f"Group rule {group_rule_id} activated successfully."}

    except Exception as e:
        logger.error(f"Exception activating group rule {group_rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_rule_id", error_return_type="dict")
async def deactivate_group_rule(ctx: Context, group_rule_id: str) -> dict:
    """Deactivate a group rule.

    Once deactivated, the rule will no longer evaluate conditions or add new users
    to groups. Existing group members are not removed. The rule must be ACTIVE to deactivate.

    Parameters:
        group_rule_id (str, required): The ID of the group rule to deactivate.

    Returns:
        Dict confirming deactivation.
    """
    logger.info(f"Deactivating group rule: {group_rule_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.deactivate_group_rule(group_rule_id)

        if err:
            logger.error(f"Okta API error deactivating group rule {group_rule_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deactivated group rule: {group_rule_id}")
        return {"message": f"Group rule {group_rule_id} deactivated successfully."}

    except Exception as e:
        logger.error(f"Exception deactivating group rule {group_rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
