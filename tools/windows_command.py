import os
import re
import shlex
import subprocess


# =========================================================
# CONFIGURATION
# =========================================================

MAX_OUTPUT = 12000

COMMAND_TIMEOUT = 30


# =========================================================
# SAFE WINDOWS EXECUTABLE COMMANDS
# =========================================================

SAFE_COMMANDS = {

    "ipconfig",
    "hostname",
    "whoami",
    "ver",
    "systeminfo",

    "tasklist",
    "getmac",
    "netstat",

    "arp",
    "route",

    "ping",
    "nslookup",
    "tracert",
    "pathping",

    "driverquery",

    "set",
    "echo",
}


# =========================================================
# WINDOWS BUILT-IN COMMANDS
# =========================================================

# These commands are handled directly by Python instead
# of opening cmd.exe.

BUILTIN_COMMANDS = {

    "dir",
}


# =========================================================
# DANGEROUS COMMANDS
# =========================================================

DANGEROUS_COMMANDS = {

    "del",
    "erase",

    "rd",
    "rmdir",

    "format",

    "shutdown",

    "restart-computer",
    "stop-computer",

    "reg",
    "sc",
    "schtasks",

    "taskkill",

    "net",
    "netsh",

    "diskpart",

    "bcdedit",

    "cipher",

    "takeown",
    "icacls",

    "wevtutil",

    "powercfg",

    "wmic",

    "msiexec",

    "bitsadmin",
}


# =========================================================
# BLOCKED SHELLS
# =========================================================

BLOCKED_COMMANDS = {

    "cmd",
    "cmd.exe",

    "powershell",
    "powershell.exe",

    "pwsh",
    "pwsh.exe",
}


# =========================================================
# GET EXECUTABLE
# =========================================================

def get_executable(command):

    try:

        parts = shlex.split(
            command,
            posix=False
        )

        if not parts:
            return ""

        executable = parts[0]

        executable = os.path.basename(
            executable
        )

        executable = executable.lower()

        executable = executable.strip(
            '"'
        )

        return executable

    except Exception:

        return ""


# =========================================================
# COMMAND CONFIRMATION
# =========================================================

def command_requires_confirmation(
    command
):

    executable = get_executable(
        command
    )


    if not executable:
        return True


    # -----------------------------------------------------
    # Block shells
    # -----------------------------------------------------

    if executable in BLOCKED_COMMANDS:

        return True


    # -----------------------------------------------------
    # Dangerous commands
    # -----------------------------------------------------

    if executable in DANGEROUS_COMMANDS:

        return True


    # -----------------------------------------------------
    # Safe executable
    # -----------------------------------------------------

    if executable in SAFE_COMMANDS:

        return False


    # -----------------------------------------------------
    # Safe built-in
    # -----------------------------------------------------

    if executable in BUILTIN_COMMANDS:

        return False


    # -----------------------------------------------------
    # Unknown
    # -----------------------------------------------------

    return True


# =========================================================
# IPV4 EXTRACTION
# =========================================================

def extract_ipv4_addresses(
    text
):

    return re.findall(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        text
    )


# =========================================================
# MAC EXTRACTION
# =========================================================

def extract_mac_addresses(
    text
):

    return re.findall(
        r"\b[0-9A-Fa-f]{2}"
        r"(?:[-:][0-9A-Fa-f]{2}){5}\b",
        text
    )


# =========================================================
# IPCONFIG ANALYZER
# =========================================================

