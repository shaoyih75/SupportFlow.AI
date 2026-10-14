-- Runs only the first time the volume is created.
-- A separate database for integration tests, so pytest never touches dev data.
CREATE DATABASE supportflow_test OWNER supportflow;
