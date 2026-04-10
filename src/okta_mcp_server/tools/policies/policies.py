# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Any, Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeactivateConfirmation, DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import (
    DEACTIVATE_POLICY,
    DEACTIVATE_POLICY_RULE,
    DELETE_POLICY,
    DELETE_POLICY_RULE,
)
from okta_mcp_server.utils.serialize import to_dict
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
async def list_policies(
    ctx: Context,
    type: str,
    status: Optional[str] = None,
    q: Optional[str] = None,
    limit: Optional[int] = 20,
    after: Optional[str] = None,
) -> Dict[str, Any]:
    """List all the policies from the Okta organization.

    Parameters:
        type (str, required): Specifies the type of policy to return. Available policy types are:
            OKTA_SIGN_ON, PASSWORD, MFA_ENROLL, IDP_DISCOVERY, ACCESS_POLICY,
            PROFILE_ENROLLMENT, POST_AUTH_SESSION, ENTITY_RISK
        status (str, optional): Refines the query by the status of the policy - ACTIVE or INACTIVE.
        q (str, optional): A query string to search policies by name.
        limit (int, optional): Number of results to return (min 20, max 100).
        after (str, optional): Specifies the pagination cursor for the next page of policies.

    Returns:
        Dict containing:
            - policies (List[Dict]): List of policy dictionaries, each containing policy details
            - error (str): Error message if the operation fails
    """
    logger.info("Listing policies from Okta organization")
    logger.debug(f"Type: '{type}', Status: '{status}', Q: '{q}', limit: {limit}")

    # Validate limit parameter range
    if limit is not None:
        if limit < 20:
            logger.warning(f"Limit {limit} is below minimum (20), setting to 20")
            limit = 20
        elif limit > 100:
            logger.warning(f"Limit {limit} exceeds maximum (100), setting to 100")
            limit = 100

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        okta_client = await get_okta_client(manager)
        params = {"type": type, "limit": limit}
        if status:
            params["status"] = status
        if q:
            params["q"] = q
        if after:
            params["after"] = after

        logger.debug("Calling Okta API to list policies")
        policies, _, err = await okta_client.list_policies(params)

        if err:
            logger.error(f"Error listing policies: {err}")
            return {"error": str(err)}

        if not policies:
            logger.info("No policies found")
            return {"policies": []}

        logger.info(f"Successfully retrieved {len(policies)} policies")
        return {
            "policies": [to_dict(policy) for policy in policies],
        }

    except Exception as e:
        logger.error(f"Exception listing policies: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def get_policy(ctx: Context, policy_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific policy by ID.

    Parameters:
        policy_id (str, required): The ID of the policy to retrieve.

    Returns:
        Dict containing the policy details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        policy, _, err = await okta_client.get_policy(policy_id)

        if err:
            logger.error(f"Error getting policy {policy_id}: {err}")
            return {"error": str(err)}

        return to_dict(policy) if policy else None

    except Exception as e:
        logger.error(f"Exception getting policy: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_policy(ctx: Context, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new policy.

    Parameters:
        policy_data (dict, required): The policy configuration containing:
            - type (str, required): Policy type (OKTA_SIGN_ON, PASSWORD, MFA_ENROLL, ACCESS_POLICY, PROFILE_ENROLLMENT,
            POST_AUTH_SESSION, ENTITY_RISK, DEVICE_SIGNAL_COLLECTION)
            - name (str, required): Policy name
            - description (str, optional): Policy description
            - status (str, optional): ACTIVE or INACTIVE (default: ACTIVE)
            - priority (int, optional): Priority of the policy
            - conditions (dict, optional): Policy conditions
            - settings (dict, optional): Policy-specific settings

    Returns:
        Dict containing the created policy details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        policy, _, err = await okta_client.create_policy(policy_data)

        if err:
            logger.error(f"Error creating policy: {err}")
            return {"error": str(err)}

        return to_dict(policy) if policy else None

    except Exception as e:
        logger.error(f"Exception creating policy: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def update_policy(ctx: Context, policy_id: str, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing policy.

    Parameters:
        policy_id (str, required): The ID of the policy to update.
        policy_data (dict, required): The updated policy configuration.

    Returns:
        Dict containing the updated policy details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        policy, _, err = await okta_client.update_policy(policy_id, policy_data)

        if err:
            logger.error(f"Error updating policy {policy_id}: {err}")
            return {"error": str(err)}

        return to_dict(policy) if policy else None

    except Exception as e:
        logger.error(f"Exception updating policy: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def delete_policy(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """Delete a policy.

    The user will be asked for confirmation before the deletion proceeds.

    Parameters:
        policy_id (str, required): The ID of the policy to delete.

    Returns:
        Dict with success status.
    """
    logger.warning(f"Deletion requested for policy {policy_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_POLICY.format(policy_id=policy_id),
        schema=DeleteConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Policy deletion cancelled for {policy_id}")
        return {"message": "Policy deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        okta_client = await get_okta_client(manager)
        _, err = await okta_client.delete_policy(policy_id)

        if err:
            logger.error(f"Error deleting policy {policy_id}: {err}")
            return {"error": str(err)}

        return {"success": True, "message": f"Policy {policy_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting policy: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def activate_policy(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """Activate a policy.

    Parameters:
        policy_id (str, required): The ID of the policy to activate.

    Returns:
        Dict with success status.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        _, err = await okta_client.activate_policy(policy_id)

        if err:
            logger.error(f"Error activating policy {policy_id}: {err}")
            return {"error": str(err)}

        return {"success": True, "message": f"Policy {policy_id} activated successfully"}

    except Exception as e:
        logger.error(f"Exception activating policy: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def deactivate_policy(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """Deactivate a policy.

    The user will be asked for confirmation before the deactivation proceeds.

    Parameters:
        policy_id (str, required): The ID of the policy to deactivate.

    Returns:
        Dict with success status.
    """
    logger.info(f"Deactivation requested for policy {policy_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=DEACTIVATE_POLICY.format(policy_id=policy_id),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Policy deactivation cancelled for {policy_id}")
        return {"message": "Policy deactivation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        okta_client = await get_okta_client(manager)
        _, err = await okta_client.deactivate_policy(policy_id)

        if err:
            logger.error(f"Error deactivating policy {policy_id}: {err}")
            return {"error": str(err)}

        return {"success": True, "message": f"Policy {policy_id} deactivated successfully"}

    except Exception as e:
        logger.error(f"Exception deactivating policy: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def list_policy_rules(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """List all rules for a specific policy.

    Parameters:
        policy_id (str, required): The ID of the policy.

    Returns:
        Dict containing:
            - rules (List[Dict]): List of policy rule dictionaries
            - has_next (bool): Whether there are more results
            - next_page_token (Optional[str]): Token for next page
            - error (str): Error message if the operation fails
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        rules, resp, err = await okta_client.list_policy_rules(policy_id)

        if err:
            logger.error(f"Error listing policy rules: {err}")
            return {"error": str(err)}

        if not rules:
            logger.info("No policy rules found")
            return {"rules": []}

        return {
            "rules": [to_dict(rule) for rule in rules],
            "has_next": resp.has_next() if resp else False,
            "next_page_token": resp.get_next_page_token() if resp and resp.has_next() else None,
        }

    except Exception as e:
        logger.error(f"Exception listing policy rules: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "rule_id", error_return_type="dict")
async def get_policy_rule(ctx: Context, policy_id: str, rule_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific policy rule.

    Parameters:
        policy_id (str, required): The ID of the policy.
        rule_id (str, required): The ID of the rule.

    Returns:
        Dict containing the policy rule details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        rule, _, err = await okta_client.get_policy_rule(policy_id, rule_id)

        if err:
            logger.error(f"Error getting policy rule: {err}")
            return {"error": str(err)}

        return to_dict(rule) if rule else None

    except Exception as e:
        logger.error(f"Exception getting policy rule: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def create_policy_rule(ctx: Context, policy_id: str, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new rule for a policy.

    Parameters:
        policy_id (str, required): The ID of the policy.
        rule_data (dict, required): The rule configuration containing:
            - name (str, required): Rule name
            - priority (int, optional): Priority of the rule
            - status (str, optional): ACTIVE or INACTIVE
            - conditions (dict, optional): Rule conditions
            - actions (dict, optional): Rule actions

    Returns:
        Dict containing the created rule details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        rule, _, err = await okta_client.create_policy_rule(policy_id, rule_data)

        if err:
            logger.error(f"Error creating policy rule: {err}")
            return {"error": str(err)}

        return to_dict(rule) if rule else None

    except Exception as e:
        logger.error(f"Exception creating policy rule: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "rule_id", error_return_type="dict")
async def update_policy_rule(
    ctx: Context, policy_id: str, rule_id: str, rule_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update an existing policy rule.

    Parameters:
        policy_id (str, required): The ID of the policy.
        rule_id (str, required): The ID of the rule to update.
        rule_data (dict, required): The updated rule configuration.

    Returns:
        Dict containing the updated rule details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        rule, _, err = await okta_client.update_policy_rule(policy_id, rule_id, rule_data)

        if err:
            logger.error(f"Error updating policy rule: {err}")
            return {"error": str(err)}

        return to_dict(rule) if rule else None

    except Exception as e:
        logger.error(f"Exception updating policy rule: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "rule_id", error_return_type="dict")
async def delete_policy_rule(ctx: Context, policy_id: str, rule_id: str) -> Dict[str, Any]:
    """Delete a policy rule.

    The user will be asked for confirmation before the deletion proceeds.

    Parameters:
        policy_id (str, required): The ID of the policy.
        rule_id (str, required): The ID of the rule to delete.

    Returns:
        Dict with success status.
    """
    logger.warning(f"Deletion requested for policy rule {rule_id} in policy {policy_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_POLICY_RULE.format(rule_id=rule_id, policy_id=policy_id),
        schema=DeleteConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Policy rule deletion cancelled for {rule_id}")
        return {"message": "Policy rule deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        okta_client = await get_okta_client(manager)
        _, err = await okta_client.delete_policy_rule(policy_id, rule_id)

        if err:
            logger.error(f"Error deleting policy rule: {err}")
            return {"error": str(err)}

        return {"success": True, "message": f"Rule {rule_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting policy rule: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "rule_id", error_return_type="dict")
async def activate_policy_rule(ctx: Context, policy_id: str, rule_id: str) -> Dict[str, Any]:
    """Activate a policy rule.

    Parameters:
        policy_id (str, required): The ID of the policy.
        rule_id (str, required): The ID of the rule to activate.

    Returns:
        Dict with success status.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    okta_client = await get_okta_client(manager)

    try:
        _, err = await okta_client.activate_policy_rule(policy_id, rule_id)

        if err:
            logger.error(f"Error activating policy rule: {err}")
            return {"error": str(err)}

        return {"success": True, "message": f"Rule {rule_id} activated successfully"}

    except Exception as e:
        logger.error(f"Exception activating policy rule: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "rule_id", error_return_type="dict")
async def deactivate_policy_rule(ctx: Context, policy_id: str, rule_id: str) -> Dict[str, Any]:
    """Deactivate a policy rule.

    Parameters:
        policy_id (str, required): The ID of the policy.
        rule_id (str, required): The ID of the rule to deactivate.

    Returns:
        Dict with success status.
    """
    logger.info(f"Deactivation requested for policy rule {rule_id} in policy {policy_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=DEACTIVATE_POLICY_RULE.format(rule_id=rule_id, policy_id=policy_id),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Policy rule deactivation cancelled for {rule_id}")
        return {"message": "Policy rule deactivation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        okta_client = await get_okta_client(manager)
        _, err = await okta_client.deactivate_policy_rule(policy_id, rule_id)

        if err:
            logger.error(f"Error deactivating policy rule: {err}")
            return {"error": str(err)}

        return {"success": True, "message": f"Rule {rule_id} deactivated successfully"}

    except Exception as e:
        logger.error(f"Exception deactivating policy rule: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def clone_policy(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """Clone an existing policy.

    Creates a new copy of the specified policy with all its settings.

    Parameters:
        policy_id (str, required): The ID of the policy to clone.

    Returns:
        Dict containing the cloned policy details.
    """
    logger.info(f"Cloning policy {policy_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        policy, _, err = await okta_client.clone_policy(policy_id)
        if err:
            logger.error(f"Error cloning policy {policy_id}: {err}")
            return {"error": str(err)}
        logger.info(f"Cloned policy {policy_id} → new policy created")
        return to_dict(policy) if policy else {}
    except Exception as e:
        logger.error(f"Exception cloning policy {policy_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_policy_simulation(
    ctx: Context,
    simulation_body: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Simulate policy evaluation for given contexts.

    Evaluates policies and policy rules based on existing configuration without
    actually enforcing them. Useful for testing how sign-on or MFA policies
    behave under different conditions.

    Parameters:
        simulation_body (list, required): List of simulation request objects, each containing:
            - policyType (list of str): Policy types to simulate, e.g. ["OKTA_SIGN_ON", "MFA_ENROLL"].
            - appInstance (str, optional): Application instance ID to simulate against.
            - policyContext (dict, optional): Simulation context with fields:
                - groups (dict): Group membership context (include list of group IDs).
                - risk (dict): Risk context (e.g. {"level": "LOW"}).
                - zones (dict): Network zone context.
                - device (dict): Device context.
                - user (dict): User context (e.g. {"id": "<userId>"}).

    Returns:
        Dict with items (list of simulation results per policy type).
    """
    logger.info("Creating policy simulation")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        results, _, err = await okta_client.create_policy_simulation(simulation_body)
        if err:
            logger.error(f"Error running policy simulation: {err}")
            return {"error": str(err)}
        items = [to_dict(r) if r else r for r in (results or [])]
        logger.info(f"Policy simulation completed with {len(items)} result(s)")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception running policy simulation: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def list_policy_apps(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """List all applications mapped to a policy.

    Note: This endpoint is deprecated. Use list_policy_mappings instead.

    Parameters:
        policy_id (str, required): The ID of the policy.

    Returns:
        Dict with items (list of application objects mapped to the policy).
    """
    logger.info(f"Listing apps for policy {policy_id} (deprecated endpoint)")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        apps, _, err = await okta_client.list_policy_apps(policy_id)
        if err:
            logger.error(f"Error listing apps for policy {policy_id}: {err}")
            return {"error": str(err)}
        items = [to_dict(a) if a else a for a in (apps or [])]
        logger.info(f"Retrieved {len(items)} app(s) for policy {policy_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing apps for policy {policy_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def list_policy_mappings(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """List all resource mappings for a policy.

    Returns all resources (such as app sign-on policies) currently mapped to
    the specified policy.

    Parameters:
        policy_id (str, required): The ID of the policy.

    Returns:
        Dict with items (list of PolicyMapping objects).
    """
    logger.info(f"Listing mappings for policy {policy_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        mappings, _, err = await okta_client.list_policy_mappings(policy_id)
        if err:
            logger.error(f"Error listing mappings for policy {policy_id}: {err}")
            return {"error": str(err)}
        items = [to_dict(m) if m else m for m in (mappings or [])]
        logger.info(f"Retrieved {len(items)} mapping(s) for policy {policy_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing mappings for policy {policy_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", error_return_type="dict")
async def map_resource_to_policy(
    ctx: Context,
    policy_id: str,
    resource_id: str,
    resource_type: str = "ACCESS_POLICY",
) -> Dict[str, Any]:
    """Map a resource to a policy.

    Associates a resource (such as an app sign-on policy) with a global
    sign-on policy.

    Parameters:
        policy_id (str, required): The ID of the policy to map to.
        resource_id (str, required): The ID of the resource (e.g. app sign-on policy ID).
        resource_type (str, optional): The type of resource. Only valid value: "ACCESS_POLICY".
            Default: "ACCESS_POLICY".

    Returns:
        Dict containing the created PolicyMapping.
    """
    logger.info(f"Mapping resource {resource_id} ({resource_type}) to policy {policy_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        body = {"resourceId": resource_id, "resourceType": resource_type}
        mapping, _, err = await okta_client.map_resource_to_policy(policy_id, body)
        if err:
            logger.error(f"Error mapping resource to policy {policy_id}: {err}")
            return {"error": str(err)}
        logger.info(f"Mapped resource {resource_id} to policy {policy_id}")
        return to_dict(mapping) if mapping else {}
    except Exception as e:
        logger.error(f"Exception mapping resource to policy {policy_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "mapping_id", error_return_type="dict")
async def get_policy_mapping(
    ctx: Context,
    policy_id: str,
    mapping_id: str,
) -> Dict[str, Any]:
    """Retrieve a specific resource mapping for a policy.

    Parameters:
        policy_id (str, required): The ID of the policy.
        mapping_id (str, required): The ID of the resource mapping.

    Returns:
        Dict containing the PolicyMapping details.
    """
    logger.info(f"Getting mapping {mapping_id} for policy {policy_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        mapping, _, err = await okta_client.get_policy_mapping(policy_id, mapping_id)
        if err:
            logger.error(f"Error getting mapping {mapping_id} for policy {policy_id}: {err}")
            return {"error": str(err)}
        return to_dict(mapping) if mapping else {}
    except Exception as e:
        logger.error(f"Exception getting policy mapping: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("policy_id", "mapping_id", error_return_type="dict")
async def delete_policy_resource_mapping(
    ctx: Context,
    policy_id: str,
    mapping_id: str,
) -> Dict[str, Any]:
    """Delete a resource mapping from a policy.

    Removes the association between a resource and the specified policy.

    Parameters:
        policy_id (str, required): The ID of the policy.
        mapping_id (str, required): The ID of the resource mapping to delete.

    Returns:
        Dict confirming deletion.
    """
    logger.warning(f"Deleting mapping {mapping_id} from policy {policy_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        okta_client = await get_okta_client(manager)
        _, _, err = await okta_client.delete_policy_resource_mapping(policy_id, mapping_id)
        if err:
            logger.error(f"Error deleting mapping {mapping_id} from policy {policy_id}: {err}")
            return {"error": str(err)}
        logger.info(f"Deleted mapping {mapping_id} from policy {policy_id}")
        return {"message": f"Resource mapping {mapping_id} deleted from policy {policy_id}."}
    except Exception as e:
        logger.error(f"Exception deleting policy mapping: {e}")
        return {"error": str(e)}
