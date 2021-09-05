###################################################
#   Helper data and functions for as65c assembler
#      by MrL314
#
#        [ Aug.19, 2020 ]
###################################################









# standard imports


# local imports
import exceptions
global DATA_TYPES
import datatypes as DATA_TYPES




# global export variables
global BSR_CHAR
global BSL_CHAR
global BANK_CHAR
global OFFSET_CHAR
global HIGH_CHAR
global LOW_CHAR
global ARITHMETIC_SYMBOLS
global OPCODE_SYMBOLS
global REGA_SYMBOLS
global REGX_SYMBOLS
global REGY_SYMBOLS
global REGS_SYMBOLS
global REGISTER_SYMBOLS
global SEPARATOR_SYMBOLS
global TYPE_SYMBOLS
global GLOBAL_SYMBOLS
global EXTERNAL_SYMBOLS
global INCLUDE_SYMBOLS
global SECTION_SYMBOLS
global PSEG_SYMBOLS
global DSEG_SYMBOLS
global COMN_SYMBOLS
global GROUP_SYMBOLS
global ORG_SYMBOLS
global DBANK_SYMBOLS
global DPAGE_SYMBOLS
global END_SYMBOLS
global PROCESSOR_SYMBOLS
global EQU_SYMBOLS
global BYTE_SYMBOLS
global WORD_SYMBOLS
global LONG_SYMBOLS
global DATA_SYMBOLS
global OTHER_SYMBOLS
global PARSING_SYMBOLS
global RESERVED
global RESERVED_FLAT
global NONE






def flatten_list(L):
	"""Turns a nested list into a flattened list, ordered by nesting order."""

	if type(L) in LIST_TYPES:
		# is a list, can be nested or not

		flattened = []

		for elem in L:
			# for each element of the "nested" list...

			for item in flatten_list(elem):
				# (recursive step)
				# ... append the items of the flattened
				# out version of that element to the 
				# final flattened out list 

				flattened.append(item)


		# return the flattened out list
		return flattened


	else:
		# if not a list, but an item...
		# end recursion and return a list containing
		# only that element, for code clarity
		return [L]












# types of list objects
#             tuple     list
LIST_TYPES = (type(()), type([]))





# bit shift operation symbols
BSL_CHAR = "«"   # ALT + 174
BSR_CHAR = "»"   # ALT + 175

# bank/offset symbols
BANK_CHAR = "@"
OFFSET_CHAR = "`"
HIGH_CHAR = "╦"  # ALT + 203 
LOW_CHAR = "╚"   # ALT + 200

# symbols used in simple arithmetic in code
ARITHMETIC_SYMBOLS = ("+", "-", "*", "/", "%", BSL_CHAR, BSR_CHAR, "|", "&", "^", "(", ")")

# symbols for separators
SEPARATOR_SYMBOLS = ("(", ")", "[", "]", ",")

# symbols for opcodes
OPCODE_SYMBOLS = ("adc", "and", "asl", "bcc", "blt", "bcs", "bge", "beq", "bit", "bmi", "bne", "bpl", "bra", "brk", "brl", "bvc", "bvs", "clc", "cld", "cli", "clv", "cmp", "cop", "cpx", "cpy", "dec", "dea", "dex", "dey", "eor", "inc", "ina", "inx", "iny", "jmp", "jml", "jsr", "jsl", "lda", "ldx", "ldy", "lsr", "mvn", "mvp", "nop", "ora", "pea", "pei", "per", "pha", "phb", "phd", "phk", "php", "phx", "phy", "pla", "plb", "pld", "plp", "plx", "ply", "rep", "rol", "ror", "rti", "rtl", "rts", "sbc", "sec", "sed", "sei", "sep", "sta", "stp", "stx", "sty", "stz", "tax", "tay", "tcd", "tcs", "tdc", "trb", "tsb", "tsc", "tsx", "txa", "txs", "txy", "tya", "tyx", "wai", "wdm", "xba", "xce")
OPCODE_REGS = {
	"adc": "a", 
	"and": "a", 
	"asl": None, 
	"bcc": None, 
	"blt": None, 
	"bcs": None, 
	"bge": None, 
	"beq": None, 
	"bit": "a", 
	"bmi": None, 
	"bne": None, 
	"bpl": None, 
	"bra": None, 
	"brk": None, 
	"brl": None, 
	"bvc": None, 
	"bvs": None, 
	"clc": None, 
	"cld": None, 
	"cli": None,
	"clv": None, 
	"cmp": "a", 
	"cop": "p", 
	"cpx": "x", 
	"cpy": "y", 
	"dec": None, 
	"dea": None, 
	"dex": None, 
	"dey": None, 
	"eor": "a", 
	"inc": None, 
	"ina": None, 
	"inx": None, 
	"iny": None, 
	"jmp": None, 
	"jml": None, 
	"jsr": None, 
	"jsl": None, 
	"lda": "a", 
	"ldx": "x", 
	"ldy": "y", 
	"lsr": None, 
	"mvn": None, 
	"mvp": None, 
	"nop": None, 
	"ora": "a", 
	"pea": "s", 
	"pei": None, 
	"per": None, 
	"pha": None, 
	"phb": None, 
	"phd": None, 
	"phk": None,
	"php": None, 
	"phx": None, 
	"phy": None, 
	"pla": None, 
	"plb": None, 
	"pld": None, 
	"plp": None, 
	"plx": None, 
	"ply": None, 
	"rep": "p", 
	"rol": None, 
	"ror": None, 
	"rti": None, 
	"rtl": None, 
	"rts": None, 
	"sbc": "a", 
	"sec": None, 
	"sed": None, 
	"sei": None, 
	"sep": "p", 
	"sta": None, 
	"stp": None, 
	"stx": None, 
	"sty": None, 
	"stz": None, 
	"tax": None, 
	"tay": None, 
	"tcd": None, 
	"tcs": None, 
	"tdc": None, 
	"trb": None, 
	"tsb": None, 
	"tsc": None, 
	"tsx": None, 
	"txa": None, 
	"txs": None, 
	"txy": None, 
	"tya": None, 
	"tyx": None, 
	"wai": None, 
	"wdm": None, 
	"xba": None, 
	"xce": None}

