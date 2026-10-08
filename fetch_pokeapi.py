"""
Run this ONCE to generate setupData.sql from PokeAPI.
Responses are cached in ./cache so re-running does not hit the API again.

    pip install requests
    python fetch_pokeapi.py
"""
import json
import os
import time

import requests

BASE = "https://pokeapi.co/api/v2"
LIMIT = 251  # Pokedex numbers 1..LIMIT (251 = generations 1 and 2)

fdir = os.path.dirname(os.path.abspath(__file__))
cacheDir = os.path.join(fdir, "cache")
os.makedirs(cacheDir, exist_ok=True)


def get(path):
    """GET from PokeAPI with a simple on-disk cache and polite delay."""
    cachePath = os.path.join(cacheDir, path.replace("/", "_").replace("?", "_") + ".json")
    if os.path.exists(cachePath):
        with open(cachePath) as f:
            return json.load(f)
    response = requests.get(f"{BASE}/{path}", timeout=30)
    response.raise_for_status()
    data = response.json()
    with open(cachePath, "w") as f:
        json.dump(data, f)
    time.sleep(0.1)
    return data


def idFromUrl(url):
    return int(url.rstrip("/").split("/")[-1])


def q(value):
    """Format a Python value as a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def insert(table, columns, row):
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(q(v) for v in row)});"


statements = []

# --- types (the 18 standard ones) ---
typeList = get("type?limit=18")["results"]
typeIds = {}  # name -> id
for t in typeList:
    typeData = get(f"type/{t['name']}")
    typeIds[typeData["name"]] = typeData["id"]
    statements.append(insert("type", ["type_id", "name"], [typeData["id"], typeData["name"]]))

# --- type effectiveness (default 1.0, then override from damage_relations) ---
multipliers = {(a, d): 1.0 for a in typeIds.values() for d in typeIds.values()}
for name, typeId in typeIds.items():
    relations = get(f"type/{name}")["damage_relations"]
    for key, value in (("double_damage_to", 2.0), ("half_damage_to", 0.5), ("no_damage_to", 0.0)):
        for target in relations[key]:
            if target["name"] in typeIds:
                multipliers[(typeId, typeIds[target["name"]])] = value
for (attacker, defender), value in sorted(multipliers.items()):
    statements.append(insert("type_effectiveness",
                             ["attacking_type_id", "defending_type_id", "multiplier"],
                             [attacker, defender, value]))

# --- pokemon, their types, and abilities ---
seenAbilities = {}
for pokemonId in range(1, LIMIT + 1):
    p = get(f"pokemon/{pokemonId}")
    species = get(f"pokemon-species/{pokemonId}")
    stats = {s["stat"]["name"]: s["base_stat"] for s in p["stats"]}

    statements.append(insert(
        "pokemon",
        ["pokemon_id", "name", "generation", "height_m", "weight_kg", "base_experience",
         "is_legendary", "hp", "attack", "defense", "special_attack", "special_defense", "speed"],
        [p["id"], p["name"], idFromUrl(species["generation"]["url"]),
         p["height"] / 10, p["weight"] / 10, p["base_experience"],
         species["is_legendary"] or species["is_mythical"],
         stats["hp"], stats["attack"], stats["defense"],
         stats["special-attack"], stats["special-defense"], stats["speed"]]))

    for t in p["types"]:
        statements.append(insert("pokemon_type", ["pokemon_id", "type_id", "slot"],
                                 [p["id"], typeIds[t["type"]["name"]], t["slot"]]))

    for a in p["abilities"]:
        abilityId = idFromUrl(a["ability"]["url"])
        if abilityId not in seenAbilities:
            seenAbilities[abilityId] = a["ability"]["name"]
            statements.append(insert("ability", ["ability_id", "name"], [abilityId, a["ability"]["name"]]))
        statements.append(insert("pokemon_ability", ["pokemon_id", "ability_id", "is_hidden"],
                                 [p["id"], abilityId, a["is_hidden"]]))
    print(f"fetched {p['id']}: {p['name']}")

# Parent tables are inserted before child tables (foreign keys), except abilities which
# are inserted inline above before the rows that use them, so order is already valid.
with open(os.path.join(fdir, "setupData.sql"), "w") as out:
    out.write("\n".join(statements) + "\n")
print(f"Wrote {len(statements)} statements to setupData.sql")
