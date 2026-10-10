# Pokemon AI SQL Database

## Description
I created a small database for the first two generations of Pokemon with some AI SQL querying.
The small database was generated using the PokeAPI and I am using OpenAI for the AI.

## Picture of Schema
![pokemon database](/drawSQL-pokemon-database.jpg)

## Sample question, SQL query, response that worked
**Sample question:** Which pokemon have the ability of 'intimidate'?

SQL Syntax Response:
```sql
SELECT p.name
FROM pokemon p
JOIN pokemon_ability pa ON p.pokemon_id = pa.pokemon_id
JOIN ability a ON pa.ability_id = a.ability_id
WHERE a.name = 'intimidate';
```

Query Raw Response:
> [('arbok',), ('arcanine',), ('ekans',), ('granbull',), ('growlithe',), ('gyarados',), ('hitmontop',), ('qwilfish',), ('snubbull',), ('stantler',), ('tauros',)]

Friendly Response:
> The Pokémon with the ability "intimidate" are: Arbok, Arcanine, Ekans, Granbull, Growlithe, Gyarados, Hitmontop, Qwilfish, Snubbull, Stantler, and Tauros.

I thought it handled this request pretty well. It correctly managed to find all the pokemon in the database that had this particular ability.

## Sample question, SQL query, response that did not work (if you have one)
**Sample question:** Which pokemon are weak to water attacks?

SQL Syntax Response:
```sql
SELECT p.name
FROM pokemon p
JOIN pokemon_type pt ON p.pokemon_id = pt.pokemon_id
JOIN type t ON pt.type_id = t.type_id
JOIN type_effectiveness te ON t.type_id = te.defending_type_id
WHERE te.attacking_type_id = (SELECT type_id FROM type WHERE name = 'water') 
AND te.multiplier < 1;
```

Query Raw Response:
> [('bulbasaur',), ('ivysaur',), ('venusaur',), ('squirtle',), ('wartortle',), ('blastoise',), ('oddish',), ('gloom',), ('vileplume',), ('paras',), ('parasect',), ('psyduck',), ('golduck',), ('poliwag',), ('poliwhirl',), ('poliwrath',), ('bellsprout',), ('weepinbell',), ('victreebel',), ('tentacool',), ('tentacruel',), ('slowpoke',), ('slowbro',), ('seel',), ('dewgong',), ('shellder',), ('cloyster',), ('krabby',), ('kingler',), ('exeggcute',), ('exeggutor',), ('tangela',), ('horsea',), ('seadra',), ('goldeen',), ('seaking',), ('staryu',), ('starmie',), ('magikarp',), ('gyarados',), ('lapras',), ('vaporeon',), ('omanyte',), ('omastar',), ('kabuto',), ('kabutops',), ('dratini',), ('dragonair',), ('dragonite',), ('chikorita',), ('bayleef',), ('meganium',), ('totodile',), ('croconaw',), ('feraligatr',), ('chinchou',), ('lanturn',), ('bellossom',), ('marill',), ('azumarill',), ('politoed',), ('hoppip',), ('skiploom',), ('jumpluff',), ('sunkern',), ('sunflora',), ('wooper',), ('quagsire',), ('slowking',), ('qwilfish',), ('corsola',), ('remoraid',), ('octillery',), ('mantine',), ('kingdra',), ('kingdra',), ('suicune',), ('celebi',)]

Friendly Response:
> The Pokémon that are weak to water attacks include: Bulbasaur, Ivysaur, Venusaur, Squirtle, Wartortle, Blastoise, Oddish, Gloom, Vileplume, Paras, Parasect, Psyduck, Golduck, Poliwag, Poliwhirl, Poliwrath, Bellsprout, Weepinbell,Victreebel, Tentacool, Tentacruel, Slowpoke, Slowbro, Seel, Dewgong, Shellder, Cloyster, Krabby, Kingler, Exeggcute, Exeggutor, Tangela, Horsea, Seadra, Goldeen, Seaking, Staryu, Starmie, Magikarp, Gyarados, Lapras, Vaporeon, Omanyte, Omastar, Kabuto, Kabutops, Dratini, Dragonair, Dragonite, Chikorita, Bayleef, Meganium, Totodile, Croconaw, Feraligatr, Chinchou, Lanturn, Bellossom, Marill, Azumarill, Politoed, Hoppip, Skiploom, Jumpluff, Sunkern, Sunflora, Wooper, Quagsire, Slowking, Qwilfish, Corsola, Remoraid, Octillery, Mantine, Kingdra, and Suicune.

This was the result for the single domain double shot, and it is just incorrect. It seems to have responded with water types and grass types, both of which would not be weak to water. This is a bit odd because the AI can formulate the correct answer with a different strategy. With this strategy, however, it was not able to correctly answer the question.

## Six Other Examples
Some other examples and their results can be seen on the following files:
 - [zero shot](/response_zero_shot_1791595500.7312236.json)
 - [single domain double shot](/response_single_domain_double_shot_1791595526.7724779.json)
 - [multi domain double shot](/response_multi_domain_double_shot_1791595549.3733957.json)

## Prompting Strategies Tried And Their Differences
I tried three different strategies: zero shot, single domain double shot, and multi domain double shot.
For almost all the questions, it seemed that the multi domain double shot gave the best and most accurate answers to the questions. I didn't notice a lot of difference between the single double shot and the zero shot, but the multi double shot outperformed both by quite a bit.