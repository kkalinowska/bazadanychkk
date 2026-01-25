-- Usuwamy stare tabele, aby uniknąć konfliktów (kolejność ma znaczenie!)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Tworzymy tabelę użytkowników
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tworzymy tabelę zadań (z automatycznym śledzeniem czasu)
CREATE TABLE tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    status ENUM('todo', 'doing', 'done') DEFAULT 'todo',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Relacja: jeśli usuniesz użytkownika, jego zadania zostaną usunięte automatycznie
    CONSTRAINT fk_tasks_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Dodajemy szybkie indeksy (przyspieszają filtrowanie)
CREATE INDEX idx_task_status ON tasks(status);
CREATE INDEX idx_task_user ON tasks(user_id);

-- 4. Wstawiamy dane testowe, żebyś od razu widział, że działa
INSERT INTO users (username, email, password_hash) VALUES 
('admin', 'admin@example.com', '$2y$10$89AbC...'), 
('user1', 'user1@example.com', '$2y$10$90XyZ...');

INSERT INTO tasks (user_id, title, description, status, priority) VALUES 
(1, 'Konfiguracja bazy', 'Baza została poprawnie ulepszona', 'done', 'high'),
(1, 'Test wydajności', 'Sprawdzenie czy indeksy działają', 'todo', 'medium'),
(2, 'Pierwsze logowanie', 'Sprawdzić czy user1 może wejść', 'doing', 'low');
