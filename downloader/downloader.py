import sqlite3
import time
import logging
import signal
import os
from ossapi import Ossapi, Cursor, UserLookupKey, GameMode, RankingType
from utils import save_user, save_beatmap, save_score, save_state, load_state


def handle_exit(signum, frame):
    global should_exit
    print("\nGraceful shutdown requested. Finishing current batch before exiting...")
    should_exit = True
signal.signal(signal.SIGINT, handle_exit)

def fetch_users():
    global api_cursor
    global country_idx
    print(f"Fetching users ranked {user_count} - {user_count + 49}")
    ranking_response = api.ranking(
        GameMode.OSU,                
        RankingType.PERFORMANCE,    
        cursor=api_cursor,
        country=countries[country_idx]
        )
    api_cursor = ranking_response.cursor
    if(api_cursor == Cursor(None)):
        country_idx += 1
    return ranking_response.ranking

def save_statistics(user_statistics):
    global user_count
    for i, user_stat in enumerate(user_statistics):
        user = user_stat.user
        print(f"[{user_count}] Saving user: {user.username}")
        save_user(db_cursor, user_stat)
        user_count += 1
        scores = api.user_scores(user.id, type="best", limit=50)
        relative_score_rank  = 1
        for score in scores:
            save_score(db_cursor, score, user.id, relative_score_rank)
            save_beatmap(db_cursor, score.beatmap)
            relative_score_rank += 1
        db_conn.commit()

db_conn = sqlite3.connect("../db.db")
db_cursor = db_conn.cursor()

with open("clientsecret.txt", "r", encoding="utf-8") as f:
    contents = f.read()
    client_secret, client_id = contents.split(",")
api = Ossapi(client_id, client_secret)

db_cursor.execute('''SELECT COUNT(*) FROM users''')
user_count = db_cursor.fetchone()[0]
end_time = 52
start_time = 0
should_exit = False
countries = ["US", "RU", "PL", "CA", "GB", "DE", "KR", "AU", "BR", "FR", "JP", "PH"]
page_num, country_idx = load_state()
api_cursor = Cursor(page=page_num)
user_statistics = []

while(not should_exit):
    waiting_time = max(0, 52 - (end_time-start_time))
    print(f"waiting {waiting_time}s before proceeding")
    time.sleep(waiting_time) #limit to batch of 51 per 51s
    start_time = time.perf_counter()
    user_statistics = fetch_users()
    save_statistics(user_statistics)
    end_time = time.perf_counter()

save_state(api_cursor.page, country_idx)
print("cleaning up...")
print("✅ Done!")
db_conn.commit()
db_conn.close()