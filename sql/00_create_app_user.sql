-- Run ONCE as a MySQL administrator (root) before starting the application:
--   mysql -u root -p < sql/00_create_app_user.sql
-- Creates the limited account the Python application logs in with.
CREATE USER IF NOT EXISTS 'parking_app'@'localhost' IDENTIFIED BY 'parking123';
CREATE USER IF NOT EXISTS 'parking_app'@'127.0.0.1' IDENTIFIED BY 'parking123';
GRANT ALL PRIVILEGES ON smart_parking.* TO 'parking_app'@'localhost';
GRANT ALL PRIVILEGES ON smart_parking.* TO 'parking_app'@'127.0.0.1';
FLUSH PRIVILEGES;
