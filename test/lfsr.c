#include "lfsr.h"

BYTE advance(BYTE seed, BYTE tap){
  int i;
  int toggle = 0;
  for(i = 0; i < 8; i++){
    if(((tap >> i & seed >> i) & 0x01)){
      if(toggle){
        toggle = 0;
      }else{
        toggle = 1;
      }
    }
  }
  return seed << 1 | toggle;
}
