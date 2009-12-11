--
-- DB Schema for zbuild
--

BEGIN TRANSACTION;

CREATE TABLE stage (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       name TEXT UNIQUE NOT NULL
);

CREATE TABLE package (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       name TEXT UNIQUE NOT NULL,
       path TEXT UNIQUE NOT NULL,
       parent_id REFERENCES package (id)
);

CREATE TABLE stage_package (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       last_duration INTEGER,
       idx INTEGER NOT NULL,
       stage_id REFERENCES stage (id) NOT NULL,
       package_id REFERENCES package (id) NOT NULL,
       UNIQUE (stage_id, package_id)
);

CREATE TABLE build (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       stage_id REFERENCES stage(id) NOT NULL,
       scheduled_for INTEGER,
       start_time INTEGER,
       end_time INTEGER,
       work_dir TEXT NOT NULL DEFAULT '',
       info TEXT NOT NULL DEFAULT ''
);

CREATE TABLE build_package (
       id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
       start_time INTEGER,
       end_time INTEGER,
       log TEXT NOT NULL DEFAULT '',
       version TEXT NOT NULL DEFAULT '0.0-1',
       revision TEXT NOT NULL DEFAULT 'HEAD',
       branch TEXT NOT NULL DEFAULT 'TRUNK',
       idx INTEGER NOT NULL,
       stage_package_id REFERENCES stage_package (id) NOT NULL,
       build_id REFERENCES build (id) NOT NULL,
       UNIQUE (stage_package_id, build_id)
);

COMMIT TRANSACTION;
