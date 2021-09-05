###################################################
#   Main "Line" object for as65c assembler
#      by MrL314
#
#        [ Aug.19, 2020 ]
###################################################


# standard imports
import traceback

# local imports
import util








class Line(object):
	"""Main "Line" Object. Holds all useful data/functions for assembling a line of code."""


	def __init__(self, raw_line, line_number=-1, file=None, include_level=0):

		self._raw_line = raw_line          # raw line text
		self._line_number = line_number    # number of line in file
		self._file = file                  # raw file path
		self._file_name = None             # file name
		self._file_path = None             # relative file directory
		self._offset = 0                   # offset in current section (in bytes)
		self._data_bytes = []              # bytes after encoding line
		self._is_code = False              # indicates if line is a line of code
		self._include_lvl = include_level  # indicates level of include of file 
		self._already_included = False     # indicates that this line has not undergone the include process

		# turn full file path into directory path and file name
		if self._file != None: 
			self._file = self._file.lstrip().rstrip()  # remove excess whitespace on ends of file path
			self.set_file_attr(self._file)             # set file name and directory


		# whitespace cleaned, trimmed, and comment-removed line
		self._cleaned_line = self.clean_line(raw_line.split(';')[0])


		# line turned into its individual components
		self._parsed_line = self.parse_line(self._cleaned_line)





	def set_file_attr(self, file=None):
		"""Turn a file name into a file direrctory and file name"""

		if file == None:
			file = self._file

		# convert file path to Windows style file path
		file = file.replace("\\", "/")

		# split up path by directories
		split_path = file.split("/")



		if file.rfind("/") != -1:
			# if file is not in the same directory
			self._file_path = "/".join(split_path[:-1]) + "/" # file directory is everything up until file name

		# file name is last part of file path
		self._file_name = split_path[-1]

		# if file path not present, set empty
		if self._file_path == None:
			self._file_path = ""



	def clean_line(self, raw_line=None):
		"""Turns all single/multi whitespace into spaces, trims line, and converts symbols to proper spacing"""

		if raw_line == None:
			raw_line = self._raw_line


		raw_line = ' '.join(raw_line.split())      # clean whitespace

		raw_line = raw_line.replace("<<", util.BSL_CHAR).replace(">>", util.BSR_CHAR)   # convert bit shift operators to single chars 

		#raw_line = raw_line.replace("<<", util.BANK_CHAR).replace(">>", util._CHAR)   # convert bit shift operators to single chars 



		# clean the expressions up, in order to parse by symbols later
		for sym in util.PARSING_SYMBOLS:
			raw_line = raw_line.replace(sym.upper(), " " + sym.upper() + " ")           # space out parsing symbols (in uppercase)

			if sym.upper() != sym.lower():
				# if the symbol is a letter (for some reason)
				raw_line = raw_line.replace(sym.lower(), " " + sym.lower() + " ")       # space out parsing symbols (in lowercase)


		# clean up #BANK and #OFFSET as to not get mixed up later with const symbol: '#'
		s = raw_line.split(" ")
		for i in range(len(s)):
			item = s[i]
			if item.lower() == "#bank":
				s[i] = util.BANK_CHAR
			elif item.lower() == "#offset":
				s[i] = util.OFFSET_CHAR
			elif item.lower() == "#high":
				s[i] = util.HIGH_CHAR
			elif item.lower() == "#low":
				s[i] = util.LOW_CHAR

		raw_line = ' '.join(s)



		# clean up data type symbols, but ONLY if they appear at beginning of item
		for sym in util.TYPE_SYMBOLS:
			raw_line = raw_line.replace(" " + sym.upper(), " " + sym.upper() + " ")     # space out type symbols (in uppercase)

			if sym.upper() != sym.lower():
				# if the symbol is a letter (for some reason)
				raw_line = raw_line.replace(" " + sym.lower(), " " + sym.lower() + " ")       # space out type symbols (in lowercase)


		raw_line = ' '.join(raw_line.split())      # clean whitespace again just in case

		return raw_line





	def parse_line(self, cleaned_line=None, is_complete_line=True):
		"""Turns a cleaned up line into its parsed components, ready for the assembler to handle"""

		if cleaned_line == None:
			cleaned_line = self._cleaned_line

		if cleaned_line == "": return []


		LINE = cleaned_line.split(" ") # split into individual components



		# parsing stack
		parse_stack = []

		ind = 0

		if is_complete_line:
			# if not a reserved word at beginning of line, then it is a label
			if not LINE[0].lower() in util.RESERVED_FLAT:
				parse_stack.append({"type": util.DATA_TYPES.LABEL, "label": LINE[0], "varname": LINE[0]})   # indicate this is a label, so parser doesnt mess with it
				ind += 1
			elif LINE[0].lower() in util.CONDITIONAL_SYMBOLS:
				# is a conditional statement that affets assembler process

				if LINE[0].lower() == "if":
					parse_stack.append({"type": util.DATA_TYPES.CONDITIONAL_IF, "condition": LINE[1]})
					ind += 2
				elif LINE[0].lower() == "endif":
					parse_stack.append({"type": util.DATA_TYPES.CONDITIONAL_ENDIF})
					ind += 1

			elif LINE[0].lower() in util.INCLUDE_SYMBOLS:
				# is an include statement, so rest of line is a file

				filename = "".join(LINE[1:])

				parse_stack.append({"type": util.DATA_TYPES.INCLUDE, "filename": filename})

				ind += len(LINE)

			elif LINE[0].lower() in util.GLOBAL_SYMBOLS:
				# is a global variable identifier

				for item in LINE[1:]:
					if not (item in util.SEPARATOR_SYMBOLS):
						parse_stack.append({"type": util.DATA_TYPES.GLOBAL, "varname": item})

				ind += len(LINE)


			elif LINE[0].lower() in util.EXTERNAL_SYMBOLS:
				# is an external variable identifier

				for item in LINE[1:]:
					if not (item in util.SEPARATOR_SYMBOLS):
						parse_stack.append({"type": util.DATA_TYPES.EXTERNAL, "varname": item})

				ind += len(LINE)



		else:
			#print("IN SUB LINE: " + cleaned_line)
			pass


		while ind < len(LINE): # iterate through LINE to parse

			item = LINE[ind]




			if util.isValue(item):
				# item is a raw value, so turn it into one
				parse_stack.append({"type": util.DATA_TYPES.VALUE, "value": util.parseValue(item)})

			elif item in "+-([":
				# if unsure about status of symbol



				if item in "([":
					# if ambiguous separator

					#print("STACK BEFORE: " + str(parse_stack))

					if parse_stack[-1]["type"] in (util.DATA_TYPES.OPCODE, util.DATA_TYPES.EQU):

						was_op = False
						if parse_stack[-1]["type"] == util.DATA_TYPES.OPCODE:
							was_op = True

						off = 1
						numparens = 1
						ended = False

						# parse where end of this paren is
						while ind+off < len(LINE):

							if item == "(":
								if LINE[ind+off] == "(":
									numparens += 1
								elif LINE[ind+off] == ")":
									numparens -= 1

							elif item == "[":
								if LINE[ind+off] == "[":
									numparens += 1
								elif LINE[ind+off] == "]":
									numparens -= 1

							if numparens == 0:
								ended = True
								break

							off += 1

						# unbalanced parens
						if not ended:
							raise LineException(self.line_number, "unbalanced parens", self._file_name)

						#print("STACK: " + str(parse_stack))

						sub_parsed = self.parse_line(" ".join(LINE[ind+1:ind+off]), is_complete_line=False)

						
						
						if was_op:
							if item == "(":
								parse_stack.append({"type": util.DATA_TYPES.INDIRECT_START})
							elif item == "[":
								parse_stack.append({"type": util.DATA_TYPES.INDIRECT_LONG_START})
						else:
							parse_stack.append({"type": util.DATA_TYPES.OPERATOR, "operator": "("})
							


						
						for p in sub_parsed:
							parse_stack.append(p)


						if was_op:
							if item == "(":
								parse_stack.append({"type": util.DATA_TYPES.INDIRECT_END})
							elif item == "[":
								parse_stack.append({"type": util.DATA_TYPES.INDIRECT_LONG_END})
						else:
							parse_stack.append({"type": util.DATA_TYPES.OPERATOR, "operator": ")"})

						#print("AFTER: " + str(parse_stack))




						ind += off
						



					else:
						# just a priority paren
						parse_stack.append({"type": util.DATA_TYPES.OPERATOR, "operator": "("})


				elif item in "+-":

					isarith = True # default is arithetic symbol unless conditions met

					if item == "-" or item == "+":
						# check to see if this is a pos/neg or if it is an arithmetic +/-

						# is pos/neg iff :
						# 1. next item is a value
						# 2. prev item is NOT a value, variable, or expression
						# 3. if prev item is an operator, must not be closed paren
						if ind != len(LINE)-1 and ind != 0:
							if util.isValue(LINE[ind+1]): # next item is value 
								if parse_stack[-1]["type"] != util.DATA_TYPES.VALUE:  # prev item not value
									if parse_stack[-1]["type"] != util.DATA_TYPES.VARIABLE:  # prev item not variable
										if parse_stack[-1]["type"] != util.DATA_TYPES.EXPRESSION:  # prev item not expression
											# fits all criterion to be pos/neg
											isarith = False

											if parse_stack[-1]["type"] == util.DATA_TYPES.OPERATOR:
												# prev item is an operator, check if it is a closed parenthesis

												if parse_stack[-1]["operator"] == ")":
													# if prev item is closed paren, must be an operator
													isarith = True

												if parse_stack[-1]["operator"] == "]":
													# if prev item is closed paren, must be an operator
													isarith = True

						else:
							isarith = False





						if not isarith:
							# base value is next item
							val = util.parseValue(LINE[ind+1])

							if item == "-": 
								# if pos, no change is needed
								# however, if neg, need to turn to negative value 
								val = -1*val


							parse_stack.append({"type": util.DATA_TYPES.VALUE, "value": val})

							ind += 1 # skip over next item

						else:
							# is an arithmetic op
							parse_stack.append({"type": util.DATA_TYPES.OPERATOR, "operator": item})






			elif item.lower() in util.ARITHMETIC_SYMBOLS:
				# item is an operator
				parse_stack.append({"type": util.DATA_TYPES.OPERATOR, "operator": item})


			elif item.lower() in util.REGISTER_SYMBOLS:
				# item is a register

				reg = util.NONE
				if item.lower() in util.REGA_SYMBOLS:
					reg = "a"
				elif item.lower() in util.REGX_SYMBOLS:
					reg = "x"
				elif item.lower() in util.REGY_SYMBOLS:
					reg = "y"
				elif item.lower() in util.REGS_SYMBOLS:
					reg = "s"

				if reg != util.NONE:
					parse_stack.append({"type": util.DATA_TYPES.REGISTER, "register": reg})

				if reg == "s":
					if len(parse_stack) >= 4:
						if parse_stack[-4]["type"] == util.DATA_TYPES.OPCODE or parse_stack[-4]["type"] == util.DATA_TYPES.INDIRECT_START:
							parse_stack.insert(len(parse_stack) - 3, {"type": util.DATA_TYPES.TYPE, "valtype": "sr", "size": 1})


			elif item.lower() in util.SEPARATOR_SYMBOLS:
				# item is a separator, pretty simple
				parse_stack.append({"type": util.DATA_TYPES.SEPARATOR})

			elif item.lower() in util.OPCODE_SYMBOLS:
				# item is an opode mnemonic
				parse_stack.append({"type": util.DATA_TYPES.OPCODE, "opcode": item, "size": 1, "reg": util.OPCODE_REGS[item.lower()]})

			elif item.lower() in util.TYPE_SYMBOLS:
				# item is a designator for a type

				itemtype = util.NONE

				if item.lower() == "<":
					itemtype = "dp"
					size = 1
				elif item.lower() == "!":
					itemtype = "addr"
					size = 2
				elif item.lower() == ">":
					itemtype = "long"
					size = 3
				elif item.lower() == "#":
					itemtype = "const"
					size = None
				elif item.lower() == util.BANK_CHAR:
					itemtype = "bank"
					size = 1
				elif item.lower() == util.OFFSET_CHAR:
					itemtype = "offset"
					size = 2
				elif item.lower() == util.HIGH_CHAR:
					itemtype = "high"
					size = 1
				elif item.lower() == util.LOW_CHAR:
					itemtype = "low"
					size = 1
				elif item.lower() == "$":
					itemtype = "constaddr"
					size = None

				if itemtype != util.NONE:
					parse_stack.append({"type": util.DATA_TYPES.TYPE, "valtype": itemtype, "size": size})

			elif item.lower() in util.GLOBAL_SYMBOLS:
				# item is an identifier for a global variable
				parse_stack.append({"type": util.DATA_TYPES.GLOBAL})

			elif item.lower() in util.EXTERNAL_SYMBOLS:
				# item is an identifier for an external variable
				parse_stack.append({"type": util.DATA_TYPES.EXTERNAL})

			elif item.lower() in util.INCLUDE_SYMBOLS:
				# item is an identifier for an included file
				parse_stack.append({"type": util.DATA_TYPES.INCLUDE})

			elif item.lower() in util.SECTION_SYMBOLS:
				# item is an identifier for a section
				parse_stack.append({"type": util.DATA_TYPES.SECTION})

				if ind+1 < len(LINE):
					parse_stack[-1]["SECTION_CLASS"] = LINE[ind+1]

					ind += 1
				else:
					parse_stack[-1]["SECTION_CLASS"] = "REL"

			elif item.lower() in util.GROUP_SYMBOLS:
				# item is an identifier for a group
				parse_stack.append({"type": util.DATA_TYPES.GROUP})

				if ind+1 < len(LINE):
					parse_stack[-1]["SECTION_GROUP"] = LINE[ind+1]

					ind += 1

			elif item.lower() in util.ORG_SYMBOLS:
				# item is an identifier for an org specifier
				lbl = self._file_name.split(".")[0]
				parse_stack.append({"type": util.DATA_TYPES.LABEL, "label": lbl, "varname": lbl})
				parse_stack.append({"type": util.DATA_TYPES.ORG})

				if LINE[ind+1].lower() == "$":
					ind += 1

				parse_stack[-1]["offset"] = util.parseValue(LINE[ind+1].replace("h", "").replace("H", "") + "h")
				ind += 1

			elif item.lower() in util.DBANK_SYMBOLS:
				# item is an identifier for a dbank instruction
				parse_stack.append({"type": util.DATA_TYPES.DATA_BANK})

				sub_parsed = self.parse_line(" ".join(LINE[ind+1:]), is_complete_line=False)

				parse_stack[-1]["bank"] = []

				for p in sub_parsed:
					parse_stack[-1]["bank"].append(p)

				ind += len(sub_parsed)

			elif item.lower() in util.DPAGE_SYMBOLS:
				# item is an identifier for a dpage instruction
				parse_stack.append({"type": util.DATA_TYPES.DATA_PAGE})

				sub_parsed = self.parse_line(" ".join(LINE[ind+1:]), is_complete_line=False)

				parse_stack[-1]["page"] = []

				for p in sub_parsed:
					parse_stack[-1]["page"].append(p)

				ind += len(sub_parsed)

			elif item.lower() in util.END_SYMBOLS:
				# item is an identifier for an END instruction
				parse_stack.append({"type": util.DATA_TYPES.END})

			elif item.lower() in util.PROCESSOR_SYMBOLS:
				# item is an identifier for a processor flag
				parse_stack.append({"type": util.DATA_TYPES.PFLAG, "flag": item.lower()})

			elif item.lower() in util.EQU_SYMBOLS:
				# item is an identifier for an EQU identifier

				var = parse_stack.pop()["varname"]
				parse_stack.append({"type": util.DATA_TYPES.EQU, "varname": var, "label": var})

				#print(str(LINE), str(parse_stack))

			elif item.lower() in util.DATA_SYMBOLS:
				# item is an identifier for byte data

				if item.lower() in util.BYTE_SYMBOLS:
					datatype = util.DATA_TYPES.DBYTE
				elif item.lower() in util.WORD_SYMBOLS:
					datatype = util.DATA_TYPES.DWORD
				elif item.lower() in util.LONG_SYMBOLS:
					datatype = util.DATA_TYPES.DLONG

				parse_stack.append({"type": datatype})

			elif item.lower() in util.PSEG_SYMBOLS:
				# item is an identifier for a PROGRAM section
				lbl = "P" + self._file_name.split(".")[0]
				parse_stack.append({"type": util.DATA_TYPES.LABEL, "label": lbl, "varname": lbl})
				parse_stack.append({"type": util.DATA_TYPES.SECTION})

			elif item.lower() in util.DSEG_SYMBOLS:
				# item is an identifier for a DATA section
				lbl = "D" + self._file_name.split(".")[0]
				parse_stack.append({"type": util.DATA_TYPES.LABEL, "label": lbl, "varname": lbl})
				parse_stack.append({"type": util.DATA_TYPES.SECTION})

			elif item.lower() in util.COMN_SYMBOLS:
				# item is an identifier for a COMN section
				lbl = "COMN"
				parse_stack.append({"type": util.DATA_TYPES.LABEL, "label": lbl, "varname": lbl})
				parse_stack.append({"type": util.DATA_TYPES.SECTION})

			else:
				# item is a variable

				if item[-1] == "$":
					# "near" variable

					size = 2
					if parse_stack != []:
						if parse_stack[-1]["type"] == util.DATA_TYPES.OPCODE:
							if parse_stack[-1]["opcode"].lower() in ("bcc", "blt", "bcs", "bge", "beq", "bmi", "bne", "bpl", "bra", "bvc", "bvs"):
								size = 1

					parse_stack.append({"type": util.DATA_TYPES.VARIABLE, "varname": item, "label": item, "vartype": util.DATA_TYPES.NEARVAR, "size": size})

				else:
					# normal variable name, possibly

					is_normal = True

					size = 0
					if parse_stack != []:
						if parse_stack[-1]["type"] == util.DATA_TYPES.OPCODE:
							if parse_stack[-1]["opcode"].lower() in ("bcc", "blt", "bcs", "bge", "beq", "bmi", "bne", "bpl", "bra", "bvc", "bvs", "brl", "per"):
								# "near" variable 
								is_normal = False

								size = 1

								if parse_stack[-1]["opcode"].lower() in ("brl", "per"):
									size = 2

								parse_stack.append({"type": util.DATA_TYPES.VARIABLE, "varname": item, "label": item, "vartype": util.DATA_TYPES.NEARVAR, "size": size})


					if is_normal:
						if parse_stack != []:
							if parse_stack[-1]["type"] != util.DATA_TYPES.TYPE:
								size = 2
						parse_stack.append({"type": util.DATA_TYPES.VARIABLE, "varname": item, "label": item, "vartype": util.DATA_TYPES.NORMALVAR, "size": size})
						






			# mercy its over thank god
			ind += 1


		for p in range(len(parse_stack)):
			if not ("size" in parse_stack[p]):
				parse_stack[p]["size"] = 0


		return parse_stack


	def get_parsed(self):
		return self._parsed_line
	
	def set_parsed(self, P):
		self._parsed_line = [p for p in P]

		for p in range(len(self._parsed_line)):
			if not ("size" in self._parsed_line[p]):
				self._parsed_line[p]["size"] = 0

	def get_file_path(self):
		return self._file_path

	def get_file_name(self):
		return self._file_name

	def get_line_num(self):
		return self._line_number

	def set_offset(self, o):
		self._offset = o

	def get_offset(self):
		return self._offset

	def get_raw(self):
		return self._raw_line.split(";")[0]

	def set_bytes(self, b):
		self._data_bytes = b

	def get_bytes(self):
		return self._data_bytes


	def set_is_not_code(self):
		self._is_code = False

	def set_is_code(self):
		self._is_code = True

	def is_code(self):
		return self.is_code


	def set_include_level(self, level):
		self._include_lvl = level

	def get_include_level(self):
		return self._include_lvl

	def is_included(self):
		if self._include_lvl > 0:
			return True
		else:
			return False

	def set_already_included(self):
		self._already_included = True

	def already_included(self):
		return self._already_included














