import json
import os
import re
import time

from ollama import chat

from tools.read_file import read_file
from tools.write_file import write_file
from tools.list_files import list_files
from tools.delete_file import delete_file
from tools.windows_command import windows_command


# =========================================================
# CONFIGURATION
# =========================================================

MODEL = "qwen3:0.6b"

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

RESPONSES_FILE = os.path.join(
    BASE_DIR,
    "responses.json"
)

NUM_CTX = 2048
TEMPERATURE = 0

MAX_OUTPUT_FOR_LLM = 12000


# =========================================================
# LOAD RESPONSES
# =========================================================

def load_responses():

    if not os.path.exists(RESPONSES_FILE):

        return {
            "conversation": {},
            "learned_responses": {},
            "commands": {}
        }

    try:

        with open(
            RESPONSES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        print("[AURA] Loaded responses.json")

        return data

    except Exception as error:

        print(
            f"[AURA] Failed to load responses: {error}"
        )

        return {
            "conversation": {},
            "learned_responses": {},
            "commands": {}
        }


response_data = load_responses()


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):

    text = text.lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# =========================================================
# CONVERSATION INDEX
# =========================================================

def build_conversation_index():

    index = {}

    for section in [
        "conversation",
        "learned_responses"
    ]:

        data = response_data.get(
            section,
            {}
        )

        if not isinstance(data, dict):
            continue

        for item in data.values():

            if not isinstance(
                item,
                dict
            ):
                continue

            patterns = item.get(
                "patterns",
                []
            )

            response = item.get(
                "response"
            )

            if not response:
                continue

            for pattern in patterns:

                index[
                    normalize_text(pattern)
                ] = response

    return index


conversation_index = (
    build_conversation_index()
)


# =========================================================
# PLANNER SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are AURA Planner.

You are a local AI agent created and programmed by
Mohammed Hamza.

Your job is to understand the user's INTENT first,
then decide whether AURA should answer normally or
use a tool.

=========================================================
IMPORTANT
=========================================================

DO NOT decide based only on keywords.

Understand what the user actually wants.

The same command can appear in a question without
the user wanting it executed.

For example:

"How can I use the dir command?"

The user wants an explanation.

DO NOT execute dir.

But:

"Run dir"

means the user wants execution.


=========================================================
INTENTS
=========================================================

You must identify one of these intents:

1. conversation

Normal conversation.

2. explanation

The user wants to know what something is or means.

Examples:

"What is dir?"
"What is ping?"
"What does ipconfig do?"

3. teaching

The user wants to learn how to use something.

Examples:

"How can I use dir?"
"How do I use ping?"
"Teach me ipconfig."

4. execution

The user explicitly wants AURA to execute an operation.

Examples:

"Run dir."
"Execute hostname."
"Show my IP."
"Check my Windows version."
"Ping 8.8.8.8."

5. file_operation

The user wants AURA to read, write, list, or delete files.

=========================================================
VERY IMPORTANT DISTINCTION
=========================================================

These are NOT the same:

"How can I use dir?"

→ teaching

"How do I use dir in Windows 11?"

→ teaching

"What is the dir command?"

→ explanation

"Explain dir with examples."

→ explanation / teaching

"Run dir."

→ execution

"Execute dir."

→ execution

"Show me the files in this folder."

→ execution

"What files are in this folder?"

→ execution

=========================================================
CURRENT WINDOWS INFORMATION
=========================================================

If the user asks for information about the CURRENT
Windows computer, AURA must use windows_command.

Examples:

"What is my IP?"
"What is my computer name?"
"Who am I logged in as?"
"What Windows version am I using?"
"Show my network configuration."
"Show running processes."

These require actual Windows data.

DO NOT answer these from general knowledge.

DO NOT invent values.

=========================================================
AVAILABLE ACTIONS
=========================================================

answer

Use when the user wants conversation, explanation,
teaching, or a question that does not require a tool.

windows_command

Use when the user explicitly wants a Windows command
executed or needs current Windows information.

