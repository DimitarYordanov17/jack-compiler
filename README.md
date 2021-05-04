# jack-compiler
A full compiler for the Jack programming language (examined in "The Elements of Computing Systems" book), written in Python.

The program is a two-stage compiler, designed to work with medium files - VM, XML and ASM, in order to produce a final machine code file - out.hack.
This compiler is designed for the Hack (theoretical) computer, as presented in the above mentioned book. In order to run the compiled file, you would need
to have the free software shared with the book.

WARNING:
The Hack computer emulator has a limit on how big of a file it can load. If you are compiling a pretty big Jack program, e.g. the pong game, which is available at /tests, it wouldn't
be possible to directly load the out.hack file in the emulator, but there is still a way to run the program. In order to do that, you should compile it with the option keep_vm=yes and then
load the vm code in the VMEmulator (which is also free, supplied by the authors).
