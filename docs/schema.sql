
CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(120), 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (email)
)

;
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_id ON users (id);

CREATE TABLE profiles (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	avatar VARCHAR(10), 
	birth_date DATE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
CREATE INDEX ix_profiles_id ON profiles (id);

CREATE TABLE sessions (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	activity_type VARCHAR(30) NOT NULL, 
	level INTEGER, 
	total_questions INTEGER, 
	correct INTEGER, 
	incorrect INTEGER, 
	accuracy FLOAT, 
	total_time INTEGER, 
	stars INTEGER, 
	is_practice BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_sessions_id ON sessions (id);

CREATE TABLE settings (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	difficulty INTEGER, 
	auto_adjust BOOLEAN, 
	sound_enabled BOOLEAN, 
	font_size VARCHAR(10), 
	theme VARCHAR(20), 
	language VARCHAR(5), 
	auto_backup BOOLEAN, 
	alerts_enabled BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (profile_id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_settings_id ON settings (id);

CREATE TABLE achievements (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	badge_id VARCHAR(30) NOT NULL, 
	unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_achievements_id ON achievements (id);

CREATE TABLE goals (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	activity_type VARCHAR(30) NOT NULL, 
	target_type VARCHAR(20) NOT NULL, 
	target_value FLOAT NOT NULL, 
	current_value FLOAT, 
	description TEXT, 
	completed BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	completed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_goals_id ON goals (id);

CREATE TABLE responses (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	question_index INTEGER, 
	is_correct BOOLEAN, 
	response_time INTEGER, 
	attempts INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id)
)

;
CREATE INDEX ix_responses_id ON responses (id);

CREATE TABLE notes (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	session_id INTEGER, 
	activity_type VARCHAR(30), 
	content TEXT NOT NULL, 
	author VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id)
)

;
CREATE INDEX ix_notes_id ON notes (id);
