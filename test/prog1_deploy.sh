#!/bin/bash
./lang/bcc.py ./code/cow/prog1.cow ./code/build/prog1.beef 
./util/grinder.py code/build/prog1.beef code/build/prog1.gbf 
./util/assemble.py code/build/prog1.gbf processor/instructions.beef 
./emulator/build/roast code/build/prog1.gbf code/seed/message.seed 
