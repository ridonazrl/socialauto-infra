from pathlib import Path

env_path = Path(__file__).parent / ".env"

print(f"Path: {env_path}")
print(f"Ada? {env_path.exists()}")
print(f"Ukuran file: {env_path.stat().st_size} bytes")
print("-" * 40)

# Baca raw bytes untuk lihat karakter tersembunyi
with open(env_path, "rb") as f:
    raw_bytes = f.read()

print("Isi RAW (bytes):")
print(raw_bytes)
print("-" * 40)

# Baca sebagai text
with open(env_path, "r", encoding="utf-8") as f:
    content = f.read()

print("Isi TEXT:")
print(repr(content))  # repr() akan menampilkan \n, \r, spasi, dll
print("-" * 40)

# Cek per baris
lines = content.splitlines()
print(f"Jumlah baris: {len(lines)}")
for i, line in enumerate(lines):
    print(f"  Baris {i+1}: {repr(line)}")