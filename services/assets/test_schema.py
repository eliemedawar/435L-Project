"""Verify schema constraints in an isolated database. Developed by: Marc Bteich.

Run: python -m unittest services.assets.test_schema -v
"""
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SchemaTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".local").mkdir(exist_ok=True)
        self.folder = tempfile.TemporaryDirectory(dir=ROOT / ".local")
        self.db = sqlite3.connect(Path(self.folder.name) / "schema-test.db")
        self.db.executescript((ROOT / "database/schema.sql").read_text())
        self.db.execute("INSERT INTO users VALUES (1,'Test Owner','owner','owner@example.test',"
                        "'test-only-placeholder','Security','admin','Active','2026-01-01',NULL)")
        self.db.execute("INSERT INTO assets VALUES (1,'Test Server','Server','192.0.2.1',NULL,"
                        "1,'Security',NULL,'Critical','Active')")

    def tearDown(self):
        self.db.close()
        self.folder.cleanup()

    def test_all_ten_tables_and_integrity(self):
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {'users', 'assets', 'incidents', 'investigation_notes', 'threats',
                                 'logs', 'vulnerabilities', 'notifications', 'playbooks', 'response_actions'})
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_asset_checks_and_owner_fk(self):
        for column, value in (("asset_name", " "), ("asset_type", "Invalid"),
                              ("criticality", "Invalid"), ("status", "Invalid"), ("owner_id", 999)):
            with self.subTest(column=column), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE assets SET {column}=? WHERE id=1", (value,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM users WHERE id=1")

    def test_existing_user_and_incident_constraints(self):
        for sql in ("UPDATE users SET role='bad'", "UPDATE users SET account_status='bad'",
                    "INSERT INTO users SELECT 2,full_name,username,email,password_hash,department,role,account_status,created_at,last_login FROM users"):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
        self.db.execute("INSERT INTO incidents VALUES (1,'Incident','Description','Malware','High',1,1,1,'Open','2026-01-01',NULL)")
        self.db.execute("INSERT INTO investigation_notes VALUES (1,1,1,'Note','2026-01-01')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE incidents SET status='Invalid'")
        self.db.execute("DELETE FROM assets WHERE id=1")
        self.assertIsNone(self.db.execute("SELECT asset_id FROM incidents").fetchone()[0])
        self.db.execute("DELETE FROM incidents WHERE id=1")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigation_notes").fetchone()[0], 0)

    def test_threat_uniqueness_and_enums(self):
        sql = "INSERT INTO threats VALUES (?, 'Domain', 'example.test','Description','High','Lab','2026-01-01')"
        self.db.execute(sql, (1,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, (2,))
        for column in ("threat_type", "severity"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE threats SET {column}='Invalid'")

    def test_vulnerability_score_status_and_asset_fk(self):
        self.db.execute("INSERT INTO vulnerabilities VALUES (1,'Vulnerability','Description','CVE-2026-1234',"
                        "9.8,'Critical',1,'Lab','Open','2026-01-01',NULL)")
        for column, value in (("cvss_score", -0.1), ("cvss_score", 10.1), ("status", "Invalid"),
                              ("severity", "Invalid"), ("asset_id", 999)):
            with self.subTest(column=column, value=value), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE vulnerabilities SET {column}=?", (value,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM assets WHERE id=1")

    def test_playbook_actions_unique_order_and_cascade(self):
        self.db.execute("INSERT INTO playbooks VALUES (1,'Playbook','Description','Malware','High',1,'2026-01-01')")
        self.db.execute("INSERT INTO response_actions (id,playbook_id,description,step_number,status,assigned_user_id) VALUES (1,1,'Step',1,'Pending',1)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO response_actions (id,playbook_id,description,step_number,status,assigned_user_id) VALUES (2,1,'Duplicate',1,'Pending',1)")
        for column, value in (("step_number", 0), ("status", "Invalid"), ("assigned_user_id", 999)):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE response_actions SET {column}=?", (value,))
        self.db.execute("DELETE FROM playbooks WHERE id=1")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM response_actions").fetchone()[0], 0)

    def test_audit_preservation_and_notification_cascade(self):
        self.db.execute("INSERT INTO users VALUES (2,'Second Owner','second','second@example.test',"
                        "'test-only-placeholder','Security','user','Active','2026-01-01',NULL)")
        self.db.execute("INSERT INTO logs VALUES (1,2,'second','LOGIN_SUCCESS','Description','Information','users','2026-01-01')")
        self.db.execute("INSERT INTO notifications VALUES (1,2,'Title','Message','Security Alert','High','Unread','2026-01-01',NULL)")
        for sql in ("UPDATE logs SET severity='bad'", "UPDATE notifications SET status='bad'",
                    "UPDATE notifications SET notification_type='bad'", "UPDATE notifications SET severity='bad'"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
        self.db.execute("DELETE FROM users WHERE id=2")
        self.assertEqual(self.db.execute("SELECT user_id, username FROM logs").fetchone(), (None, 'second'))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM notifications").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
