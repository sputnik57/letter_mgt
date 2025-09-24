PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE letters (
                letter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                prisoner_idx INTEGER NOT NULL,
                prisoner_code TEXT NOT NULL,
                
                -- Step work (manually acquired from letter content)
                step_work TEXT,
                
                -- Image paths
                envelope_image_path TEXT,  -- manually redacted, encrypted later, local drive
                letter_pages_image_path TEXT,  -- PDF, manually redacted, encrypted later, posted online
                
                -- Standardized date tracking (21Sep2025 format)
                date_picked_up_po TEXT,  -- manually entered
                date_env_letter_scanned TEXT,  -- auto-filled when scanned
                date_letter_postmarked TEXT,  -- OCR or manual entry/confirmation
                date_began_response TEXT,  -- manual entry/confirmation
                date_finished_response TEXT,  -- manual entry
                
                -- OCR and processing data
                ocr_text TEXT,
                ocr_confidence REAL,
                return_address TEXT,
                processing_status TEXT DEFAULT 'scanned',
                processor_notes TEXT,
                raw_ocr_json_path TEXT,
                
                -- System timestamps (for audit purposes)
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
INSERT INTO letters VALUES(1,2,'Mbssz!BmboQspggjuu!U73284',replace('Step 6\n','\n',char(10)),'uploaded_file',NULL,NULL,'21Sep2025',NULL,NULL,NULL,replace('LA Proffitt T-62173\nE 25-B204-1L\n480 Alta Rd.\nSan Diego, CA 92179\nAsep 2025\nAttn: CA Privener Outreach\n9141382648 8039\n$001.32\nSCISAA\nPO Box 57648\nSherman Oaks, CA 91413','\n',char(10)),NULL,'','scanned',NULL,NULL,'2025-09-21 20:51:03','2025-09-21 14:06:00');
INSERT INTO letters VALUES(2,2,'Mbssz!BmboQspggjuu!U73284',NULL,'uploaded_file',NULL,NULL,'21Sep2025',NULL,NULL,NULL,replace('LA Proffitt T-62173\nE 25-B204-1L\n480 Alta Rd.\nSan Diego, CA 92179\nAsep 2025\nAttn: CA Privener Outreach\n9141382648 8039\n$001.32\nSCISAA\nPO Box 57648\nSherman Oaks, CA 91413','\n',char(10)),NULL,'','scanned',NULL,NULL,'2025-09-21 20:58:53','2025-09-21 20:58:53');
INSERT INTO letters VALUES(3,2,'Mbssz!BmboQspggjuu!U73284',NULL,'uploaded_file',NULL,NULL,'21Sep2025',NULL,NULL,NULL,replace('LA Proffitt T-62173\nE 25-B204-1L\n480 Alta Rd.\nSan Diego, CA 92179\nAsep 2025\nAttn: CA Privener Outreach\n9141382648 8039\n$001.32\nSCISAA\nPO Box 57648\nSherman Oaks, CA 91413','\n',char(10)),NULL,'','scanned',NULL,NULL,'2025-09-21 21:01:34','2025-09-21 21:01:34');
CREATE TABLE audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                letter_id INTEGER,
                field_changed TEXT,
                old_value TEXT,
                new_value TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
INSERT INTO audit_log VALUES(1,'2025-09-21 13:51:03','letter_added',1,'envelope_scanned','','Letter envelope scanned on 21Sep2025','Updated envelope_scanned','2025-09-21 20:51:03');
INSERT INTO audit_log VALUES(2,'2025-09-21 13:58:53','letter_added',2,'envelope_scanned','','Letter envelope scanned on 21Sep2025','Updated envelope_scanned','2025-09-21 20:58:53');
INSERT INTO audit_log VALUES(3,'2025-09-21 14:01:34','letter_added',3,'envelope_scanned','','Letter envelope scanned on 21Sep2025','Updated envelope_scanned','2025-09-21 21:01:34');
INSERT INTO audit_log VALUES(4,'2025-09-21 14:05:50','field_updated',1,'step_work','None',replace('6\n','\n',char(10)),'Updated step_work','2025-09-21 21:05:50');
INSERT INTO audit_log VALUES(5,'2025-09-21 14:06:00','field_updated',1,'step_work',replace('6\n','\n',char(10)),replace('Step 6\n','\n',char(10)),'Updated step_work','2025-09-21 21:06:00');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('letters',3);
INSERT INTO sqlite_sequence VALUES('audit_log',5);
COMMIT;
