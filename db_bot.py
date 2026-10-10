import json
import os
import sqlite3
import time
from typing import Any

from openai import OpenAI, RateLimitError

print("Running db_bot.py!")

fdir = os.path.dirname(os.path.abspath(__file__))


def getPath(fname):
    return os.path.join(fdir, fname)


# ----------------------------------------------------------------------------
# SQLITE
# ----------------------------------------------------------------------------
sqliteDbPath = getPath("aidb.sqlite")
setupSqlPath = getPath("setup.sql")
setupSqlDataPath = getPath("setupData.sql")

# Erase previous db
if os.path.exists(sqliteDbPath):
    os.remove(sqliteDbPath)

sqliteCon = sqlite3.connect(sqliteDbPath)
sqliteCursor = sqliteCon.cursor()

with open(setupSqlPath) as setupSqlFile, open(setupSqlDataPath) as setupSqlDataFile:
    setupSqlScript = setupSqlFile.read()
    setupSqlDataScript = setupSqlDataFile.read()

sqliteCursor.executescript(setupSqlScript)  # tables and keys
sqliteCursor.executescript(setupSqlDataScript)  # data
sqliteCon.commit()

# After setup, refuse any write from AI-generated SQL
sqliteCursor.execute("PRAGMA query_only = ON")


def runSql(query):
    # Belt and braces: only allow a single read-only statement
    cleaned = query.strip().rstrip(";").strip()
    if ";" in cleaned or not cleaned.lower().startswith(("select", "with")):
        raise ValueError("Only a single SELECT statement is allowed.")
    return sqliteCursor.execute(cleaned).fetchall()


# ----------------------------------------------------------------------------
# LLM (Google Gemini through its OpenAI-compatible endpoint)
# ----------------------------------------------------------------------------
configPath = getPath("config.json")
with open(configPath) as configFile:
    config = json.load(configFile)

# config.json example:
# {
#   "apiKey": "YOUR_GEMINI_KEY",
#   "baseUrl": "https://generativelanguage.googleapis.com/v1beta/openai/",
#   "model": "gemini-2.5-flash",
#   "delaySeconds": 5
# }
client = OpenAI(api_key=config["apiKey"], base_url=config["baseUrl"])
chosen_model = config["model"]
delaySeconds = config.get(
    "delaySeconds", 5
)  # spacing between calls to stay under free-tier limits


