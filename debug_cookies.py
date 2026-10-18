import os, json, base64, sqlite3, shutil, tempfile, ctypes
from ctypes import wintypes

USER_DATA = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
print('USER_DATA:', USER_DATA)

# 1. Check Local State
ls = os.path.join(USER_DATA, 'Local State')
print('Local State exists:', os.path.isfile(ls))
with open(ls,'r',encoding='utf-8') as f:
    data = json.load(f)
b64 = data['os_crypt']['encrypted_key']
print('encrypted_key b64 len:', len(b64))

# 2. DPAPI decrypt
class DATA_BLOB(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]

raw = base64.b64decode(b64)[5:]  # strip 'DPAPI' prefix
p = ctypes.create_string_buffer(raw, len(raw))
bi = DATA_BLOB(ctypes.sizeof(p), p)
bo = DATA_BLOB()
ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(bi),None,None,None,None,0,ctypes.byref(bo))
print('DPAPI decrypt ok:', bool(ok))
if not ok:
    import ctypes; print('Error:', ctypes.GetLastError()); exit()

aes = ctypes.string_at(bo.pbData, bo.cbData)
print('AES key len:', len(aes))

# 3. Open Default Cookies
cpath = os.path.join(USER_DATA, 'Default', 'Network', 'Cookies')
print('Default Cookies path:', cpath)
print('Exists:', os.path.isfile(cpath))

tmp = tempfile.mktemp(suffix='.db')
try:
    shutil.copy2(cpath, tmp)
    print('Copied to temp:', tmp)
except Exception as e:
    print('Copy error:', e)
    exit()

conn = sqlite3.connect(tmp)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [r[0] for r in cur.fetchall()])

cur.execute('SELECT COUNT(*) FROM cookies')
print('Total cookies in Default:', cur.fetchone()[0])

cur.execute("SELECT DISTINCT host_key FROM cookies WHERE host_key LIKE '%.google%' LIMIT 20")
print('Google hosts:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT host_key, name, length(encrypted_value), encrypted_value FROM cookies WHERE host_key LIKE '%.google%' LIMIT 5")
rows = cur.fetchall()
for r in rows:
    print(f"  host={r[0]}, name={r[1]}, enc_len={r[2]}, prefix={bytes(r[3])[:4]}")

conn.close()
os.remove(tmp)

# 4. Try decryption on one cookie
print('\n--- Decrypt test ---')
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    tmp2 = tempfile.mktemp(suffix='.db')
    shutil.copy2(cpath, tmp2)
    conn2 = sqlite3.connect(tmp2)
    cur2 = conn2.cursor()
    cur2.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%.google%' LIMIT 3")
    for name, ev in cur2.fetchall():
        ev = bytes(ev)
        if ev[:3] in (b'v10', b'v11'):
            nonce = ev[3:15]
            ct = ev[15:]
            try:
                val = AESGCM(aes).decrypt(nonce, ct, None).decode('utf-8','replace')
                print(f"  {name} = {val[:40]}...")
            except Exception as e:
                print(f"  {name} DECRYPT FAIL: {e}")
        else:
            print(f"  {name}: legacy/empty prefix={ev[:4]}")
    conn2.close()
    os.remove(tmp2)
except Exception as e:
    print('Decrypt error:', e)
    import traceback; traceback.print_exc()

print('Done.')
