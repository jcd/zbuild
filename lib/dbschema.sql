--
-- DB Schema for zbuild
--

BEGIN TRANSACTION;

--
-- A buildset specifies the set of script to 
-- run when building this buildset
--
CREATE TABLE buildset (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       name TEXT UNIQUE NOT NULL,
       flags INT NOT NULL DEFAULT 0
);

--
-- Metadata for a script that can be executed
--
CREATE TABLE script (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       name TEXT NOT NULL,
       repos TEXT,
       path TEXT UNIQUE NOT NULL,
       is_parent INTEGER DEFAULT 0,
       parent_id REFERENCES script (id)
);

--
-- Coupling between buildset and scripts belonging
-- to the buildset
--
CREATE TABLE buildset_script (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       last_duration INTEGER,
       idx INTEGER NOT NULL,
       buildset_id REFERENCES buildset (id) NOT NULL,
       script_id REFERENCES script (id) NOT NULL,
       UNIQUE (buildset_id, script_id)
);

--
-- A build of a given buildset
--
CREATE TABLE build (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       buildset_id REFERENCES buildset(id) NOT NULL,
       scheduled_for INTEGER,
       start_time INTEGER,
       end_time INTEGER,
       work_dir TEXT NOT NULL DEFAULT '',
       info TEXT NOT NULL DEFAULT ''
);

--
-- The status of a script run as part of a build
--
CREATE TABLE build_script_status (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       start_time INTEGER,
       end_time INTEGER,
       log TEXT NOT NULL DEFAULT '',
       version TEXT NOT NULL DEFAULT '0.0-1',
       revision TEXT NOT NULL DEFAULT 'HEAD',
       branch TEXT NOT NULL DEFAULT 'TRUNK',
       idx INTEGER NOT NULL,
       exit_code INTEGER,
       buildset_script_id REFERENCES buildset_script (id) NOT NULL,
       build_id REFERENCES build (id) NOT NULL,
       UNIQUE (buildset_script_id, build_id)
);

COMMIT TRANSACTION;