def getLlmResponse(content, retries=4):
    """One prompt in, one string out. Backs off and retries on rate limits."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=chosen_model,
                messages=[{"role": "user", "content": content}],
            )
            time.sleep(delaySeconds)
            return response.choices[0].message.content or ""
        except RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Still rate limited after several retries")


# ----------------------------------------------------------------------------
# STRATEGIES
# ----------------------------------------------------------------------------
commonSqlOnlyRequest = (
    " Give me a sqlite select statement that answers the question. "
    "Only respond with sqlite syntax. If there is an error do not explain it!"
)

# Example from the SAME domain (Pokemon)
singleDomainExample = (
    " Which pokemon have two types? "
    "\nSELECT p.name\nFROM pokemon p\nJOIN pokemon_type pt ON p.pokemon_id = pt.pokemon_id\n"
    "GROUP BY p.pokemon_id\nHAVING COUNT(*) = 2;\n "
)

# Example from a DIFFERENT domain (schema + question + SQL), as in the multi-domain
# strategy from the paper. Replace with whatever other schema you like.
otherDomainExample = (
    " CREATE TABLE person (person_id INTEGER PRIMARY KEY, name TEXT);"
    " CREATE TABLE phone (phone_id INTEGER PRIMARY KEY, person_id INTEGER, can_receive_sms INTEGER);"
    " Who doesn't have a way for us to text them? "
    "\nSELECT p.person_id, p.name\nFROM person p\n"
    "LEFT JOIN phone ph ON p.person_id = ph.person_id AND ph.can_receive_sms = 1\n"
    "WHERE ph.phone_id IS NULL;\n "
)

strategies = {
    "zero_shot": setupSqlScript + commonSqlOnlyRequest,
    "single_domain_double_shot": setupSqlScript
    + singleDomainExample
    + commonSqlOnlyRequest,
    "multi_domain_double_shot": otherDomainExample
    + setupSqlScript
    + singleDomainExample
    + commonSqlOnlyRequest,
}

questions = [
    "Which pokemon has the highest attack?",
    "What are the top 3 fastest pokemon?",
    "Which pokemon have more than one type?",
    "Which fire type pokemon have the highest special attack?",
    "How many pokemon are there of each type as their primary type?",
    "Which pokemon are weak to water attacks?",
    "Which of the previous pokemon are also legendary?",  # follow-up: needs earlier context
    "Which pokemon have a lot of hp and would be good for a tank in battle?",
    "Which pokemon have the ability of 'intimidate'?",
    "Who is the strongest pokemon?",
]

USE_HISTORY = True  # include earlier question/SQL pairs so follow-ups like "the previous pokemon" can work


# use the markdown for the sql syntax to find the SQL query
def sanitizeForJustSql(value):
    marker = "```"
    if marker in value:
        value = value.split(marker, 1)[1]
        newline_index = value.find("\n")  # skip the language tag (sql, sqlite, ...)
        if newline_index != -1:
            value = value[newline_index + 1 :]
    if marker in value:
        value = value.split(marker, 1)[0]
    return value.strip()


def buildSqlPrompt(strategy, question, history):
    prompt = strategies[strategy]
    if USE_HISTORY and history:
        prompt += " Earlier in this conversation: " + " ".join(
            f'Q: "{h["question"]}" SQL: {h["sql"]}' for h in history[-2:]
        )
    return prompt + " " + question


history: list[dict[str, str]] = []


def buildFriendlyPrompt(question, sql, rawResult):
    # Gives the model the schema, the SQL that ran, and the result, not just the question and rows.
    return (
        "You are answering questions about a Pokemon database with this schema:\n"
        + setupSqlScript
        + f'\nThe user asked: "{question}"\n'
        f"This SQL query was run to answer it:\n{sql}\n"
        f"The query returned these rows (as Python tuples): {rawResult}\n"
        "Using only these rows, give a concise, friendly answer in plain English. "
        "If no rows came back, say nothing matched. Do not give suggestions or extra chatter."
    )


# ----------------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------------
for strategy in strategies:
    responses: dict[str, Any] = {
        "strategy": strategy,
        "prompt_prefix": strategies[strategy],
    }
    questionResults = []
    history = []
    print("########################################################################")
    print(f"Running strategy: {strategy}")

    for question in questions:
        print(
            "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        )
        print("Question:")
        print(question)

        # initialise so a failure part-way through doesn't crash the results record
        sqlSyntaxResponse = None
        queryRawResponse = None
        friendlyResponse = None
        error = "None"

        try:
            sqlSyntaxResponse = sanitizeForJustSql(
                getLlmResponse(buildSqlPrompt(strategy, question, history))
            )
            print("SQL Syntax Response:")
            print(sqlSyntaxResponse)

            queryRawResponse = str(runSql(sqlSyntaxResponse))
            print("Query Raw Response:")
            print(queryRawResponse)

            friendlyResponse = getLlmResponse(
                buildFriendlyPrompt(question, sqlSyntaxResponse, queryRawResponse)
            )
            print("Friendly Response:")
            print(friendlyResponse)

            history.append({"question": question, "sql": sqlSyntaxResponse})
        except Exception as err:
            error = str(err)
            print("Error:", err)

        questionResults.append(
            {
                "question": question,
                "sql": sqlSyntaxResponse,
                "queryRawResponse": queryRawResponse,
                "friendlyResponse": friendlyResponse,
                "error": error,
            }
        )

    responses["questionResults"] = questionResults
    with open(getPath(f"response_{strategy}_{time.time()}.json"), "w") as outFile:
        json.dump(responses, outFile, indent=2)

sqliteCursor.close()
sqliteCon.close()
print("Done!")
