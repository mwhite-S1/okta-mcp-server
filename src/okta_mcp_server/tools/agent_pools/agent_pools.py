# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Directory agent pool tools.

Covers /api/v1/agentPools — list agent pools and manage agent update schedules
for Active Directory (AD) and LDAP agents deployed on-premises.
"""

import json as _json
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call via the SDK request executor."""
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {})
    if error:
        return None, error
    response, response_body, error = await request_executor.execute(request)
    if error:
        return None, error
    if not response_body:
        return None, None
    if isinstance(response_body, str):
        try:
            response_body = _json.loads(response_body)
        except Exception:
            pass
    return response_body, None


# ---------------------------------------------------------------------------
# Agent Pools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_agent_pools(
    ctx: Context,
    limit_per_pool_type: Optional[int] = None,
    pool_type: Optional[str] = None,
    after: Optional[str] = None,
) -> dict:
    """List all agent pools in the organization.

    Agent pools group on-premises agents (AD/LDAP) that Okta communicates with
    for directory synchronization, password sync, and delegated authentication.
    Each pool represents a set of agents for a specific directory integration.

    Parameters:
        limit_per_pool_type (int, optional): Max results per pool type.
        pool_type (str, optional): Filter by agent type — one of:
            "AD" (Active Directory), "LDAP", "APP", "IDP", "MFA", "RADIUS",
            "TELEPHONY", "JAMF", "MOBILEIRON".
        after (str, optional): Pagination cursor for the next page.

    Returns:
        Dict with items (list of AgentPool objects) and total_fetched.
        Each pool includes: id, name, type, agents (with health and version info).
    """
    logger.info("Listing agent pools")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if limit_per_pool_type is not None:
            params["limitPerPoolType"] = str(limit_per_pool_type)
        if pool_type:
            params["poolType"] = pool_type
        if after:
            params["after"] = after
        path = "/api/v1/agentPools"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing agent pools: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} agent pool(s)")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing agent pools: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Agent Pool Updates
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_agent_pool_updates(
    ctx: Context,
    pool_id: str,
    scheduled: Optional[bool] = None,
) -> dict:
    """List all update jobs for a specific agent pool.

    Agent pool updates represent automated update schedules or manual update
    jobs for the on-premises agents in a pool. Updates move agents to a new
    version during a maintenance window.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        scheduled (bool, optional): If True, return only scheduled updates.
            If False, return only on-demand updates. Default: all updates.

    Returns:
        Dict with items (list of AgentPoolUpdate objects) and total_fetched.
        Each update includes: id, status, schedule, targetVersion, and agents.
    """
    logger.info(f"Listing updates for agent pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if scheduled is not None:
            params["scheduled"] = str(scheduled).lower()
        path = f"/api/v1/agentPools/{pool_id}/updates"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing updates for pool {pool_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} update(s) for pool {pool_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing agent pool updates: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_data: Dict[str, Any],
) -> dict:
    """Create a new update job for an agent pool.

    Creates either a scheduled or immediate update job for on-premises agents
    in the specified pool. The update moves agents to the latest or a specific
    target version.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_data (dict, required): Update job configuration. Key fields:
            - agentType (str): Agent type (e.g. "AD", "LDAP").
            - agents (list): List of agent objects to update: [{"id": "agent-id"}].
            - name (str): Display name for this update job.
            - schedule (dict, optional): Scheduled maintenance window:
                {"cron": "0 0 * * 0", "timezone": "America/Los_Angeles",
                 "maintenanceWindowDuration": 120}
            - targetVersion (str, optional): Specific version to update to.

    Returns:
        Dict containing the created AgentPoolUpdate object.
    """
    logger.info(f"Creating update for agent pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", f"/api/v1/agentPools/{pool_id}/updates", update_data)
        if error:
            logger.error(f"Error creating update for pool {pool_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Created update for pool {pool_id}: {(body or {}).get('id', 'unknown')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception creating agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_agent_pool_update_settings(
    ctx: Context,
    pool_id: str,
) -> dict:
    """Retrieve the automatic update settings for an agent pool.

    Returns the configured maintenance window and update schedule that applies
    to all agents in the pool by default.

    Parameters:
        pool_id (str, required): The ID of the agent pool.

    Returns:
        Dict containing the AgentPoolUpdateSetting with schedule configuration
        and continueOnError flag.
    """
    logger.info(f"Getting update settings for agent pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/agentPools/{pool_id}/updates/settings")
        if error:
            logger.error(f"Error getting update settings for pool {pool_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting agent pool update settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_agent_pool_update_settings(
    ctx: Context,
    pool_id: str,
    settings_data: Dict[str, Any],
) -> dict:
    """Update the automatic update settings for an agent pool.

    Configures the maintenance window schedule that governs when agents in
    the pool are automatically updated.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        settings_data (dict, required): Update settings configuration:
            - continueOnError (bool): Continue updating other agents if one fails.
            - latestVersion (str): The latest available agent version.
            - minimumSupportedVersion (str): Minimum supported version.
            - poolName (str): Display name for the pool.
            - poolType (str): Agent type ("AD", "LDAP", etc.).
            - releaseChannel (str): Release channel ("GA", "BETA").

    Returns:
        Dict containing the updated AgentPoolUpdateSetting.
    """
    logger.info(f"Updating update settings for agent pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/settings",
            settings_data,
        )
        if error:
            logger.error(f"Error updating settings for pool {pool_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Updated update settings for pool {pool_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception updating agent pool update settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Retrieve a specific update job for an agent pool.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the update job.

    Returns:
        Dict containing the AgentPoolUpdate with id, status, targetVersion,
        agents (with per-agent status), and schedule.
    """
    logger.info(f"Getting update {update_id} for agent pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/agentPools/{pool_id}/updates/{update_id}")
        if error:
            logger.error(f"Error getting update {update_id} for pool {pool_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
    update_data: Dict[str, Any],
) -> dict:
    """Update (replace) an agent pool update job's configuration.

    Modifies an existing update job, for example to change the maintenance
    window schedule before the update runs.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the update job to modify.
        update_data (dict, required): Updated job configuration (same schema as
            create_agent_pool_update).

    Returns:
        Dict containing the updated AgentPoolUpdate object.
    """
    logger.info(f"Updating update job {update_id} for agent pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}",
            update_data,
        )
        if error:
            logger.error(f"Error updating job {update_id} for pool {pool_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Updated job {update_id} for pool {pool_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception updating agent pool update job: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Delete an agent pool update job.

    Removes the update job. Only jobs that have not yet started or have
    been stopped can be deleted.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the update job to delete.

    Returns:
        Dict confirming the update job was deleted.
    """
    logger.info(f"Deleting update job {update_id} from pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/api/v1/agentPools/{pool_id}/updates/{update_id}")
        if error:
            logger.error(f"Error deleting update job {update_id} for pool {pool_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deleted update job {update_id} from pool {pool_id}")
        return {"message": f"Update job {update_id} deleted from agent pool {pool_id}."}
    except Exception as e:
        logger.error(f"Exception deleting agent pool update job: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def activate_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Activate (start) an agent pool update job.

    Triggers the update job to begin executing. Agents in the pool will be
    updated according to the job's schedule and configuration.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the update job to activate.

    Returns:
        Dict containing the updated AgentPoolUpdate with status SCHEDULED or RUNNING.
    """
    logger.info(f"Activating update job {update_id} for pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}/activate",
        )
        if error:
            logger.error(f"Error activating update job {update_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Activated update job {update_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception activating agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def deactivate_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Deactivate a scheduled agent pool update job.

    Cancels a scheduled update before it starts. The update remains in the
    system but will not execute on its next scheduled time.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the scheduled update job.

    Returns:
        Dict containing the updated AgentPoolUpdate with status INACTIVE.
    """
    logger.info(f"Deactivating update job {update_id} for pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}/deactivate",
        )
        if error:
            logger.error(f"Error deactivating update job {update_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deactivated update job {update_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception deactivating agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def pause_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Pause a running agent pool update job.

    Temporarily halts an in-progress update. Agents that have already been
    updated are not affected. Use resume_agent_pool_update to continue.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the running update job.

    Returns:
        Dict containing the updated AgentPoolUpdate with status PAUSED.
    """
    logger.info(f"Pausing update job {update_id} for pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}/pause",
        )
        if error:
            logger.error(f"Error pausing update job {update_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Paused update job {update_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception pausing agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def resume_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Resume a paused agent pool update job.

    Continues an update that was previously paused. The update resumes from
    where it stopped, updating remaining agents.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the paused update job.

    Returns:
        Dict containing the updated AgentPoolUpdate with status RUNNING.
    """
    logger.info(f"Resuming update job {update_id} for pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}/resume",
        )
        if error:
            logger.error(f"Error resuming update job {update_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Resumed update job {update_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception resuming agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def retry_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Retry a failed agent pool update job.

    Re-attempts an update job that previously failed. Only agents that failed
    in the previous run are retried — successfully updated agents are not
    updated again.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the failed update job.

    Returns:
        Dict containing the updated AgentPoolUpdate with status RUNNING.
    """
    logger.info(f"Retrying update job {update_id} for pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}/retry",
        )
        if error:
            logger.error(f"Error retrying update job {update_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Retrying update job {update_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception retrying agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stop_agent_pool_update(
    ctx: Context,
    pool_id: str,
    update_id: str,
) -> dict:
    """Stop a running agent pool update job.

    Permanently stops an in-progress update. Agents that have not yet been
    updated will remain on their current version. Unlike pause, this cannot
    be resumed — a new update job must be created.

    Parameters:
        pool_id (str, required): The ID of the agent pool.
        update_id (str, required): The ID of the running update job to stop.

    Returns:
        Dict containing the updated AgentPoolUpdate with status STOPPED.
    """
    logger.info(f"Stopping update job {update_id} for pool {pool_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/agentPools/{pool_id}/updates/{update_id}/stop",
        )
        if error:
            logger.error(f"Error stopping update job {update_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Stopped update job {update_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception stopping agent pool update: {type(e).__name__}: {e}")
        return {"error": str(e)}
