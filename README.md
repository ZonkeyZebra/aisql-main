# Pokemon AI SQL Database

## Description
I created a small database for the first two generations of Pokemon with some AI SQL querying.
The small database was generated using the PokeAPI and I am using OpenAI for the AI.

## Picture of Schema
![pokemon database](/drawSQL-pokemon-database.jpg)

## Sample question, SQL query, response that worked
**Sample question:** Which pokemon have the ability of 'intimidate'?

SQL Syntax Response:
```
SELECT p.name
FROM pokemon p
JOIN pokemon_ability pa ON p.pokemon_id = pa.pokemon_id
JOIN ability a ON pa.ability_id = a.ability_id
WHERE a.name = 'intimidate';
```

Query Raw Response:
```
[('arbok',), ('arcanine',), ('ekans',), ('granbull',), ('growlithe',), ('gyarados',), ('hitmontop',), ('qwilfish',), ('snubbull',), ('stantler',), ('tauros',)]
```

Friendly Response:
```
The Pokémon with the ability "intimidate" are: Arbok, Arcanine, Ekans, Granbull, Growlithe, Gyarados, Hitmontop, Qwilfish, Snubbull, Stantler, and Tauros.
```

I thought it handled this request pretty well. It correctly managed to find all the pokemon in the database that had this particular ability.

## Sample question, SQL query, response that did not work (if you have one)
**Sample question:** Which pokemon have a lot of hp and would be good for a tank in battle?

SQL Syntax Response:
```
SELECT p.name
FROM pokemon p
WHERE p.hp >= 150;
```

Query Raw Response:
```
[('chansey',), ('snorlax',), ('wobbuffet',), ('blissey',)]
```

Friendly Response:
```
The Pokémon that have a lot of HP and would be good for a tank in battle are Chansey, Snorlax, Wobbuffet, and Blissey.
```

I was quite curious to see how it would handle a more vague and subjective request. I think it did an all right job, but I do find it interesting to see what value it decided would mean "a lot", which in this case was apparently 150. I can't say I would argue with the number it selected, but it was interesting to see.

## Six Other Examples
Some other examples and their results can be seen on the following files:
 - [zero shot](/response_zero_shot_1791595500.7312236.json)
 - [single domain double shot](/response_single_domain_double_shot_1791595526.7724779.json)
 - [multi domain double shot](/response_multi_domain_double_shot_1791595549.3733957.json)

## Prompting Strategies Tried And Their Differences
I tried three different strategies: zero shot, single domain double shot, and multi domain double shot.