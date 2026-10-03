import json
import os
import re
from ollama import chat


# =========================================================
# AURA KNOWLEDGE TRAINER v0.6
# =========================================================

MODEL = "qwen3:0.6b"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRAINING_DATA = os.path.join(
    BASE_DIR,
    "trainer",
    "training_data.json"
)

PENDING_RESPONSES = os.path.join(
    BASE_DIR,
    "trainer",
    "pending_responses.json"
)


# =========================================================
# JSON HELPERS
# =========================================================

def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"[ERROR] Failed to read {path}")
        print(e)
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# CLEAN LLM RESPONSE
# =========================================================

def clean_json_response(text):
    """
    Remove accidental markdown/code fences
    from the LLM response.
    """

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)

    return text.strip()


# =========================================================
# GENERATE
# =========================================================

def generate_questions(category, amount):
    print()
    print("=" * 60)
    print("AURA TRAINER")
    print("=" * 60)

    print(f"Category : {category}")
    print(f"Amount   : {amount}")
    print(f"Model    : {MODEL}")
    print()
    category_fact = CATEGORY_FACTS.get(
    category,
    "No special fact is defined for this category.",
)
    category_examples = CATEGORY_EXAMPLES.get(
    category,
    []
)


    prompt = f"""
You are the training-data generator for AURA,
a local AI assistant created and programmed by Mohammed Hamza.

Generate {amount} simple conversational question/answer pairs.

Category:
{category}

FACT:

{category_fact}

The answer MUST NOT contradict this fact.

EXAMPLES OF VALID QUESTIONS:

{json.dumps(category_examples, ensure_ascii=False, indent=2)}

Generate questions that are natural variations of the examples above.

Do NOT change the main intent or topic of the examples.

CATEGORY-SPECIFIC RULES:

If the category is "creator":

The question MUST specifically ask about the PERSON
who created, programmed, made, built, or developed AURA.

Valid examples:

- Who created AURA?
- Who programmed you?
- Who is your creator?
- Who is your programmer?
- Who made you?
- Who built AURA?
- Who developed you?
- Who is behind AURA?
- Who created you?
- Who is the person behind AURA?

Invalid examples:

- What does AURA do?
- What is AURA's purpose?
- What are AURA's capabilities?
- What tools does AURA use?
- How does AURA work?
- How was AURA built?
- How was AURA developed?
- How is AURA maintained?
- How many users does AURA have?

For the "creator" category,
DO NOT generate questions about:
purpose, capabilities, tools, functions,
development process, implementation,
maintenance, users, or technical details.

The category field in every generated object MUST be exactly:
"{category}"

Do not change the category name.
Do not translate it.
Do not use another category name.

IMPORTANT RULES:

1. Only ordinary human conversation.
2. Do NOT generate programming questions.
3. Do NOT generate cybersecurity questions.
4. Do NOT generate technical questions.
5. Do NOT generate questions requiring complex reasoning.
6. Do NOT generate file-operation commands.
7. Do NOT generate questions about tools.
8. Questions must be useful for normal conversation.
9. Answers must be short, natural and friendly.
10. Keep AURA's identity consistent.
11. The answer must respect the FACT above.
12. Generate different natural ways of asking similar things.
13. Do not duplicate questions.
14. Every item MUST contain exactly these fields:
    question
    answer
    category
15. Do not invent facts about AURA.
16. If the question is about AURA's creator,
    the answer must identify Mohammed Hamza.
17. Stay strictly within the selected category.

Return ONLY valid JSON.

Example:

[
  {{
    "question": "Who created you?",
    "answer": "I was created and programmed by Mohammed Hamza.",
    "category": "{category}"
  }}
]
"""
    
    try:
        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.4,
                "num_ctx": 2048
            }
        )

        content = response["message"]["content"]

        content = clean_json_response(content)

        data = json.loads(content)

        if not isinstance(data, list):
            print("[ERROR] LLM did not return a list.")
            return []

        return data

    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON returned by LLM.")
        return []

    except Exception as e:
        print("[ERROR]", e)
        return []


# =========================================================
# VALIDATOR
# =========================================================