read_file

Use to read a file.

write_file

Use to create or modify a file.

list_files

Use to list files.

delete_file

Use to delete a file.

=========================================================
PLANNER OUTPUT
=========================================================

Return JSON only.

No markdown.

No explanation outside JSON.


For conversation:

{
    "action": "answer",
    "intent": "conversation",
    "answer": "..."
}


For explanation:

{
    "action": "answer",
    "intent": "explanation",
    "answer": "..."
}


For teaching:

{
    "action": "answer",
    "intent": "teaching",
    "answer": "..."
}


For Windows execution:

{
    "action": "windows_command",
    "intent": "execution",
    "command": "...",
    "goal": "..."
}


For reading:

{
    "action": "read_file",
    "intent": "file_operation",
    "path": "..."
}


For writing:

{
    "action": "write_file",
    "intent": "file_operation",
    "path": "...",
    "content": "..."
}


For listing:

{
    "action": "list_files",
    "intent": "file_operation",
    "path": "."
}


For deleting:

{
    "action": "delete_file",
    "intent": "file_operation",
    "path": "..."
}


=========================================================
WINDOWS EXAMPLES
=========================================================

User:

What is my IP?

Output:

{
    "action": "windows_command",
    "intent": "execution",
    "command": "ipconfig",
    "goal": "find the active local IPv4 address"
}


User:

What is my computer name?

Output:

{
    "action": "windows_command",
    "intent": "execution",
    "command": "hostname",
    "goal": "find the computer hostname"
}


User:

Who am I?

Output:

{
    "action": "windows_command",
    "intent": "execution",
    "command": "whoami",
    "goal": "find the current Windows username"
}


User:

What version of Windows am I using?

Output:

{
    "action": "windows_command",
    "intent": "execution",
    "command": "ver",
    "goal": "find the Windows version"
}


User:

How can I use the dir command?

Output:

{
    "action": "answer",
    "intent": "teaching",
    "answer": "..."
}


User:

What does dir do?

Output:

{
    "action": "answer",
    "intent": "explanation",
    "answer": "..."
}


User:

Run dir.

Output:

{
    "action": "windows_command",
    "intent": "execution",
    "command": "dir",
    "goal": "show the contents of the current directory"
}


=========================================================
CREATOR
=========================================================

