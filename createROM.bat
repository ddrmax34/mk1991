
@echo  OFF

set asm-vars=--options ENG_VER 1 JAP_VER 0

set linker-input="linked rel files.txt"
set linker-options="rel options.txt"
set linker-output="../LINKED_OUTPUT.rom"

set asset-instructions="ROM files.txt"
set ROM-OUTPUT="../final output.sfc"






ECHO Assembling .asm files into .rel files!

break>SYMBOLS.txt



rem Assemble all files



rem PUT FILES TO ASSEMBLE HERE:
rem format as "assembler.exe <file_directory> %asm-vars%"

assembler.exe ../1991_alpha/CODE/sfx-exp.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/init-exp.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/set-bg.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/set-obj.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/calc-exp.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/data-exp.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/ctrl-exp.asm %asm-vars%
assembler.exe ../1991_alpha/CODE/check-exp.asm %asm-vars%







ECHO Assembled .asm files!

ECHO.

ECHO Linking .rel files into a single ROM





linker.exe %linker-input% %linker-options% %linker-output%

ECHO Linked files into a single ROM!

ECHO.

ECHO Adding asset data

addROMdata.exe %linker-output% %asset-instructions% %ROM-OUTPUT%

ECHO Asset data added

ECHO.

ECHO Created .sfc at %ROM-OUTPUT%!

PAUSE