-- Pokemon database (SQLite). This file is also pasted into the AI prompt,
-- so the comments are there to help the model write correct SQL.

CREATE TABLE type (
    type_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE              -- e.g. 'fire', 'water', 'grass'
);

CREATE TABLE pokemon (
    pokemon_id INTEGER PRIMARY KEY,        -- Pokedex number
    name TEXT NOT NULL UNIQUE,             -- lowercase, e.g. 'pikachu'
    generation INTEGER NOT NULL,           -- 1, 2, 3, ...
    height_m REAL,                         -- meters
    weight_kg REAL,                        -- kilograms
    base_experience INTEGER,
    is_legendary INTEGER NOT NULL DEFAULT 0, -- 1 = legendary or mythical, 0 = not
    hp INTEGER NOT NULL,                   -- base stats
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    special_attack INTEGER NOT NULL,
    special_defense INTEGER NOT NULL,
    speed INTEGER NOT NULL
);

-- A pokemon has one or two types (many-to-many)
CREATE TABLE pokemon_type (
    pokemon_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    slot INTEGER NOT NULL,                 -- 1 = primary type, 2 = secondary type
    PRIMARY KEY (pokemon_id, type_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon (pokemon_id),
    FOREIGN KEY (type_id) REFERENCES type (type_id)
);

CREATE TABLE ability (
    ability_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE              -- e.g. 'static', 'overgrow'
);

CREATE TABLE pokemon_ability (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden INTEGER NOT NULL DEFAULT 0,  -- 1 = hidden ability
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon (pokemon_id),
    FOREIGN KEY (ability_id) REFERENCES ability (ability_id)
);

-- Damage multiplier when an attack of one type hits a defender of another type.
-- 0 = no effect, 0.5 = not very effective, 1 = normal, 2 = super effective.
-- For a dual-type defender, multiply the two rows together.
CREATE TABLE type_effectiveness (
    attacking_type_id INTEGER NOT NULL,
    defending_type_id INTEGER NOT NULL,
    multiplier REAL NOT NULL,
    PRIMARY KEY (attacking_type_id, defending_type_id),
    FOREIGN KEY (attacking_type_id) REFERENCES type (type_id),
    FOREIGN KEY (defending_type_id) REFERENCES type (type_id)
);
