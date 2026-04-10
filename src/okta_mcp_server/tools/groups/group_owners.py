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
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
@validate_ids("group_id", error_return_type="dict")
async def list_group_owners(
    ctx: Context,
    group_id: str,
    search: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all owners of a group.

    Returns the users and groups that are designated as owners of the specified
    Okta group.

    Parameters:
        group_id (str, required): The ID of the group.
        search (str, optional): Filter owners by display name or other attributes.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max number of results per page.

    Returns:
        Dict with items (list of GroupOwner objects) and total_fetched.
    """
    logger.info(f"Listing owners for group {group_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if search is not None:
            kwargs["search"] = search
        if after is not None:
            kwargs["after"] = after
        if limit is not None:
            kwargs["limit"] = limit

        owners, _, err = await client.list_group_owners(group_id, **kwargs)

        if err:
            logger.error(f"Error listing owners for group {group_id}: {err}")
            return {"error": str(err)}

        items = [o.to_dict() if hasattr(o, "to_dict") else o for o in (owners or [])]
        logger.info(f"Retrieved {len(items)} owner(s) for group {group_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing group owners for {group_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_id", error_return_type="dict")
async def assign_group_owner(
    ctx: Context,
    group_id: str,
    owner: Dict[str, Any],
) -> dict:
    """Assign an owner to a group.

    Designates a user or group as an owner of the specified Okta group. Owners
    can manage the group's membership and settings.

    Parameters:
        group_id (str, required): The ID of the group.
        owner (dict, required): Owner assignment configuration:
            - id (str, required): The ID of the user or group to assign as owner.
            - type (str, required): The type of owner — "USER" or "GROUP".

    Returns:
        Dict containing the created GroupOwner assignment.
    """
    logger.info(f"Assigning owner to group {group_id}: {owner}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        result, _, err = await client.assign_group_owner(group_id, owner)

        if err:
            logger.error(f"Error assigning owner to group {group_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
        logger.info(f"Assigned owner {owner.get('id', 'unknown')} to group {group_id}")
        return out

    except Exception as e:
        logger.error(f"Exception assigning group owner for {group_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("group_id", "owner_id", error_return_type="dict")
async def delete_group_owner(
    ctx: Context,
    group_id: str,
    owner_id: str,
) -> dict:
    """Remove an owner from a group.

    The user will be prompted for confirmation before the removal proceeds.

    Parameters:
        group_id (str, required): The ID of the group.
        owner_id (str, required): The ID of the owner (user or group) to remove.

    Returns:
        Dict confirming the owner was removed.
    """
    logger.warning(f"Removal requested for owner {owner_id} from group {group_id}")

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm removal of owner {owner_id} from group {group_id}, "
            f"please explicitly confirm this action."
        ),
        "group_id": group_id,
        "owner_id": owner_id,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=(
            f"Are you sure you want to remove owner {owner_id} from group {group_id}? "
            f"This action cannot be undone."
        ),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for group owner removal — returning fallback prompt")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Group owner removal cancelled for owner {owner_id} from group {group_id}")
        return {"message": "Group owner removal cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.delete_group_owner(group_id, owner_id)

        if err:
            logger.error(f"Error removing owner {owner_id} from group {group_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Removed owner {owner_id} from group {group_id}")
        return {"message": f"Owner {owner_id} removed from group {group_id}."}

    except Exception as e:
        logger.error(f"Exception removing group owner {owner_id} from {group_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
