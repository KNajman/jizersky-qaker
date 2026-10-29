"""jizerky.db -> data.json pro web (bez lomů, masivů a Loučeňského cimbuří – dle pořadatele)."""
import sqlite3, json
db = sqlite3.connect("jizerky.db"); db.row_factory = sqlite3.Row
rows = [dict(r) for r in db.execute(
    "SELECT * FROM prehled WHERE typ != 'lom' AND objekt NOT LIKE '%masiv%' AND id != 18455 ORDER BY sektor, objekt COLLATE NOCASE")]
json.dump(rows, open("data.json", "w"), ensure_ascii=False)
print(len(rows), "objektů -> data.json")
