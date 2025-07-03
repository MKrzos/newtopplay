import sqlite3
import time
import logging
import signal
import os
from ossapi import Ossapi, Cursor, UserLookupKey, GameMode, RankingType

should_exit = False

def handle_exit(signum, frame):
    global should_exit
    print("\nGraceful shutdown requested. Finishing current batch before exiting...")
    should_exit = True

# Catch Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, handle_exit)

def load_cursor():
    if os.path.exists("cursor_state.txt"):
        with open("cursor_state.txt", "r", encoding="utf-8") as f:
            return Cursor(page=f.read().strip()[-2]) #lol
    return None

# Save cursor to file
def save_cursor(cursor_value):
    with open("cursor_state.txt", "w", encoding="utf-8") as f:
        f.write(cursor_value or "")

def save_user_count(user_count):
    with open("user_count_state.txt", "w", encoding="utf-8") as f:
        f.write(user_count)

def load_user_count():
    if os.path.exists("user_count_state.txt"):
        with open("user_count_state.txt", "r", encoding="utf-8") as f:
            return int(f.read().strip())
    return 0

# logging.getLogger("ossapi.ossapiv2").setLevel(logging.INFO)  # or WARNING

# # Enable HTTP requests logging
# logging.getLogger("httpx").setLevel(logging.DEBUG)  # if ossapi uses httpx
# logging.getLogger("requests").setLevel(logging.DEBUG)  # if ossapi uses requests
# logging.getLogger("urllib3").setLevel(logging.WARNING)  # avoid connection noise

def save_user(user_statistics):
    user = user_statistics.user
    # print(user.id, user.username, user_statistics.country_rank,
    #     user_statistics.global_rank or -1, user_statistics.pp,
    #     user_statistics.hit_accuracy, user_statistics.play_time,
    #     user.country_code, user_statistics.play_count)
    cursor.execute('''
        INSERT OR IGNORE INTO users (
            id, username, country_rank, global_rank, pp, hit_accuracy, play_time, country_code, playcount
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user.id, user.username, user_statistics.country_rank,
        user_statistics.global_rank or -1, user_statistics.pp,
        user_statistics.hit_accuracy, user_statistics.play_time,
        user.country_code, user_statistics.play_count
    ))

# API call per map, way too slow

#def save_beatmapset(beatmapset):
 #   cursor.execute('''
  #      INSERT OR IGNORE INTO beatmapset (
   #         id, title, artist, creator
    #    ) VALUES (?, ?, ?, ?)
    #''', (
     #   beatmapset.id, beatmapset.title, beatmapset.artist, beatmapset.creator
   # ))


def save_beatmap(beatmap):
    #beatmapset = beatmap.beatmapset()
    #save_beatmapset(beatmapset)  # Must save beatmapset first

    cursor.execute('''
        INSERT OR IGNORE INTO beatmap (
            id, beatmapset_id, ar, accuracy, bpm, cs, count_circles, count_sliders,
            count_spinners, difficulty_rating, play_count, total_length
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        beatmap.id, beatmap.beatmapset_id, beatmap.ar, beatmap.accuracy, beatmap.bpm, beatmap.cs,
        beatmap.count_circles, beatmap.count_sliders, beatmap.count_spinners,
        beatmap.difficulty_rating, beatmap.playcount, beatmap.total_length
    ))


def save_score(score, user_id, relative_score_rank):
    beatmap = score.beatmap
    save_beatmap(beatmap)

    # Insert score
    # print(score.id, score.accuracy, score.beatmap_id, score.classic_total_score,
    #   score.legacy_total_score, score.total_score, score.max_combo, score.pp,
    #   score.rank, score.rank_country, score.rank_global,
    #   user_id, score.is_perfect_combo)
    # print(f"SCORE RANK: {score.rank.value}")

    map_instance_id = score.beatmap_id << 2 
    for mod in score.mods:
        if((mod.acronym) == "NC" or mod.acronym == "DT"):
            map_instance_id = map_instance_id | 1
        if((mod.acronym) == "HR"):
            map_instance_id | 2
    save_top_play(score.id, user_id, score.beatmap_id, map_instance_id, score.pp, relative_score_rank)
    
    cursor.execute('''
        INSERT OR IGNORE INTO score (
            id, accuracy, beatmap_id, map_instance_id, classic_total_score, legacy_total_score,
            total_score, max_combo, pp, rank, rank_country, rank_global,
            user_id, is_perfect_combo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        score.id, score.accuracy, score.beatmap_id, map_instance_id, score.classic_total_score, score.legacy_total_score,
        score.total_score, score.max_combo, score.pp, score.rank.value,
        score.rank_country, score.rank_global, user_id, score.is_perfect_combo
    ))

    # Mods as individual rows
    for mod in score.mods:
        cursor.execute('''
            INSERT OR IGNORE INTO score_mod (score_id, mod) VALUES (?, ?)
        ''', (score.id, mod.acronym))

def save_top_play(id, user_id, beatmap_id, map_instance_id, pp, play_rank):
    cursor.execute('''
        INSERT OR REPLACE INTO top_scores (id, user_id, beatmap_id, map_instance_id, pp, play_rank)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id, user_id, beatmap_id, map_instance_id, pp, play_rank))


conn = sqlite3.connect("db.db")
cursor = conn.cursor()
with open("clientsecret.txt", "r", encoding="utf-8") as f:
    contents = f.read()
    client_secret, client_id = contents.split(",")
api = Ossapi(client_id, client_secret)


user_count = load_user_count()
api_cursor = load_cursor()
user_statistics = []

time2 = 52
time1= 0
while(not should_exit):
    waiting_time = max(0, 52 - (time2-time1))
    print(f"waiting {waiting_time}s before proceeding")
    time.sleep(max(0, 52 - (time2-time1))) #limit to batch of 51 per 51s
    time1 = time.perf_counter()
    print(f"Fetching users ranked {user_count + 1} - {user_count + 50}")
    ranking_response = api.ranking(
        GameMode.OSU,                # Mode standard
        RankingType.PERFORMANCE,     # Ranking by pp 
        cursor=api_cursor
    )
    api_cursor = ranking_response.cursor
    user_statistics = ranking_response.ranking

    for i, user_stat in enumerate(user_statistics):
        user = user_stat.user
        print(f"[{user_count}] Saving user: {user.username}")
        save_user(user_stat)
        user_count += 1

        # Step 2: Get user's top 50 scores
        #print(f"Fetching top 50 plays for {user.username}...")
        scores = api.user_scores(user.id, type="best", limit=50)
        relative_score_rank  = 1
        for score in scores:
            save_score(score, user.id, relative_score_rank)
            relative_score_rank += 1
        conn.commit()  # Save after each user
    time2 = time.perf_counter()

print("cleaning up...")

save_cursor(str(api_cursor))
save_user_count(str(user_count))

print("✅ Done!")
conn.commit()
conn.close()