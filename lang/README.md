# COW Language Spec
Features:
* namespaces
    * The function block architecture used by BCC allows for function
        "namespaces" of up to 255 functions. Functions occupying a
        namespace may call any other function by name within the namespace.
* modules
    * Import code from other .cow files
        * load other modules and expose their top-level namespace
        * nested namespaces may import the module and access its top-level
            namespace as if it were nested
        * functions and nested namespaces may bind keywords from imported
            modules, which will use the imported definitions when unpacking
    * preamble and postamble
        * Modules which specify a preamble and postamble can be run as
            standalone programs.
        * Preambles prep processor memory by allocating a control cell and
            loading it with the desired "entry-point" function ID
        * Postambles clean up processor memory before the program exits
        * Preamble and Postable routines only run for the root module
* functions and recursion
* debugging
    * automatic cell and stack locking (planned)
        * generates error messages at runtime when code violates important 
            conditions
* keywords:
    * rebase: inform the compiler that the current location of the data head
        should be treated as a given relative address
        * functions rebase to the current data head location on entry
        * compiler will attempt to track relative position
        * assert, rebase, goto, etc require a valid base
    * assert: assert on some condition, error on violation
        * value: assert on the value in some location
            * enables compiler to optimize under this assumption, 
                * example: when zeroing cells to make function calls,
                    compiler can fetch an asserted zero instead of using "[-]"
            * (planned) specify a range or set of values
        * stack (planned): assert on the top value of the stack
            * also enables some compiler optimizations
        * verify (planned): visit all asserted locations to manually check them
            * generates goto statements which allow VM to check locked cells
            * produces no net data head movement, which means that compression
                tools (grinder) will completely strip out move instructions
                produced for assertion verification
        * clear (planned): remove assertions at all listed locations
        * compounding (planned): make multiple value assertions in one statement
        *** compiler needs better assertion management system
        *** need to finish implementing VM locks for these to work
        *** position assertions don't really make sense, just rebase
        *** assertions may be unused if the location they assert on is not
             visited
        *** assertions are cleared when they go out of scope
    * goto: resposition the data head to the given relative location
        * clearer, more concise COW files, less prone to error than manually 
            writing ">" and "<" to reposition the data head
        * accepts relative location or layout names as destination
    * set: set the value of a cell
        * can be compounded: statement may contain multiple address-target
            pairs
        * (maybe) language support for string creation using set statements
    * create: create a value at a specified address
        * by default, will zero then increment cell to value
        * nearby assertions will be considered as "shortcuts" to value
    * layout: assign names to relative locations in the current coordinate base
        * inner text is a whitespace delimited list of position-name pairs
        * reserved names carry special meaning (planned)
            * free: unused memory location, allow compiler to optimize around
        * bindings which contain layout information allow modules to export 
            formatting information for their function calls
    * lock: marks code as having no net effect on data head position
        * wraps code block in data head position assertions to enforce
    * scope: create a scope
        * assertions and keywords bound within the scope are invisible outside
        * avoid namespace collisions or pollution by scoping bindings, etc
    * bind: bind keywords to text in the current scope
        * binding a module name will add all of its bindings to the scope
        * new keywords can be bound inline
    * panic (planned): abort the VM and print a custom message
    * value:
        * bind a name to a numeric value, which can be used as a modifier or a 
            target value in SET statements
        * ex: bind ascii alphabet to single-letter names, for easy "string" use
    * exec (planned): in-order function calling
        * unlike normal calls, exec calls happen immediately
        * implicitly segments function, stacks a call to second segment under
            call to exec'ed function
        * preserves scope across function call, but not inside it

PLANNED:
* counting block optimization
    * current design is prone to spending excessive amounts of time repeatedly
        zeroing the cell at { 0 }
    * (maybe) assume control cell will be a lower value, 
        * zero the CC and copy to { 0 } instead of zeroing { 0 }
* pre-compiled modules
    * compile module into intermediate format and save it
        * parse tree files (pickled)
        * fully compiled files with annotations specifying entry points and 
            FCIDs
* optimize compiler
    * cache semi-resolved bindings