# symbols for accumulator register
REGA_SYMBOLS = ("a", "acc", "accumulator", "accum")

# symbols for x register
REGX_SYMBOLS = ("x")

# symbols for y register
REGY_SYMBOLS = ("y")

# symbols for stack register
REGS_SYMBOLS = ("s", "stack")

# symbols for registers
REGISTER_SYMBOLS = flatten_list((REGA_SYMBOLS, REGX_SYMBOLS, REGY_SYMBOLS, REGS_SYMBOLS))



# symbols for data types
TYPE_SYMBOLS = ("<", ">", "!", "#", BANK_CHAR, OFFSET_CHAR, HIGH_CHAR, LOW_CHAR, "$")


# symbols to declare global
GLOBAL_SYMBOLS = ("glb", "global", "glob")

# symbols to declare external
EXTERNAL_SYMBOLS = ("ext", "external", "extern")

# symbols to declare include file
INCLUDE_SYMBOLS = ("incl", "include")



# symbols to declare section
SECTION_SYMBOLS = ("sect", "section")

# symbols to declare program section
PSEG_SYMBOLS = ("prog", "program")

# symbols to declare data section
DSEG_SYMBOLS = ("data")

# symbols to declare common section
COMN_SYMBOLS = ("comn", "common")

# symbols to declare group
GROUP_SYMBOLS = ("group", "grp")

# symbols to declare org section
ORG_SYMBOLS = ("org")



# symbols to declare data bank
DBANK_SYMBOLS = ("dbank", "databank")

# symbols to declare data page
DPAGE_SYMBOLS = ("dpage", "datapage")


# symbols to declare end
END_SYMBOLS = ("end", "endm")   # endm is end macro


# symbols for processor flags
PROCESSOR_SYMBOLS = ("mem8", "mem16", "idx8", "idx16")


# symbols to declare variable value
EQU_SYMBOLS = ("equ", "equal", "equals")



# symbols to declare byte data
BYTE_SYMBOLS = ("byte", "bytes", "db")

# symbols to declare word data
WORD_SYMBOLS = ("word", "words", "dw")

# symbols to declare long data
LONG_SYMBOLS = ("long", "longs", "dl")

# symbols to declare data
DATA_SYMBOLS = flatten_list((BYTE_SYMBOLS, WORD_SYMBOLS, LONG_SYMBOLS))



# symbols that affect compilation flow
CONDITIONAL_SYMBOLS = ("if", "endif")

# symbols that arent compiled but I don't know what to do with them yet
OTHER_SYMBOLS = ("native", "extend", "list", "nolist", "rel")


# list of symbols used in parsing the data
PARSING_SYMBOLS = flatten_list((SEPARATOR_SYMBOLS, ARITHMETIC_SYMBOLS))

# list of reserved names
RESERVED = (
	REGISTER_SYMBOLS,    # register names
	PARSING_SYMBOLS,     # parsing
	OPCODE_SYMBOLS,      # opcode mnemonics
	TYPE_SYMBOLS,        # data types
	GLOBAL_SYMBOLS, EXTERNAL_SYMBOLS,               # global variables
	INCLUDE_SYMBOLS,                                # included files
	SECTION_SYMBOLS, GROUP_SYMBOLS, ORG_SYMBOLS,    # sections
	DBANK_SYMBOLS, DPAGE_SYMBOLS,                   # data bank/page
	END_SYMBOLS,         # end of sections
	PROCESSOR_SYMBOLS,   # processor flags
	EQU_SYMBOLS,         # variables
	DATA_SYMBOLS,        # data
	CONDITIONAL_SYMBOLS, # assembler flow conditionals
	OTHER_SYMBOLS        # other
	)



RESERVED_FLAT = flatten_list(RESERVED)


NONE = None












