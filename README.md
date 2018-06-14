# BeeF Processor Design Notes
***
## ISA: width: 3 bits (8 instructions)
*see: https://en.wikipedia.org/wiki/Brainfuck*

`^`: __PSH__ - push current cell to stack 

`_`: __POP__ - pop item from stack, overwriting current cell

`+`: __INC__ - increment data

`-`: __DEC__ - decrement data

`>`: __MVR__ - move data head right

`<`: __MVL__ - move data head left

`[`: __CBF__ - if data is 0, skip to matching "]"

`]`: __CBB__ - if data is not 0, skip to matchin "["
***

## Toolchain:

This repository contains a number of tools for BeeF development, including:
* `BCC`: A higher-level language, called __COW__, which compiles into BeeF.
See the `lang` directory for more information about __COW__
* `BVM`: A virtual machine for running __BeeF__, with support for additional features
via VM Directives
    * __COW__ makes uses the directive system to provide stronger language 
    features
    * _TODO_: memory-mapped syscalls to make __BeeF__ and __BVM__ do useful things
* `GRINDER`: A basic compression and optimization tool which attempts to reduce the size of
assembly files by optimizing or removing common instruction patterns.
    * __COW__ generates very verbose assembly to support it VM Directive usage,
    which helps developers track down bugs more easily. Once __COW__ programs
    have been thoroughly tested, run `grinder.py` on them strip out extra
    instructions
* `MISC`: A simple processor designed to run BeeF as an ISA
    * An assembler for converting ASCII-type BeeF programs into ASCII-binary files,
    which can be run by the processor

## Assembly:

* BeeF is a minimal ISA, so the assembler must do extra work to provide some basic functionality

***
## Writing Code
### Basic Building Blocks
* ADD: current cell and next cell
```[->+<]```

* SUB: current cell and next cell
```[->-<]```

* ZER: zero the current cell
```[-]```

### Complex Assembler Construct
* INV: invert the current cell
``` >^[-]<[->-<]>-^<_>_< ```

* SHR: right-shift cell value by doubling it
```>^[-]<[->++<]>^<_>_<```

* NOT: logical not of the current cell ```>^[-]^<[ [-]->_+^- ] + >__```
    * use the right adjacent cell as scratch space loop condition



