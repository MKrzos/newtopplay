def save_state(page_number, country_number):
    try:
        with open("state.txt", "w") as f:
            f.write(f"{page_number}\n{country_number}\n")
    except Exception as e:
        print(e)
        print(page_number)
        print(country_number)

def load_state():
    try:
        with open("state.txt", "r") as f:
            page_number = f.readline()
            country_number = f.readline()
            return int(page_number), int(country_number)
    except Exception as e:
        print("no previous state found, starting from beginning")
        return 0, 0

def save_user(cursor, user_statistics):
    user = user_statistics.user
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

def save_beatmap(cursor, beatmap):
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


def save_score(cursor, score, user_id, relative_score_rank):
    map_instance_id = score.beatmap_id << 2 
    for mod in score.mods:
        if((mod.acronym) == "NC" or mod.acronym == "DT"):
            map_instance_id = map_instance_id | 1
        if((mod.acronym) == "HR"):
            map_instance_id | 2

    cursor.execute('''
        INSERT OR REPLACE INTO top_scores (id, user_id, beatmap_id, map_instance_id, pp, play_rank)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (score.id, user_id, score.beatmap_id, map_instance_id, score.pp, relative_score_rank))
    
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