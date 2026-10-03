from tools.terminal import run_command


print("=== TEST 1 ===")
print(run_command("python --version"))


print("\n=== TEST 2 ===")
print(run_command("echo Hello from AURA"))


print("\n=== TEST 3 ===")
print(run_command("dir"))


print("\n=== TEST 4 ===")
print(run_command("dir C:\\Windows"))


print("\n=== TEST 5 ===")
print(run_command("echo AURA > files\\terminal_test.txt"))


print("\n=== TEST 6 ===")
print(run_command("type files\\terminal_test.txt"))