AURA was created and programmed by Mohammed Hamza.
"""


# =========================================================
# JSON PARSER
# =========================================================

def parse_json(text):

    if not text:
        return None

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    start = text.find("{")
    end = text.rfind("}")

    if (
        start != -1
        and end != -1
        and end > start
    ):

        text = text[
            start:end + 1
        ]

    try:

        result = json.loads(text)

        if isinstance(
            result,
            dict
        ):

            return result

    except Exception as error:

        print(
            f"[AURA JSON ERROR] {error}"
        )

        print(
            "[AURA RAW]"
        )

        print(text)

    return None


# =========================================================
# PLANNER
# =========================================================

def ask_planner(user_text):

    start = time.perf_counter()

    try:

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            options={
                "temperature": TEMPERATURE,
                "num_ctx": NUM_CTX
            }
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[AURA PLANNER] {elapsed:.2f}s"
        )

        raw = response[
            "message"
        ][
            "content"
        ].strip()

        return parse_json(
            raw
        )

    except Exception as error:

        print(
            f"[AURA PLANNER ERROR] {error}"
        )

        return None


# =========================================================
# COMMAND CONFIRMATION
# =========================================================

def confirm_command(command):

    print()

    print(
        "[AURA SECURITY]"
    )

    print(
        f"Command: {command}"
    )

    answer = input(
        "Execute? [y/N]: "
    ).strip().lower()

    return answer in {
        "y",
        "yes"
    }


# =========================================================
# EXECUTE PLAN
# =========================================================

def execute_plan(plan):

    if not isinstance(
        plan,
        dict
    ):

        return {
            "success": False,
            "error": "Invalid planner result."
        }


    action = plan.get(
        "action"
    )


    # =====================================================
    # ANSWER
    # =====================================================

    if action == "answer":

        return {
            "success": True,
            "type": "answer",
            "answer": plan.get(
                "answer",
                ""
            )
        }


    # =====================================================
    # WINDOWS COMMAND
    # =====================================================

    if action == "windows_command":

        command = plan.get(
            "command"
        )

        if not command:

            return {
                "success": False,
                "error": (
                    "Planner did not provide "
                    "a Windows command."
                )
            }


        print(
            f"[AURA WINDOWS] {command}"
        )


        result = windows_command(
            command
        )


        # -------------------------------------------------
        # Confirmation
        # -------------------------------------------------

        if result.get(
            "requires_confirmation"
        ):

            if not confirm_command(
                command
            ):

                return {
                    "success": False,
                    "cancelled": True,
                    "error": (
                        "User cancelled command execution."
                    )
                }


            result = windows_command(
                command,
                confirmed=True
            )


        return result


    # =====================================================
    # READ FILE
    # =====================================================

    if action == "read_file":

        path = plan.get(
            "path"
        )

        if not path:

            return {
                "success": False,
                "error": "Missing file path."
            }

        try:

            result = read_file(
                path
            )

            return {
                "success": True,
                "tool": "read_file",
                "result": result
            }

        except Exception as error:

            return {
                "success": False,
                "error": str(error)
            }


    # =====================================================
    # WRITE FILE
    # =====================================================

    if action == "write_file":

        path = plan.get(
            "path"
        )

        content = plan.get(
            "content",
            ""
        )

        if not path:

            return {
                "success": False,
                "error": "Missing file path."
            }

        try:

            result = write_file(
                path,
                content
            )

            return {
                "success": True,
                "tool": "write_file",
                "result": result
            }

        except Exception as error:

            return {
                "success": False,
                "error": str(error)
            }


    # =====================================================
    # LIST FILES
    # =====================================================

    if action == "list_files":

        path = plan.get(
            "path",
            "."
        )

        try:

            result = list_files(
                path
            )

            return {
                "success": True,
                "tool": "list_files",
                "result": result
            }

        except Exception as error:

            return {
                "success": False,
                "error": str(error)
            }


    # =====================================================
    # DELETE FILE
    # =====================================================

    if action == "delete_file":

        path = plan.get(
            "path"
        )

        if not path:

            return {
                "success": False,
                "error": "Missing file path."
            }


        print()

        print(
            "[AURA SECURITY]"
        )

        print(
            f"Delete file: {path}"
        )

        answer = input(
            "Delete? [y/N]: "
        ).strip().lower()


        if answer not in {
            "y",
            "yes"
        }:

            return {
                "success": False,
                "cancelled": True,
                "error": (
                    "User cancelled deletion."
                )
            }


        try:

            result = delete_file(
                path
            )

            return {
                "success": True,
                "tool": "delete_file",
                "result": result
            }

        except Exception as error:

            return {
                "success": False,
                "error": str(error)
            }


    # =====================================================
    # UNKNOWN
    # =====================================================

    return {
        "success": False,
        "error": (
            f"Unknown action: {action}"
        )
    }


# =========================================================
# FINAL ANSWER
# =========================================================

def generate_final_answer(
    user_text,
    plan,
    result
):

    action = plan.get(
        "action"
    )

    intent = plan.get(
        "intent",
        ""
    )


    # =====================================================
    # Direct answer
    # =====================================================

    if action == "answer":

        return result.get(
            "answer",
            ""
        )


    # =====================================================
    # Goal
    # =====================================================

    goal = plan.get(
        "goal",
        "answer the user's question"
    )


    # =====================================================
    # Result
    # =====================================================

    result_json = json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    )


    if len(result_json) > MAX_OUTPUT_FOR_LLM:

        result_json = (
            result_json[
                :MAX_OUTPUT_FOR_LLM
            ]
            + "\n[Output truncated]"
        )


    # =====================================================
    # FINAL PROMPT
    # =====================================================

    prompt = f"""
