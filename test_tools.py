from tools.write_file import write_file
from tools.read_file import read_file
from tools.list_files import list_files
from tools.delete_file import delete_file


print("=== WRITE ===")
print(write_file("files/test.txt", "Hello from AURA!"))


print("\n=== LIST ===")
print(list_files("files"))


print("\n=== READ ===")
print(read_file("files/test.txt"))


print("\n=== DELETE ===")
print(delete_file("files/test.txt"))


print("\n=== LIST AFTER DELETE ===")
print(list_files("files"))