def size_to_bytes(size):
	"""Converts the number for a size into the REL format for size."""

	if size < 0x80:
		# if smaller than 0x80 bytes, set "small size" bit of size
		return [size | 0x80]

	else:
		# if larger than 0x80 bytes, convert into size_len+size format

		num_bytes = 0

		size_bytes = []

		while size != 0:
			size_bytes.append(size % 256)
			size = size // 256
			num_bytes += 1

		if num_bytes > 0x7f:
			raise 




def is_int(v):
	try:
		int(v)
		return True
	except:
		return False

def is_operator(t):
	if t in "+-/*%&|^" + BSL_CHAR + BSR_CHAR:
		return True


def get_precedence(t):

	if t == "*" or t == "/" or t == "%":
		return 6
	elif t == "+" or t == "-":
		return 5
	elif t == BSL_CHAR or t == BSR_CHAR:
		return 4
	elif t == "&": 
		return 3
	elif t == "^":
		return 2
	elif t == "|":
		return 1
	else:
		return 0




def evaluateExpression(EXP):

	E = EXP.replace("[", "(").replace("]", ")")
	E = " ".join(E.split()).split(" ")


	# convert infix to postfix via Shunting-yard algorithm
	output_queue = []
	operator_stack = []

	for tok in E:
		if is_int(tok):
			output_queue.append(tok)

		elif is_operator(tok):
			while operator_stack != []:
				if get_precedence(operator_stack[-1]) >= get_precedence(tok):
					if operator_stack[-1] != "(":
						output_queue.append(operator_stack.pop())
					else:
						break
				else:
					break

			operator_stack.append(tok)

		elif tok == "(":
			operator_stack.append(tok)

		elif tok == ")":
			while operator_stack != [] and operator_stack[-1] != "(":
				output_queue.append(operator_stack.pop())

			if operator_stack != []:
				if operator_stack[-1] == "(":
					operator_stack.pop()

	while operator_stack != []:
		output_queue.append(operator_stack.pop())


	# output_queue is now a postfix expression, which is easier to evaluate

	#print(output_queue, E)

	# postfix evaluation algorithm

	eval_stack = []

	for tok in output_queue:
		if is_int(tok):
			eval_stack.append(int(tok))

		elif is_operator(tok):

			right_arg = eval_stack.pop()
			left_arg = eval_stack.pop()

			if tok == "+":
				val = left_arg + right_arg
			elif tok == "-":
				val = left_arg - right_arg
			elif tok == "*":
				val = left_arg * right_arg
			elif tok == "/":
				val = left_arg // right_arg
			elif tok == "%":
				val = left_arg % right_arg
			elif tok == "&":
				val = left_arg & right_arg
			elif tok == "|":
				val = left_arg | right_arg
			elif tok == "^":
				val = left_arg ^ right_arg
			elif tok == BSL_CHAR:
				val = left_arg << right_arg
			elif tok == BSR_CHAR:
				val = left_arg >> right_arg
			else:
				raise Exception("Bad expression " + " ".join(E))

			eval_stack.append(val)

		else:
			raise Exception("Bad expression " + " ".join(E))


	if len(eval_stack) == 1:
		return eval_stack[0]
	else:
		raise Exception("Error evaluating " + " ".join(E))







def isValue(v):
	"""Returns true if the input is a type of value literal"""
	try:
		# if this works, the value is a decimal number
		int(v)
		return True
	except:
		pass
	
	try:
		if v[-1].lower() == "b":
			# if this works, the value is a binary number
			int("0b" + v[:-1], 2)
			return True
		elif v[-1].lower() == "h":
			# if this works, the value is a hex number
			int("0x" + v[:-1], 16)
			return True
		else:
			return False
	except:
		pass

	return False



def parseValue(v):
	"""Converts different types of values from string form into in integer""" 

	try:
		# if this works, the value is a decimal number
		return int(v)
	except:
		pass
	
	try:
		if v[-1].lower() == "b":
			# if this works, the value is a binary number
			return int("0b" + v[:-1], 2)
		elif v[-1].lower() == "h":
			# if this works, the value is a hex number
			return int("0x" + v[:-1], 16)
		else:
			raise TypeError("Invalid value type: " + str(type(v)) + " " + str(v))
	except:
		pass

	raise TypeError("Invalid value type: " + str(type(v)) + " " + str(v))



def get_symbols(file):

	lines = []
	with open(file, "r") as f:

		for line in f:
			lines.append(line.replace("\n", ""))


	symbols = []

	for line in lines:
		parsed = line.split("   ")

		try:
			var = parsed[0]
			vartype = parsed[1]
			varval = int(parsed[2])

			symbols.append((var, vartype, varval))
		except IndexError as e:
			raise e



	return symbols




def set_symbols(symbols, file):

	with open(file, "w") as f:

		for var in symbols:
			#        var name             var type                     var value
			f.write(str(var) + "   " + str(symbols[var][0]) + "   " + str(symbols[var][1]) + "\n")



if __name__ == "__main__":
	L = (1, ((2, 3, (4)), 5, (6), 7), 8, (9, (10)))

	print(flatten_list(L))