def parse_ipconfig(
    output
):

    adapters = []

    blocks = re.split(
        r"\n\s*\n",
        output
    )


    for block in blocks:

        adapter_match = re.search(
            r"(?:Ethernet adapter|Wireless LAN adapter)"
            r"\s+(.+?):",
            block,
            re.IGNORECASE
        )


        if not adapter_match:
            continue


        adapter_name = (
            adapter_match
            .group(1)
            .strip()
        )


        ipv4_match = re.search(
            r"IPv4 Address[.\s]*:\s*([\d.]+)",
            block,
            re.IGNORECASE
        )


        gateway_match = re.search(
            r"Default Gateway[.\s]*:\s*([\d.]+)",
            block,
            re.IGNORECASE
        )


        disconnected = (
            "Media disconnected"
            in block
        )


        adapters.append({

            "adapter": adapter_name,

            "ipv4": (
                ipv4_match.group(1)
                if ipv4_match
                else None
            ),

            "gateway": (
                gateway_match.group(1)
                if gateway_match
                else None
            ),

            "connected": (
                not disconnected
            ),
        })


    return adapters


# =========================================================
# DIR IMPLEMENTATION
# =========================================================

def execute_dir(
    command
):

    try:

        parts = shlex.split(
            command,
            posix=False
        )

    except Exception as error:

        return {

            "success": False,

            "error": (
                f"Invalid dir syntax: {error}"
            )
        }


    # -----------------------------------------------------
    # Default directory
    # -----------------------------------------------------

    current_directory = os.getcwd()


    # -----------------------------------------------------
    # Detect simple path argument
    # -----------------------------------------------------

    path = current_directory

    for part in parts[1:]:

        clean_part = part.strip(
            '"'
        )


        # Ignore common DIR switches
        if clean_part.startswith("/"):
            continue


        if clean_part.startswith("-"):
            continue


        path = os.path.abspath(
            clean_part
        )

        break


    # -----------------------------------------------------
    # Validate directory
    # -----------------------------------------------------

    if not os.path.isdir(
        path
    ):

        return {

            "success": False,

            "error": (
                f"Directory not found: {path}"
            )
        }


    # -----------------------------------------------------
    # Read directory
    # -----------------------------------------------------

    try:

        entries = os.listdir(
            path
        )

    except PermissionError:

        return {

            "success": False,

            "error": (
                f"Permission denied: {path}"
            )
        }

    except Exception as error:

        return {

            "success": False,

            "error": str(error)
        }


    # -----------------------------------------------------
    # Build output similar to DIR
    # -----------------------------------------------------

    lines = []

    lines.append(
        f" Directory of {path}"
    )

    lines.append("")


    directories = []

    files = []


    for name in sorted(
        entries,
        key=str.lower
    ):

        full_path = os.path.join(
            path,
            name
        )


        try:

            if os.path.isdir(
                full_path
            ):

                directories.append(
                    name
                )

            else:

                files.append(
                    name
                )

        except Exception:

            files.append(
                name
            )


    for name in directories:

        lines.append(
            f"<DIR>    {name}"
        )


    for name in files:

        lines.append(
            f"          {name}"
        )


    lines.append("")

    lines.append(
        f"{len(files)} File(s)"
    )

    lines.append(
        f"{len(directories)} Dir(s)"
    )


    output = "\n".join(
        lines
    )


    analysis = {

        "executable": "dir",

        "directory": path,

        "directories": directories,

        "files": files,

        "file_count": len(files),

        "directory_count": len(
            directories
        ),
    }


    return {

        "success": True,

        "returncode": 0,

        "command": command,

        "output": output,

        "analysis": analysis,
    }


# =========================================================
# GENERIC ANALYZER
# =========================================================

def analyze_output(
    command,
    output
):

    executable = get_executable(
        command
    )


    analysis = {

        "executable": executable,

        "ipv4_addresses": (
            extract_ipv4_addresses(
                output
            )
        ),

        "mac_addresses": (
            extract_mac_addresses(
                output
            )
        ),

        "network_adapters": [],
    }


    # -----------------------------------------------------
    # IPCONFIG
    # -----------------------------------------------------

    if executable == "ipconfig":

        analysis[
            "network_adapters"
        ] = parse_ipconfig(
            output
        )


    return analysis


# =========================================================
# WINDOWS COMMAND EXECUTOR
# =========================================================

