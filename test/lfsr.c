#include <stdlib.h>
#include <stdio.h>

unsigned char advance(unsigned char seed, unsigned char tap){
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

int main(int argc,char** argv){
  if(argc != 4){
    printf("usage: lfsr seed tap steps\n");
    return 1;
  }
  unsigned char seed =  (unsigned char)atoi(argv[1]);
  unsigned char tap  =  (unsigned char)atoi(argv[2]);
  int steps =           (unsigned char)atoi(argv[3]);

  int i;
  for(i = 0; i < steps; i++){
    seed = advance(seed,tap);
    printf("Next State: 0x%x ie %u\n",seed,seed);
  }
  return 0;

}