ALLOWED_CATEGORIES = {
    "greeting",
    "identity",
    "creator",
    "casual_conversation",
    "thanks",
    "goodbye",
    "small_talk",
    "simple_questions"
}
CATEGORY_FACTS = {

    "creator": (
        "AURA was created and programmed by Mohammed Hamza."
    ),

    "identity": (
        "AURA is a local AI assistant created by Mohammed Hamza."
    )

}
CATEGORY_EXAMPLES = {

    "creator": [
        "Who created AURA?",
        "Who programmed you?",
        "Who is your creator?",
        "Who is your programmer?",
        "Who made you?",
        "Who built AURA?",
        "Who developed you?",
        "Who is behind AURA?",
        "Who created you?",
        "Who was responsible for creating AURA?"
    ],

    "identity": [
        "Who are you?",
        "What is your name?",
        "What are you?",
        "Who is AURA?",
        "Can you tell me who you are?",
        "How should I call you?"
    ],

    "greeting": [
        "Hello",
        "Hi",
        "Hey",
        "Good morning",
        "Good evening",
        "Hello AURA",
        "Hi AURA"
    ],

    "thanks": [
        "Thanks",
        "Thank you",
        "Thanks AURA",
        "I appreciate your help",
        "Thank you for helping me"
    ],

    "goodbye": [
        "Bye",
        "Goodbye",
        "See you later",
        "See you",
        "Talk to you later"
    ],

    "small_talk": [
        "How was your day?",
        "What are you doing?",
        "Are you busy?",
        "How are you today?",
        "Are you having a good day?"
    ],

    "casual_conversation": [
        "What do you like?",
        "What do you enjoy?",
        "Tell me something interesting",
        "Can we chat?",
        "Do you like talking to people?"
    ],

    "simple_questions": [
        "What is your favorite color?",
        "What is your favorite food?",
        "Do you like music?",
        "Can you tell me something fun?",
        "What do you like to talk about?"
    ]

}

CATEGORY_KEYWORDS = {

    "greeting": [
        "hello",
        "hi",
        "hey",
        "morning",
        "evening",
        "سلام",
        "هلا",
        "هلو"
    ],

    "identity": [
        "who are you",
        "what are you",
        "your name",
        "what is your name",
        "who is aura",
        "what is aura"
    ],

    "creator": [
        "who created",
        "who programmed",
        "who is your creator",
        "who is your programmer",
        "who made you",
        "who built you",
        "who developed you",
        "who is behind aura",
        "who is behind you",
        "who created you",
        "who made aura",
        "who built aura",
        "who developed aura"
    ],

    "thanks": [
        "thanks",
        "thank you",
        "thx",
        "appreciate"
    ],

    "goodbye": [
        "bye",
        "goodbye",
        "see you",
        "later"
    ],

    "casual_conversation": [
        "what do you like",
        "what do you enjoy",
        "tell me something",
        "what do you think"
    ],

    "small_talk": [
        "how was your day",
        "how is your day",
        "what are you doing",
        "are you busy",
        "are you free"
    ]
}
CATEGORY_BLOCKED_PATTERNS = {

    "creator": [
        "how was",
        "how is",
        "how does",
        "what is",
        "what does",
        "what are",
        "why is",
        "why does"
    ]

}
BLOCKED_WORDS = {

    # Programming
    "python",
    "javascript",
    "java",
    "code",
    "coding",
    "programming",
    "function",
    "class",
    "api",
    "algorithm",

    # Cybersecurity
    "hack",
    "hacking",
    "exploit",
    "xss",
    "sql injection",
    "malware",
    "ransomware",
    "keylogger",
    "backdoor",
    "metasploit",
    "nmap",
    "burp",
    "payload",
    "vulnerability",

    # Technical
    "linux",
    "windows",
    "tcp",
    "udp",
    "http",
    "https",
    "database",
    "server",
    "network",
    "terminal",
    "command",

}


