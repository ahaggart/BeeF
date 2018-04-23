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
    printf("usage: lfsr seed tap message\n");
    return 1;
  }
  unsigned char seed =  (unsigned char)atoi(argv[1]);
  unsigned char tap  =  (unsigned char)atoi(argv[2]);

  char c;
  int i = 0;
  while((c=argv[3][i++])!=0){
    seed = advance(seed,tap);
    printf("Seed: 0x%x\tEncrypted: 0x%x\n",seed,seed^(unsigned char)c);
  }
  printf("Done.... Encrypted %d chars\n",i);
  return 0;

}
