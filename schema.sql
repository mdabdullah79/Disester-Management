
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'citizen','volunteer')) NOT NULL
);

CREATE TABLE IF NOT EXISTS disasters (
    disaster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    location TEXT NOT NULL,
    date_time TEXT NOT NULL,
    description TEXT,
    reported_by INTEGER,
    FOREIGN KEY(reported_by) REFERENCES users(user_id)
);



CREATE TABLE IF NOT EXISTS help_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    disaster_id INTEGER NOT NULL,
    help_type TEXT NOT NULL,
    location TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(disaster_id) REFERENCES disasters(disaster_id)
);
CREATE TABLE IF NOT EXISTS volunteer_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disaster_id INTEGER NOT NULL,
    volunteer_id INTEGER NOT NULL,
    assigned_on TEXT NOT NULL,
    FOREIGN KEY(disaster_id) REFERENCES disasters(disaster_id),
    FOREIGN KEY(volunteer_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS volunteers (
    volunteer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skills TEXT,
    location TEXT,
    availability INTEGER DEFAULT 1,
    assigned_to INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(assigned_to) REFERENCES disasters(disaster_id)
);

CREATE TABLE IF NOT EXISTS resources (
    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    location TEXT NOT NULL
);

