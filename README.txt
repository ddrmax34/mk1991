#######################################
#    RICOH as65c REMAKE   by MrL314   #
#######################################




If creating the alpha prototype, simply find these files:

	in NEWS/NEWS_05/home/kimura/exp:
		calc-exp.asm
		check-exp.asm
		ctrl-exp.asm
		data-exp.asm
		init-exp.asm
		set-bg.asm
		set-obj.asm
		sfx-exp.asm
		buffer
		D77C25
		rp5a22
		rp5c77
		work

and place them in 1991_alpha/CODE.
You will need to edit line 260 of set-bg.asm, and put a ! in front of the 2135h.
That will fix a fatal error that prevents the game from working as intended. 



For the assets, I do not remember which exact files I used, but look in the
file named "ROM files.txt". I have put my best estimate as to which file 
goes where, and what each one does, but you will need those files, or at
least replacement files that would replace where those files go. For example, 
if you wanted to change the Mario spriteset, set the file under "# mario car"
as your replacement file, but do not touch anything else. Put the asset files
in 1991_alpha/DATA.
If you would like the files I used, contact me directly through discord
	MrL314#8106
		




If you are intending to use this as a general purpose assembler, BE CAREFUL!!!
This assembler was formatted after the programming practices used in SMK source
files, meaning that the syntax is very strict. As such,

   put ! before 2-byte word values
   put < before 1-byte direct-page values
   put > before 3-byte long values
   put # before const values

These are not necessary in data tables, but in code it is necessary for this
assembler to work. 




To assemble the game, simply run createROM.bat




To debug rel files, use the "rel reader.py" program. Simply run
	rel_reader.exe <file>




I will be writing a more in-depth instruction manual soon, but I would like to 
get a beta version of this out before it becomes too much hassle. So stay up
to date with the newest releases on the discord server:
	https://discord.gg/QNcKNQC


