" Vim syntax file
" Language: COW
" Maintainer: Alexander Haggart
" Latest Revision: 6 May 2018

if exists("b:current_syntax")
  finish
endif

" Keywords
syn keyword closureKeywords scope bind layout set goto rebase create assert value debug

syn keyword lock lock

syn keyword topLevelKeywords postamble namespace bindings
syn keyword dependsKeyword depends contained nextgroup=dependsClosure
syn keyword preambleKeyword preamble contained nextgroup=bindingText

" Regexes
syn match moduleName "[a-zA-Z][a-zA-Z0-9_]*" nextgroup=topLevel
syn match lineComment "#.*$"
syn match rawAssembly "[]^_+<>[-]+" contained 
syn match name "[a-zA-Z][a-zA-Z0-9_]*" contained
syn match number "[+-]?[0-9]+" contained

"syn region modifierChain start="(" end=")" 
syn region address start="{" end="}" contained
syn region lockClosure start="{" end="}" contained transparent
syn region dependsClosure start="{" end="}" contained transparent
syn region topLevel    start="{" end="}" contained transparent contains=topLevelKeywords,dependsKeyword,preambleKeyword
syn region bindingText start="{" end="}" contained transparent contains=name,rawAssembly

let b:current_syntax = "cow"

hi def link closureKeywords   Type
hi def link topLevelKeywords  Type
hi def link lock              Type     
hi def link lineComment       Comment
hi def link rawAssembly       Special
hi def link name              Comment
hi def link moduleName        PreProc        
hi def link dependsKeyword    Type           
hi def link preambleKeyword   Comment        
hi def link number            Constant 
hi def link address           Constant 
