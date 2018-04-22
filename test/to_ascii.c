#include <stdio.h>
#include <stdlib.h>

int main(int argc,char**argv){
    if(argc != 2){
        printf("usage: ascii_to_convert");
        return 1;
    }

    printf("ascii: ");
    char c;
    int i = 0;
    while((c=argv[1][i++])!=0){
        printf("%d,",c);
    }
    printf("\n");
}