def is_simple_question(item):

    if not isinstance(item, dict):
        print("[REJECT] Item is not a dictionary")
        print(item)
        return False

    question = item.get("question")
    answer = item.get("answer")
    category = item.get("category")

    if not question:
        print("[REJECT] Missing question")
        print(item)
        return False

    if not answer:
        print("[REJECT] Missing answer")
        print(item)
        return False

    if not category:
        print("[REJECT] Missing category")
        print(item)
        return False

    # Normalize category
    category = str(category).strip().lower()

    if category not in ALLOWED_CATEGORIES:
        print(
            f"[REJECT] Invalid category: {category}"
        )
        print(item)
        return False

    question_lower = str(question).lower()

    for word in BLOCKED_WORDS:
        if word in question_lower:
            print(
                f"[REJECT] Blocked word: {word}"
            )
            print(item)
            return False

    if len(str(question)) > 200:
        print("[REJECT] Question too long")
        print(item)
        return False

    if len(str(answer)) > 500:
        print("[REJECT] Answer too long")
        print(item)
        return False

    return True


def matches_category(item):

    question = str(
        item["question"]
    ).lower().strip()

    category = str(
        item["category"]
    ).lower().strip()

    # simple_questions does not require
    # specific keywords
    if category == "simple_questions":
        return True

    # Check blocked patterns
    blocked_patterns = CATEGORY_BLOCKED_PATTERNS.get(
        category,
        []
    )

    for pattern in blocked_patterns:

        if question.startswith(pattern):
            return False

    # Check category keywords
    keywords = CATEGORY_KEYWORDS.get(
        category,
        []
    )

    if not keywords:
        return True

    for keyword in keywords:

        if keyword in question:
            return True

    return False


# =========================================================
# DUPLICATE CHECK
# =========================================================

def normalize_question(question):
    return " ".join(
        question.lower().strip().split()
    )


def remove_duplicates(items):

    unique = []
    seen = set()

    for item in items:

        question = normalize_question(
            item["question"]
        )

        if question in seen:
            continue

        seen.add(question)
        unique.append(item)

    return unique


# =========================================================
# SAVE PENDING
# =========================================================

def save_pending(items):

    existing = load_json(
        PENDING_RESPONSES,
        []
    )

    if not isinstance(existing, list):
        existing = []

    combined = existing + items

    combined = remove_duplicates(combined)

    save_json(
        PENDING_RESPONSES,
        combined
    )

    return len(combined)


# =========================================================
# TRAIN
# =========================================================

def train():

    print()
    print("AURA KNOWLEDGE TRAINER v0.6")
    print()

    training_data = load_json(
        TRAINING_DATA,
        {}
    )

    categories = training_data.get(
        "categories",
        {}
    )

    if not categories:

        print("[ERROR]")
        print("training_data.json contains no categories.")

        return

    print("Available categories:")

    category_names = list(categories.keys())

    for i, category in enumerate(
        category_names,
        start=1
    ):
        print(
            f"{i}. {category}"
        )

    print()

    choice = input(
        "Select category: "
    ).strip()

    try:
        index = int(choice) - 1
        category = category_names[index]

    except:
        print("[ERROR] Invalid category.")
        return

    amount_input = input(
        "How many Q&A pairs? "
    ).strip()

    try:
        amount = int(amount_input)

        if amount <= 0:
            raise ValueError

    except:
        print("[ERROR] Invalid amount.")
        return

    generated = generate_questions(
        category,
        amount
    )

    print()
    print(
        f"Generated: {len(generated)}"
    )

    valid = []

    for item in generated:

        if not is_simple_question(item):
            continue

        if not matches_category(item):
            print(
                f"[REJECT] Wrong category: "
                f"{item['question']}"
            )
            continue

        valid.append(item)

    print(
        f"Valid:     {len(valid)}"
    )

    rejected = len(generated) - len(valid)

    print(
        f"Rejected:  {rejected}"
    )

    valid = remove_duplicates(valid)

    print(
        f"Unique:    {len(valid)}"
    )

    if not valid:
        print()
        print("Nothing to save.")
        return

    total = save_pending(valid)

    print()
    print("=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    print(
        f"Added to pending: {len(valid)}"
    )

    print(
        f"Total pending:    {total}"
    )

    print()
    print(
        "Saved:"
    )

    print(
        PENDING_RESPONSES
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    train()