def windows_command(
    command,
    confirmed=False
):

    # =====================================================
    # TYPE VALIDATION
    # =====================================================

    if not isinstance(
        command,
        str
    ):

        return {

            "success": False,

            "error": (
                "Command must be a string."
            )
        }


    command = command.strip()


    if not command:

        return {

            "success": False,

            "error": "Empty command."
        }


    # =====================================================
    # BLOCK SHELL OPERATORS
    # =====================================================

    blocked_tokens = [

        "&&",
        "||",
        "|",

        ">",
        "<",

        "&",
    ]


    for token in blocked_tokens:

        if token in command:

            return {

                "success": False,

                "error": (
                    "Command rejected: "
                    f"operator '{token}' "
                    "is not allowed."
                )
            }


    # =====================================================
    # BLOCK MULTILINE
    # =====================================================

    if (
        "\n" in command
        or "\r" in command
    ):

        return {

            "success": False,

            "error": (
                "Multiline commands "
                "are not allowed."
            )
        }


    # =====================================================
    # EXECUTABLE
    # =====================================================

    executable = get_executable(
        command
    )


    if not executable:

        return {

            "success": False,

            "error": (
                "Could not determine command."
            )
        }


    # =====================================================
    # BLOCK SHELLS
    # =====================================================

    if executable in BLOCKED_COMMANDS:

        return {

            "success": False,

            "error": (
                f"'{executable}' is blocked "
                "by AURA security."
            )
        }


    # =====================================================
    # CONFIRMATION
    # =====================================================

    needs_confirmation = (
        command_requires_confirmation(
            command
        )
    )


    if (
        needs_confirmation
        and not confirmed
    ):

        return {

            "success": False,

            "requires_confirmation": True,

            "command": command,

            "message": (
                "This command requires "
                "user confirmation."
            )
        }


    # =====================================================
    # BUILT-IN COMMANDS
    # =====================================================

    if executable == "dir":

        return execute_dir(
            command
        )


    # =====================================================
    # PARSE EXECUTABLE COMMAND
    # =====================================================

    try:

        args = shlex.split(
            command,
            posix=False
        )

    except ValueError as error:

        return {

            "success": False,

            "error": (
                "Invalid command syntax: "
                f"{error}"
            )
        }


    if not args:

        return {

            "success": False,

            "error": "Empty command."
        }


    # =====================================================
    # EXECUTE
    # =====================================================

    try:

        result = subprocess.run(

            args,

            shell=False,

            capture_output=True,

            text=True,

            timeout=COMMAND_TIMEOUT,

            encoding="utf-8",

            errors="replace",
        )


        stdout = (
            result.stdout.strip()
        )

        stderr = (
            result.stderr.strip()
        )


        if stdout:

            output = stdout

        elif stderr:

            output = stderr

        else:

            output = (
                "Command finished with "
                f"exit code {result.returncode}."
            )


        # =================================================
        # ANALYZE
        # =================================================

        analysis = analyze_output(
            command,
            output
        )


        # =================================================
        # LIMIT OUTPUT
        # =================================================

        if len(output) > MAX_OUTPUT:

            output = (
                output[
                    :MAX_OUTPUT
                ]
                + "\n\n[Output truncated]"
            )


        # =================================================
        # RETURN
        # =================================================

        return {

            "success": (
                result.returncode == 0
            ),

            "returncode": (
                result.returncode
            ),

            "command": command,

            "output": output,

            "analysis": analysis,
        }


    # =====================================================
    # TIMEOUT
    # =====================================================

    except subprocess.TimeoutExpired:

        return {

            "success": False,

            "error": (
                "Command timed out after "
                f"{COMMAND_TIMEOUT} seconds."
            )
        }


    # =====================================================
    # NOT FOUND
    # =====================================================

    except FileNotFoundError:

        return {

            "success": False,

            "error": (
                "Command not found on "
                "this Windows system."
            )
        }


    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as error:

        return {

            "success": False,

            "error": (
                "Command execution error: "
                f"{error}"
            )
        }