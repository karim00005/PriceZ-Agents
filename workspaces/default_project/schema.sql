-- Database Schema for Attendance System
CREATE TABLE IF NOT EXISTS employees (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_punches (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) REFERENCES employees(id),
    punch_time TIMESTAMP NOT NULL,
    punch_type VARCHAR(30) DEFAULT 'Fingerprint',
    device_ip VARCHAR(45)
);

CREATE INDEX idx_punch_time ON attendance_punches(punch_time);
