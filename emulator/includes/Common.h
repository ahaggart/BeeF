#define FMT_INDENT "   "
#define SRC_LEN_T   long
#define SRC_LEN_PRNT_T  "%ld"

#ifdef VM_DEBUG
  #define BVM_DEBUG(...) printf(__VA_ARGS__)
#else
  #define BVM_DEBUG(...)
#endif

#ifdef VM_ASSEMBLY
  #define BVM_ASSEMBLY(...) printf(__VA_ARGS__)
#else
  #define BVM_ASSEMBLY(...)
#endif