if __name__ == "__main__":

	TEXT = ";---------------------------------------------------------------------\n; ƒMƒuƒAƒbƒv•\Ž¦\n;---------------------------------------------------------------------\nDisp_giveup	LDA	#button_trigger+1\n\t\tCLC\n\t\tADC	!pause_index\n\t\tTAY\n\t\tLDA	#-0100H\n\t\tLDX	#pause_cursor\n\t\tJSR	Calc_cursor2\n\t\tLDA	#POS_GIVEUP\n\t\tLDY	#pause_test\n\t\tJSR	Sprite_set\n;- - - - - - - - - - - - - - - - - - - - - - \n\t\tLDA	#(POS_YESNO-0010H)\n\t\tLDX	!pause_cursor\n\t\tBEQ	skip$\n\t\tLDA	#(POS_YESNO+1000H-0010H)\nskip$		LDY	#pause_sign\n\t\tJMP	Sprite_set_FR\n;*********************************************************************\n;	ƒ|[ƒY‰ðœŒã‚Ìˆ—\n;	( ‚Í‚¢A‚¢‚¢‚¦@‚ð‘I‘ð‚µ‚½Œã‚Ì‹¤’Êˆ— )\n;*********************************************************************\nExit_pause	\n;- - - - - - - - - - - - - - - - - - - - - - \ncheck_retire	BIT	!replay_flag\n\t\tBMI	replay$\n\t\tLDA	!pause_cursor		; ƒŠƒ^ƒCƒA‚·‚é‚©H\n\t\tBNE	goback_entry		; no->skip\n\t\tBEQ	retire$\n;- - - - - - - - - - - - - - - - - - - - - - "

	LINES = []
	for L in TEXT.split("\n"):
		LINES.append(Line(L, "../Pause.asm"))



	for line in LINES:
		print(line._raw_line)
		print(str(line.get_parsed()))

		print("\n")



