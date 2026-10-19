import sys

# Get files
file1 = sys.argv[1]
file2 = sys.argv[2]

# Open chosen message file and get the bits of the file
print("[+] Loading File 1 data...")
with open(file1, "rb") as f:
    contents = bytearray(f.read())
    file1_data_bits = "".join(format(byte, "08b") for byte in contents)
print(f"[+] Loaded {len(file1_data_bits)} bits of data from {file1}")

# Get bits from second one
print("[+] Loading File 2 data...")
with open(file2, "rb") as f:
    contents = bytearray(f.read())
    file2_data_bits = "".join(format(byte, "08b") for byte in contents)
print(f"[+] Loaded {len(file2_data_bits)} bits of data from {file2}")

# Compare
print(f"Length of file1 : {len(file1_data_bits)}")
print(f"Length of file2 : {len(file2_data_bits)}")
errors = 0
for i in range(len(file1_data_bits)):
    if int(file1_data_bits[i]) != int(file2_data_bits[i]):
        errors += 1
print(f"Error rate = {errors} / {len(file1_data_bits)} = {(errors / len(file1_data_bits)) * 100}%")