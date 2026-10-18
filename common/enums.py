"""Allowed values shared by all services, so every service uses the exact same strings."""

SEVERITIES = ("Low", "Medium", "High", "Critical")          # incidents, threats, vulns, assets (criticality), playbooks
LOG_SEVERITIES = ("Information", "Warning", "Error", "Critical")

ACCOUNT_STATUSES = ("Active", "Inactive", "Suspended")
ASSET_STATUSES = ("Active", "Inactive", "Under Maintenance")
ACTION_STATUSES = ("Pending", "In Progress", "Completed")
NOTIFICATION_STATUSES = ("Unread", "Read")

# Lifecycles: each status may only move to the next one in the tuple.
INCIDENT_FLOW = ("Open", "Under Investigation", "Mitigated", "Resolved", "Closed")
VULNERABILITY_FLOW = ("Open", "Under Investigation", "In Progress", "Resolved", "Closed")

THREAT_TYPES = ("IP Address", "Domain", "File Hash", "Malware Signature", "Other")
NOTIFICATION_TYPES = (
    "Incident Assignment",
    "Security Alert",
    "System Notification",
    "Threat Alert",
    "Vulnerability Alert",
)


def next_status(flow, current):
    """Return the only status allowed after `current` in `flow`, or None if it is the last one."""
    index = flow.index(current)
    return flow[index + 1] if index + 1 < len(flow) else None
