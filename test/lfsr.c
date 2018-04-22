#include <stdlib.h>
#include <stdio.h>


int main(int argc,char** argv){
  if(argc != 3){
    printf("usage: lfsr seed tap\n");
    return 1;
  }
  unsigned char seed = (unsigned char)atoi(argv[1]);
  unsigned char tap  = (unsigned char)atoi(argv[2]);

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

  unsigned char result = seed << 1 | toggle;
  printf("Next State: 0x%x ie %u\n",result,result);

  return 0;

}
