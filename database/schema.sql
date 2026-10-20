-- Developed by: Marc Bteich
-- SQLite development schema. Run on a NEW database; never drops existing data.
-- Mirrors Elie Medawar's existing models, including their column and FK names.
-- Dates are UTC. ORM defaults are supplied by Python when services write records.
PRAGMA foreign_keys = ON;
BEGIN;

CREATE TABLE users (
 id INTEGER PRIMARY KEY, full_name VARCHAR(100) NOT NULL,
 username VARCHAR(30) NOT NULL UNIQUE, email VARCHAR(120) NOT NULL UNIQUE,
 password_hash VARCHAR(60) NOT NULL, department VARCHAR(100) NOT NULL,
 role VARCHAR(20) NOT NULL CHECK(role IN ('admin','analyst','user','auditor')),
 account_status VARCHAR(20) NOT NULL CHECK(account_status IN ('Active','Inactive','Suspended')),
 created_at DATETIME NOT NULL, last_login DATETIME
);
CREATE TABLE assets (
 id INTEGER PRIMARY KEY, asset_name VARCHAR(150) NOT NULL CHECK(length(trim(asset_name)) > 0),
 asset_type VARCHAR(30) NOT NULL CHECK(asset_type IN ('Server','Workstation','Database','Application','Network Device','Cloud Resource')),
 ip_address VARCHAR(45) NOT NULL, operating_system VARCHAR(100),
 owner_id INTEGER NOT NULL REFERENCES users(id), department VARCHAR(100) NOT NULL,
 location VARCHAR(150),
 criticality VARCHAR(10) NOT NULL CHECK(criticality IN ('Low','Medium','High','Critical')),
 status VARCHAR(25) NOT NULL CHECK(status IN ('Active','Inactive','Under Maintenance'))
);
CREATE INDEX ix_assets_owner_id ON assets(owner_id);
CREATE TABLE incidents (
 id INTEGER PRIMARY KEY, title VARCHAR(150) NOT NULL, description VARCHAR(2000) NOT NULL,
 category VARCHAR(30) NOT NULL CHECK(category IN ('Malware','Unauthorized Access','Phishing','Data Leakage','Account Compromise','Denial of Service','Other')),
 severity VARCHAR(10) NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 reporter_id INTEGER NOT NULL REFERENCES users(id),
 asset_id INTEGER REFERENCES assets(id) ON DELETE SET NULL,
 assigned_analyst_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 status VARCHAR(25) NOT NULL CHECK(status IN ('Open','Under Investigation','Mitigated','Resolved','Closed')),
 created_at DATETIME NOT NULL, resolved_at DATETIME
);
CREATE INDEX ix_incidents_reporter_id ON incidents(reporter_id);
CREATE INDEX ix_incidents_asset_id ON incidents(asset_id);
CREATE INDEX ix_incidents_assigned_analyst_id ON incidents(assigned_analyst_id);
CREATE TABLE investigation_notes (
 id INTEGER PRIMARY KEY, incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
 analyst_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 content VARCHAR(2000) NOT NULL, created_at DATETIME NOT NULL
);
CREATE INDEX ix_investigation_notes_incident_id ON investigation_notes(incident_id);
CREATE TABLE threats (
 id INTEGER PRIMARY KEY, threat_type VARCHAR(30) NOT NULL CHECK(threat_type IN ('IP Address','Domain','File Hash','Malware Signature','Other')),
 threat_value VARCHAR(255) NOT NULL, description VARCHAR(2000) NOT NULL,
 severity VARCHAR(10) NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 source VARCHAR(150) NOT NULL, date_added DATETIME NOT NULL,
 CONSTRAINT uq_threat_type_value UNIQUE(threat_type, threat_value)
);
CREATE TABLE logs (
 id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 username VARCHAR(30), action VARCHAR(50) NOT NULL, description VARCHAR(500) NOT NULL,
 severity VARCHAR(20) NOT NULL CHECK(severity IN ('Information','Warning','Error','Critical')),
 related_service VARCHAR(30) NOT NULL, timestamp DATETIME NOT NULL
);
CREATE INDEX ix_logs_user_id ON logs(user_id);
CREATE INDEX ix_logs_action ON logs(action);
CREATE INDEX ix_logs_timestamp ON logs(timestamp);
CREATE TABLE vulnerabilities (
 id INTEGER PRIMARY KEY, title VARCHAR(150) NOT NULL, description VARCHAR(2000) NOT NULL,
 cve_id VARCHAR(40) NOT NULL, cvss_score NUMERIC(3,1) NOT NULL CHECK(cvss_score BETWEEN 0 AND 10),
 severity VARCHAR(10) NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 asset_id INTEGER NOT NULL REFERENCES assets(id), discovery_source VARCHAR(150) NOT NULL,
 status VARCHAR(25) NOT NULL CHECK(status IN ('Open','Under Investigation','In Progress','Resolved','Closed')),
 created_at DATETIME NOT NULL, resolution_date DATETIME
);
CREATE INDEX ix_vulnerabilities_asset_id ON vulnerabilities(asset_id);
CREATE TABLE notifications (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 title VARCHAR(150) NOT NULL, message VARCHAR(1000) NOT NULL,
 notification_type VARCHAR(30) NOT NULL CHECK(notification_type IN ('Incident Assignment','Security Alert','System Notification','Threat Alert','Vulnerability Alert')),
 severity VARCHAR(10) NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 status VARCHAR(10) NOT NULL CHECK(status IN ('Unread','Read')),
 created_at DATETIME NOT NULL, read_at DATETIME
);
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE TABLE playbooks (
 id INTEGER PRIMARY KEY, name VARCHAR(150) NOT NULL, description VARCHAR(2000) NOT NULL,
 incident_category VARCHAR(30) NOT NULL CHECK(incident_category IN ('Malware','Unauthorized Access','Phishing','Data Leakage','Account Compromise','Denial of Service','Other')),
 severity VARCHAR(10) NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 created_by INTEGER NOT NULL REFERENCES users(id), created_at DATETIME NOT NULL
);
CREATE TABLE response_actions (
 id INTEGER PRIMARY KEY, playbook_id INTEGER NOT NULL REFERENCES playbooks(id) ON DELETE CASCADE,
 description VARCHAR(2000) NOT NULL, step_number INTEGER NOT NULL CHECK(step_number > 0),
 status VARCHAR(20) NOT NULL CHECK(status IN ('Pending','In Progress','Completed')),
 assigned_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, completion_date DATETIME,
 CONSTRAINT uq_action_step UNIQUE(playbook_id, step_number)
);
CREATE INDEX ix_response_actions_playbook_id ON response_actions(playbook_id);
CREATE INDEX ix_response_actions_assigned_user_id ON response_actions(assigned_user_id);
COMMIT;