You are AURA's final answer system.

The user asked:

{user_text}

The detected intent is:

{intent}

The information goal is:

{goal}

The executor returned:

{result_json}


Answer the user's original question.


=========================================================
RULES
=========================================================

Use the executor result as the source of truth.

Never invent information.

Never guess.

If the command failed, clearly say that it failed.

If multiple values exist, select the value that matches
the goal.

For network information:

- distinguish connected adapters
- distinguish disconnected adapters
- distinguish Wi-Fi and Ethernet
- prefer an adapter with a Default Gateway when asking
  for the active local IPv4
- distinguish private/local IP from public IP


=========================================================
IMPORTANT
=========================================================

Do not claim that a successful command failed.

Do not say a command is unavailable if the executor
successfully executed it.

Be concise and natural.
"""


    try:

        start = time.perf_counter()

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                }
            ],
            options={
                "temperature": TEMPERATURE,
                "num_ctx": NUM_CTX
            }
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[AURA ANSWER] {elapsed:.2f}s"
        )

        return response[
            "message"
        ][
            "content"
        ].strip()

    except Exception as error:

        print(
            f"[AURA ANSWER ERROR] {error}"
        )

        if result.get(
            "output"
        ):

            return result[
                "output"
            ]

        if result.get(
            "error"
        ):

            return (
                f"I couldn't complete the request: "
                f"{result['error']}"
            )

        return str(
            result
        )


# =========================================================
# MAIN AGENT
# =========================================================

def ask_aura(user_text):

    normalized = normalize_text(
        user_text
    )


    # =====================================================
    # KNOWLEDGE DATABASE
    # =====================================================

    if normalized in conversation_index:

        print(
            "[AURA ROUTER] Knowledge → Direct"
        )

        return conversation_index[
            normalized
        ]


    # =====================================================
    # PLANNER
    # =====================================================

    print(
        "[AURA ROUTER] → Planner"
    )


    plan = ask_planner(
        user_text
    )


    if plan is None:

        return (
            "I couldn't understand the request."
        )


    # =====================================================
    # SHOW PLAN
    # =====================================================

    print(
        "[AURA PLAN]"
    )

    print(
        json.dumps(
            plan,
            indent=2,
            ensure_ascii=False
        )
    )


    # =====================================================
    # EXECUTION
    # =====================================================

    execution_start = (
        time.perf_counter()
    )


    result = execute_plan(
        plan
    )


    execution_time = (
        time.perf_counter()
        - execution_start
    )


    print(
        f"[AURA EXECUTION] "
        f"{execution_time:.3f}s"
    )


    # =====================================================
    # FINAL ANSWER
    # =====================================================

    answer = generate_final_answer(
        user_text,
        plan,
        result
    )


    return answer


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 60
    )

    print(
        "AURA AI AGENT"
    )

    print(
        "Written by: Mohammed Hamza"
    )

    print(
        f"Model: {MODEL}"
    )

    print(
        "Architecture: Intent Planner → Executor → Analyzer → Answer"
    )

    print(
        "Tools: File System + Windows Commands"
    )

    print(
        "Version: 0.6.2"
    )

    print(
        "Natural Language Windows Control: Enabled"
    )

    print(
        "Intent Understanding: Enabled"
    )

    print(
        "Generic Windows Output Analysis: Enabled"
    )

    print(
        "Security Layer: Enabled"
    )

    print(
        "Type 'exit' to quit"
    )

    print(
        "=" * 60
    )


    while True:

        try:

            user_text = input(
                "\nYou > "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\n[AURA] Goodbye!"
            )

            break


        if not user_text:
            continue


        if normalize_text(
            user_text
        ) in {
            "exit",
            "quit"
        }:

            print(
                "[AURA] Goodbye!"
            )

            break


        try:

            answer = ask_aura(
                user_text
            )

            print(
                "\nAURA >"
            )

            print(
                answer
            )

        except Exception as error:

            print(
                f"\n[AURA ERROR] {error}"
            )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()