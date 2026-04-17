# Runbook: Governance — Certifications & Security Access Reviews

Covers `governance/certifications.py` — 17 tools total.

⏭️ All tests skip if Okta IGA is not enabled or the caller lacks certification management permissions.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$FIRST_CAMPAIGN_ID` | `list_certification_campaigns(limit=1)` → first `id` |
| `$FIRST_SAR_ID` | `list_security_access_reviews(limit=1)` → first `id` |

---

## Section 1 — Certification Campaigns

### T-1: list_certification_campaigns

**Call:** `list_certification_campaigns(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_CAMPAIGN_ID` = `items[0]["id"]` if non-empty

---

### T-2: get_certification_campaign

⏭️ Skip if `$FIRST_CAMPAIGN_ID` not set.

**Call:** `get_certification_campaign(campaign_id=$FIRST_CAMPAIGN_ID)`  
**Expect:** `result["id"] == $FIRST_CAMPAIGN_ID`; has `name`, `status`; no `error`

---

### T-3: 🔁 create_certification_campaign → launch → end → delete

⚠️ Launching a campaign sends review notifications to reviewers. Use only in sandbox.

**CREATE:**
```
create_certification_campaign(
  name="runbook-test-campaign",
  description="Created by CRUD runbook",
  reviewer_type="MANAGER",
  resource_type="APP",
  resource_id=$FIRST_APP_ID
)
```
**Expect:** `result["id"]` → `$NEW_CAMPAIGN_ID`; `result["status"] == "DRAFT"` or `"PENDING"`

**GET:** `get_certification_campaign(campaign_id=$NEW_CAMPAIGN_ID)` → verify it exists

**LAUNCH:** `launch_certification_campaign(campaign_id=$NEW_CAMPAIGN_ID)`  
⏭️ Skip launch in production — it emails real reviewers.  
**Expect:** no `error`; `status` changes to `"ACTIVE"`

**END (cleanup):** `end_certification_campaign(campaign_id=$NEW_CAMPAIGN_ID)`  
**Expect:** no `error`

**DELETE (cleanup):** `delete_certification_campaign(campaign_id=$NEW_CAMPAIGN_ID)`  
**Expect:** no `error`

---

## Section 2 — Certification Reviews

### T-4: list_certification_reviews

⏭️ Skip if `$FIRST_CAMPAIGN_ID` not set or campaign has no reviews.

**Call:** `list_certification_reviews(campaign_id=$FIRST_CAMPAIGN_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_REVIEW_ID` = `items[0]["id"]` if non-empty

---

### T-5: get_certification_review

⏭️ Skip if `$FIRST_REVIEW_ID` not set.

**Call:** `get_certification_review(campaign_id=$FIRST_CAMPAIGN_ID, review_id=$FIRST_REVIEW_ID)`  
**Expect:** `result["id"] == $FIRST_REVIEW_ID`; no `error`

---

### T-6: reassign_certification_review

⏭️ Skip unless running in sandbox — reassignment notifies the new reviewer.

**Call:** `reassign_certification_review(campaign_id=$FIRST_CAMPAIGN_ID, review_id=$FIRST_REVIEW_ID, reviewer_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

## Section 3 — Certification Settings

### T-7: get_certification_settings

**Call:** `get_certification_settings()`  
**Expect:** no `error`; result is a dict

---

### T-8: update_certification_settings (no-op)

**Call:** `update_certification_settings(<current settings from T-7>)`  
**Expect:** no `error`

---

## Section 4 — Security Access Reviews (SAR)

### T-9: list_security_access_reviews

**Call:** `list_security_access_reviews(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_SAR_ID` = `items[0]["id"]` if non-empty

---

### T-10: get_security_access_review

⏭️ Skip if `$FIRST_SAR_ID` not set.

**Call:** `get_security_access_review(review_id=$FIRST_SAR_ID)`  
**Expect:** `result["id"] == $FIRST_SAR_ID`; no `error`

---

### T-11: get_security_access_review_stats

⏭️ Skip if `$FIRST_SAR_ID` not set.

**Call:** `get_security_access_review_stats(review_id=$FIRST_SAR_ID)`  
**Expect:** no `error`; result has totals/counts

---

### T-12: 🔁 create_security_access_review → update → summarize

**CREATE:**
```
create_security_access_review(
  name="runbook-test-sar",
  resource_type="APP",
  resource_id=$FIRST_APP_ID,
  reviewer_type="MANAGER"
)
```
**Expect:** `result["id"]` → `$NEW_SAR_ID`; no `error`

**UPDATE:** `update_security_access_review(review_id=$NEW_SAR_ID, status="ACTIVE")`  
⏭️ Skip status change if workflow doesn't allow it.

**SUMMARIZE:** `create_security_access_review_summary(review_id=$NEW_SAR_ID)`  
**Expect:** no `error`

---

### T-13: list_security_access_review_actions

⏭️ Skip if `$FIRST_SAR_ID` not set.

**Call:** `list_security_access_review_actions(review_id=$FIRST_SAR_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_SAR_ACTION_ID` = `items[0]["id"]` if non-empty

---

### T-14: submit_security_access_review_action

⏭️ Skip unless `$FIRST_SAR_ACTION_ID` is set and the caller is the assigned reviewer.

**Call:** `submit_security_access_review_action(review_id=$FIRST_SAR_ID, action_id=$FIRST_SAR_ACTION_ID, decision="APPROVE")`  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Campaigns | T-1 – T-3 | Create/launch/end/delete; ⚠️ launch emails reviewers |
| Reviews | T-4 – T-6 | Read + reassign; reassign notifies new reviewer |
| Cert Settings | T-7 – T-8 | Read + no-op update |
| SAR | T-9 – T-14 | Create/update/summarize/action cycle |
