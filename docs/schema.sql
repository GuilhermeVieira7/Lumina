CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(120), 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20), 
	consent_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (email)
)

;
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE profiles (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	avatar VARCHAR(10), 
	birth_date DATE, 
	interests TEXT, 
	sensory_notes TEXT, 
	communication VARCHAR(30), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
CREATE INDEX ix_profiles_id ON profiles (id);

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

CREATE TABLE activity_plans (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	activity_type VARCHAR(30) NOT NULL, 
	level INTEGER, 
	enabled BOOLEAN, 
	recommended BOOLEAN, 
	question_count INTEGER, 
	time_limit INTEGER, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_activity_plans_id ON activity_plans (id);

CREATE TABLE child_requests (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	key VARCHAR(20) NOT NULL, 
	context VARCHAR(60), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_child_requests_id ON child_requests (id);

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

CREATE TABLE mood_checks (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	mood VARCHAR(20) NOT NULL, 
	moment VARCHAR(20), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_mood_checks_id ON mood_checks (id);

CREATE TABLE profile_access (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	professional_id INTEGER NOT NULL, 
	status VARCHAR(20), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	responded_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id), 
	FOREIGN KEY(professional_id) REFERENCES users (id)
)

;
CREATE INDEX ix_profile_access_id ON profile_access (id);

CREATE TABLE recommendation_decisions (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	rec_key VARCHAR(60) NOT NULL, 
	activity_type VARCHAR(30), 
	action VARCHAR(20) NOT NULL, 
	level INTEGER, 
	decided_by INTEGER, 
	last_session_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id), 
	FOREIGN KEY(decided_by) REFERENCES users (id)
)

;
CREATE INDEX ix_recommendation_decisions_id ON recommendation_decisions (id);

CREATE TABLE routine_items (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	position INTEGER, 
	icon VARCHAR(16), 
	label VARCHAR(60) NOT NULL, 
	time VARCHAR(5), 
	duration INTEGER, 
	done_on DATE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_routine_items_id ON routine_items (id);

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
	help_level VARCHAR(20), 
	reward VARCHAR(60), 
	timed_out BOOLEAN, 
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
	voice_enabled BOOLEAN, 
	low_stimulus BOOLEAN, 
	mastery_threshold INTEGER, 
	mastery_sessions INTEGER, 
	token_board BOOLEAN, 
	request_board BOOLEAN, 
	mood_checkin BOOLEAN, 
	rewards_json TEXT, 
	requests_json TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (profile_id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_settings_id ON settings (id);

CREATE TABLE notes (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	session_id INTEGER, 
	activity_type VARCHAR(30), 
	content TEXT NOT NULL, 
	author VARCHAR(100), 
	author_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(profile_id) REFERENCES profiles (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;
CREATE INDEX ix_notes_id ON notes (id);

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