* namespace size management
    * automatically nest functions in overfull namespaces without changing 
        how they can be referenced
    * allow namespaces to logically group contents without worrying about
        exceeding size limit

CONVENTIONS:
* make function calls from zeroed cells
    * indexing to the next functional block will repeatedly zero then restore 
        the cell, so this will save a lot of cycles
* top level functions should make heavy use of assertion verification to prevent
    misuse or misunderstanding by importers
    * tightly controlled code is much easier to debug
    * verification code is easily optimized out

BINDING SEMANTICS:
* Bindings do not create a local scope, so they will pollute the caller's
    namespace. This allows bindings to contain layout and assertion information
    * top-level functions with complex memory footprints should have associated
        bindings which define and verify their expected layout

MODULE CONTENTS:
* preamble:
    * Defines a closure as a module preamble. Preamble closures are run when
    the parent module is run, and are expected to prepare memory then
    call a function in the module namespace.
* postamble:
    * Defines a closure as a module postamble. Modules running as the root
    executable will run their postamble on exit. Postambles are
    expected to clean up memory from execution.
* depends:
    * Defines a closure as a dependency closure. Dependency closures list
    files containing modules to import from
* namespace:
    * Defines a closure as a namespace. Namespaces may contain up to 255
    closures, which must have a namespace-unique name
* bindings:
    * Bindings are direct text substitutions resolved at compile time,
    so they are _invoked_ rather than _called_
    * Bindings may declare typed modifiers, which are passed by the invoker
    and change binding behavior
        * modifier types:
            * `text`: bind invoker-supplied text to a keyword in the invoked 
            binding's scope
                * must be a single token
            * `value`: bind a name to a number supplied by invoker
            * `layout`: bind a name to a relative address supplied by invoker
    * Bindings may contain other bindings
    * Bindings can import another module's bindings, which will be used when
    resolving the binding's text
    * Bindings may not contain function calls (this may change in future releases)
    * modifier system (parenthetical expressions): "apply" some expression to 
        a token by following it with a parenthesized expression
        * by default, a modifier application will duplicate the token, and thus 
        only accepts `value`-type input
        * bindings can define custom modifier behavior by adding a parenthesized
            expression between the name and the curly braces: 
            binding(expr){tokens}
            * any occurence of "expr" in binding text is resolved at compile 
            time, substituting "expr" with the expression supplied in the 
            binding invocation
                * this allows binding subexpressions to be selectively 
                duplicated, as in: [ <(expr) + >(expr) ], to provide a 
                generalized form for expressions which may have different uses 
                for different values of "expr"


# BCC Compiler Notes

## Executable Format

Instruction Layout:
```xml
<program>
    <preamble/> 
    <namespace>
        <header-block/> 
        <functional-blocks>
            <counting-block>
                <code/>
            </counting-block>
            <counting-block>
                <namespace/>
            </counting-block>
        <functional-blocks/>
        <footer-block/>
    </namespace>
    <postamble/>
</program>
```


Preamble:
* The preamble is first code to execute in a _COW_ processor, and is intended as
    a location for setting up memory for the executable before calling a function
    in the module's namespace
    * preambles should ensure that function calls do no destroy important memory
    by shifting or otherwise preserving data in cells that will be used for
    function calls

Header Block:
* Opens the `control loop`, which organizes program function calls.

Counting Block: 
* The counting block is the basic building block for function call structure
* Each block decrements the control cell if it is nonzero
    * The block which decrements the counter to zero is executed
    * Subsequent blocks will see zeroed counter and skip execution
* Namespaces can be nested inside of counting blocks
    * Namespace assembly layout allows nested namespaces to function as if they
    were the root module
    * The next value on top of the stack is used by the nested namespace for
    indexing its own functional blocks
```
Functional Block Prototype:
^                       # push cc to stack for breathing room
[                       # block container (skipped if cc is zeroed)
    _-^                 # decrement cc and push back to stack
    >^[-]+^             # save adjacent cell, then set to one and push to stack
    <                   # return to cc 
    [                   # skip block 1: skipped if cc is (now zero)
        _[-]^           # overwrite stacked one to zero
    ]                 
    _                   # pull stacked value (one if cc was zero, zero ow)
    >_<                 # restore adjacent cell
    [                   # skip block 2: skipped if cc was not zero
        _>
        # INNER CODE HERE
        <[-]^           # zero cc (exit skip block 2)
    ]
                        # (exit container)
]_                      # restore cc
```

