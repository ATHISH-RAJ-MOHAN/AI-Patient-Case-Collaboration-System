USE healthcare_group_chat;
-- 1) users Table - Stores all users (doctors, nurses, coordinators - person managing the case room) who can access the system
create table users(
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'doctor',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2) Patient cases table - Represents each patient case room where care team members collaborate
create table patient_cases (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_code VARCHAR(100) NOT NULL UNIQUE,
    case_title VARCHAR(255) not null,
    status VARCHAR(20) not null default 'open',
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_patient_cases_created_by
        FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 3) Case members table - Maps users to patient cases (who is part of which case room)
CREATE TABLE case_members (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    member_role VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_case_user (case_id, user_id),
    CONSTRAINT fk_case_members_case
        FOREIGN KEY (case_id) REFERENCES patient_cases(id),
    CONSTRAINT fk_case_members_user
        FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 4) Messages Table - Stores all chat messages within each patient case room
CREATE TABLE messages(
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_id BIGINT NOT NULL,
    sender_id BIGINT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    content TEXT NOT NULL,
    reply_to_id BIGINT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_messages_case
        FOREIGN KEY (case_id) REFERENCES patient_cases(id),
    CONSTRAINT fk_message_sender
        FOREIGN KEY (sender_id) REFERENCES users(id)
);

-- 5) Documents table - Stores metadata for uploaded files (PDFs/images) linked to patient cases
CREATE TABLE documents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_id BIGINT NOT NULL,
    uploaded_by BIGINT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_documents_case
        FOREIGN KEY (case_id) REFERENCES patient_cases(id),
    CONSTRAINT fk_documents_user
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
);