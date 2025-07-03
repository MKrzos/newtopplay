import sqlite3

conn = sqlite3.connect("db.db") 
cursor = conn.cursor()

#Create users table

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    country_rank INTEGER,
    global_rank INTEGER NOT NULL,
    pp REAL NOT NULL,
    hit_accuracy REAL NOT NULL,
    play_time INTEGER NOT NULL,
    country_code TEXT,
    avatar_url TEXT,
    playcount INTEGER
);
''')

#Create beatmapset table

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS beatmapset (
#     id INTEGER PRIMARY KEY,
#     title TEXT,
#     artist TEXT,
#     creator TEXT
# );
# ''')

# Create beatmap table
cursor.execute('''
CREATE TABLE IF NOT EXISTS beatmap (
    id INTEGER PRIMARY KEY,
    beatmapset_id INTEGER,
    ar REAL,
    accuracy REAL,
    bpm REAL,
    cs REAL,
    count_circles INTEGER,
    count_sliders INTEGER,
    count_spinners INTEGER,
    difficulty_rating REAL,
    play_count INTEGER,
    total_length INTEGER
);
''')

# # Create join table for many-to-many relationship
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS beatmap_owner (
#     beatmap_id INTEGER,
#     user_id INTEGER,
#     PRIMARY KEY (beatmap_id, user_id),
#     FOREIGN KEY (beatmap_id) REFERENCES beatmap(id) ON DELETE CASCADE,
#     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
# );
# ''')

#map_instance_id is (beatmap_id << 2) | mod_bits where dt = 1, hr = 2 ,dthr = 3
cursor.execute('''
CREATE TABLE IF NOT EXISTS score (
    id INTEGER PRIMARY KEY,
    accuracy REAL,
    beatmap_id INTEGER NOT NULL,
    map_instance_id INTEGER NOT NULL,
    classic_total_score INTEGER,
    legacy_total_score INTEGER,
    total_score INTEGER,
    max_combo INTEGER,
    pp REAL,
    rank TEXT CHECK(rank IN ('A', 'B', 'C', 'D', 'F', 'S', 'SH', 'SS', 'SSH')),
    rank_country INTEGER,
    rank_global INTEGER,
    user_id INTEGER NOT NULL,
    is_perfect_combo BOOLEAN,

    FOREIGN KEY (beatmap_id) REFERENCES beatmap(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
''')

#Create score-mod merge table
cursor.execute('''
CREATE TABLE IF NOT EXISTS score_mod (
    score_id INTEGER NOT NULL,
    mod TEXT NOT NULL,
    PRIMARY KEY (score_id, mod),
    FOREIGN KEY (score_id) REFERENCES score(id) ON DELETE CASCADE
);
'''
)

cursor.execute('''
CREATE TABLE IF NOT EXISTS top_scores (
    id INTEGER PRIMARY KEY,      -- unique score id
    user_id INTEGER NOT NULL,
    beatmap_id INTEGER NOT NULL,
    map_instance_id INTEGER NOT NULL, 
    pp REAL NOT NULL,
    play_rank INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (beatmap_id) REFERENCES beatmap(id) ON DELETE CASCADE
);
''')

cursor.execute('''CREATE INDEX IF NOT EXISTS idx_score_beatmap_id ON score(beatmap_id);''')
cursor.execute('''CREATE INDEX IF NOT EXISTS idx_score_mod_score_id ON score_mod(score_id);''')
cursor.execute('''CREATE INDEX IF NOT EXISTS idx_top_scores_user ON top_scores(user_id);''')
cursor.execute('''CREATE INDEX IF NOT EXISTS idx_top_scores_beatmap ON top_scores(beatmap_id);''')


# Commit changes and close connection
conn.commit()
conn.close()