Footer Block:
* Closes the `control loop`
* Unpacks function call ID from stack
    * Function call ID of 0 will exit control loop and "pop" to lower
    execution level (a containing control loop, if one exists)
    * Lowest execution level is the preamble/postamble, which will exit the
    program

## Function Call Semantics

Function calls can be made by pushing values to the stack. At the end of each
execution cycle, the top of the stack is used as a function call ID. Call IDs
are resolved and assigned at compile time, and cannot have their value set by
the programmer. Function calls can be "passed" to another function by pushing
them the the stack underneath the receiver function. The receiver must then 
unpack the call stack into memory, and reload the call stack as needed.

Calls to nested namespaces are made by pushing the call ID of function within
the namespace, followed by the call ID of the counting block containing the 
namespace. The namespace ID is unpacked first, and the nested namespace code 
will unpack the next value from the stack.

Function calls also push "exit" and "re-entry" ID stacks, which are constructed
to exit from the called namespace into the base namespace, then index back into
the caller's namespace. This ensures a consistent starting point for all calls
made from a given nesting level.

Functions written in COW must often modify the stack and 
otherwise alter normal program flow in order to achieve the desired result.
One side effect of this is functions which must be called in a specific
order, as they rely on non-standard stack behavior executed in related code.
These non-atomic functions should not be exposed in the base namespace.
Multi-part function executions should be hidden in nested namespaces and 
called upon by functions in the base namespace, which allows modules to 
make use of non-standard behavior without exposing non-standard components to
importing modules.

## Keywords

* rebase: inform the compiler that the current location of the data head
    should be treated as the basis for relative positioning code
    * functions rebase to the current data head location on entry
    * compiler will attempt to track relative position, but will give up
        when it encounters a "[" or a "]"
        * will follow trivial loops if they contain balanced "<" and ">"
* assert: assert on some condition, error on violation
    * value: assert on the value in some location
        * enables compiler to optimize under this assumption, 
            * example: when zeroing cells to make function calls,
                compiler can fetch an asserted zero instead of using "[-]"
        * can specify a range or set of values
        * programmer should be careful not to modify asserted cells from 
        within the scope of the assertion
* goto: resposition the data head to the given relative location
    * clearer, more concise __COW__ files, less prone to error than manually 
        writing ">" and "<" to reposition the data head
    * accepts relative location or layout names as destination
* set: set the value of a cell
    * by default, will zero then increment cell to value
    * nearby assertions will be considered as "shortcuts" to value
* layout: assign names to relative locations in the current coordinate base
    * inner text is a whitespace delimited list of position-name pairs
    * reserved names carry special meaning
        * free: unused memory location, allow compiler to optimize around
    * bindings which contain layout information allow modules to export 
        formatting information for their function calls
* stable/static/atomic: marks a code block as not changing the data head
    position, allowing for additional implicit position tracking
    * wraps code block in data head position assertions to enforce property
    * creates a local positioning scope that is applied only to interior
        * initial state is copied from containing scope
        * rebases will not affect the containing scope on exit
        * layout information will not pollute containing scope
* debug: print compile-time information
* (_PLANNED_) panic: abort the VM and print a custom message

## OPTIMIZATION
* Compiler attempts to optimize the creation of constants based on nearby known
value
* Other optimizations
    * Easy
        * Eliminate pairs of instructions that have no effect
            * `<>` and `><`
            * `^_`
            * `+-` and `-+`
            * This is done by the `GRINDER` optimization tool

## PLANNED FEATURES
* better parsing? needs some research on compiler parse strategy
    * this should be done before adding more features to the hacky compiler
        we have now
* prettier code generation
    * is this even worthwhile? no one wants to look at .beef files anyway
    * need a strategy for grouping things into lines, etc
        * source mapping? VM directives might get in the way if we try to simply
            place assembly on the line corresponding to the line that
            generated it
            * add a directive to ignore directives in line count
* parameter system: module-wide global parameters
    * work in same fashion as bindings, but allow for arbitary text

## Standard Library (WIP)

* common: Contains bindings for useful patterns such as `map` and `reduce`

* bitwise: Contains functions which apply bitwise operations to a pair of 
operands
    * bitwise ops are very expensive in __BeeF__ due to the use of a 
    binary expander, which is an expensive procedure itself, and also
    requires a large workspace which must be preserved and zeroed 

* rails: working with variable-sized data structures if often best achieved 
    using "rails", which are dead memory areas filled with 1's, bounded on both 
    sides by a zero. These regions can be traversed by a simple [>], so code can
    be written to traverse by regions instead of by individual cell.
    * rail creation: rails can be created by hand if their length is known at 
        compile time, or they can be generated by a rail-laying function, which
        carries a counter with it that allows rail length to be a value in
        memory. Rails can also be laid until some memory condition is satisfied,
        such as encountering a nonzero cell. Rails can be a useful data processing
        tool, allowing programs to process input in memory byte-by-byte by 
        laying rails as data is consumed
    * rail traversal: rails are extremely easy to traverse (as long as you only 
        go end-to-end) using [>] or [<], which allows functions to compactly
        reposition to other memory locations without expensive recursive
        travelling functions or hardcoded values.
    * data: data can be used as rails if it is known to be nonzero. Otherwise, a 
        data rail should be used, which makes use of alternating 1's with data.
        Data rails can be traversed with [>>], and can store arbitrary 
        data. 
        * transferring data by rail can be done by stack internally, but should
            be loaded in other ways externally to prevent interference with
            nested call IDs on the stack.
        * exposed functions that transfer data by rail should push data from
            memory, using any scheme suitable for the rail size used
    * functions: recursive functions can make use of rails since they are a
        known value, allowing them to safely and atomically traverse rails. This
        can be used to operate on railed data without needing to account for
        the data clobbering that traveller functions do. One application of this
        is the use of a traveller function to segment existing rails, allowing
        for abstractions such as "memory allocation" by cutting new regions into
        an existing rail line.

* (_WIP_) stack: Bindings and function calls for working with `stack`-like data
structures

* (_PLANNED_) memory manager: using rails, we can implement a memory management
system with rich features such as indexing, and allocation
    * this may be parallel the behavior of the hardware MMU
    * create: create a memory management instance at the current location.
    Requires a moderate amount of free memory, can be passed arguments
    specifying how large the initial memory should be and how it should be
    created
        * unless module import reorganization is implemented, any module using
            the memory manager will have a copy of core mm functions.
            * focus on making mm modular and lightweight, so only the base 
                module needs to import heavier components
            * use request-based system to allow non-base modules to import
                minimal code, base module is responsible for invoking
                memory management routines regularly
    * allocate: segments the memory management rail, creating a free space 
    of the specified size. Updates the manager's memory table to reflect
    the allocation. Returns to the caller's memory index, and writes the
    memory index of the allocated zone to the caller's arg section
        * allocated memory has a number of sections:
            * before and after the allocation are data rails which help direct
            memory traversals over the region, contiaining information such
            as the zone ID and size
            * at the low memory index of the allocated region is the messaging
            space, which is where memory calls should originate and where
            function call arguments should be placed
    * free: removes an entry from the reserved memory table. The manager will
    not wipe or remove memory that is free'd unless it is needed by another
    allocation.
        * optimize for traversal time?
    * goto: use the memory manager to relocate the data head to another zone.
    The caller should load the stack with a reciever function that will
    be passed control after the goto routine completes. The goto routine
    will complete in the messaging section of the given zone, unless
    an error occurred and the request could not be completed
        * cautious memory traversal: 
            * initiated by user-generated memory traversal calls, uses zone 
                annotations to traverse towards manager zone with request data
            * chainer-style function, runs until it reaches the manager zone
                then dumps request data
        * quick memory traversal:
            * initiated by the memory manager, does not use zone annotations
            * manager can preload call stack using information from the memory
                table, allowing it to avoid using chainer functions

