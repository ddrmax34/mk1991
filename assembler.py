###################################################
#   Main as65c assembler program
#      by MrL314
#
#        [ Aug.26, 2020 ]
###################################################



# standard imports
import traceback
import sys, os
import math
from datetime import date, datetime
import argparse

# local imports
import LineObject
import util
from exceptions import LineException




# stupid fix because python didnt want to keep this as the working directory
#abspath = os.path.abspath(__file__)
#dname = os.path.dirname(abspath)
os.chdir(os.getcwd())





# temp variable indicator symbols, change later to impossible symbols
TEMP_LEFT = "<" # "◄"
TEMP_RIGHT = ">" # "►"



SYMBOLS_FILE = "SYMBOLS.txt"


EXTERNAL_SYMBOLS = {}



def get_symbols(file):

	global EXTERNAL_SYMBOLS


	for var, vartype, varval in util.get_symbols(file):
		EXTERNAL_SYMBOLS[var] = (vartype, varval)



def set_symbols(file):

	global EXTERNAL_SYMBOLS


	util.set_symbols(EXTERNAL_SYMBOLS, file)











def read_file(filename):

	lines = []

	with open(filename, "r", encoding="utf-8", errors="ignore") as file:
		for line in file:
			lines.append(line.replace("\n", ""))


	return lines



def read_bin_file(filename):

	lines = []
	with open(filename, "rb") as file:

		data = file.read()

		ind = 0

		# parse each 16 bytes as a data line
		while ind < len(data):
			data_line = data[ind:ind+16]
			ind += 16

			line = "\t\tdb\t" # match format of regular code

			for d in range(len(data_line)):
				if d != 0:
					line += ", "
				line += format(data_line, "02x") + "h"

			lines.append(line)

	return lines





def getsecind(s):
	if s > 1:
		return s + 1
	else:
		return s







def parse_format(i_form):
	
	out_form = []

	FORM = i_form.split(" ")

	for el in FORM:
		out_parsed = {"type": None, "valtype": None, "register": None}

		if el.lower() == "(":
			out_parsed["type"] = util.DATA_TYPES.INDIRECT_START

		elif el.lower() == ")":
			out_parsed["type"] = util.DATA_TYPES.INDIRECT_END

		elif el.lower() == "[":
			out_parsed["type"] = util.DATA_TYPES.INDIRECT_LONG_START
		
		elif el.lower() == "]":
			out_parsed["type"] = util.DATA_TYPES.INDIRECT_LONG_END
		
		elif el.lower() == ",":
			out_parsed["type"] = util.DATA_TYPES.SEPARATOR
		
		elif el.lower() == "dp":
			out_parsed["type"] = util.DATA_TYPES.TYPE
			out_parsed["valtype"] = "dp"

		elif el.lower() == "sr":
			out_parsed["type"] = util.DATA_TYPES.TYPE
			out_parsed["valtype"] = "sr"
		
		elif el.lower() == "addr":
			out_parsed["type"] = util.DATA_TYPES.TYPE
			out_parsed["valtype"] = "addr"
		
		elif el.lower() == "long":
			out_parsed["type"] = util.DATA_TYPES.TYPE
			out_parsed["valtype"] = "long"
		
		elif el.lower() == "#const":
			out_parsed["type"] = util.DATA_TYPES.TYPE
			out_parsed["valtype"] = "const"
		
		elif el.lower() == "x":
			out_parsed["type"] = util.DATA_TYPES.REGISTER
			out_parsed["register"] = "x"

		elif el.lower() == "y":
			out_parsed["type"] = util.DATA_TYPES.REGISTER
			out_parsed["register"] = "y"

		elif el.lower() == "a":
			out_parsed["type"] = util.DATA_TYPES.REGISTER
			out_parsed["register"] = "a"

		elif el.lower() == "s":
			out_parsed["type"] = util.DATA_TYPES.REGISTER
			out_parsed["register"] = "s"

		else:
			raise Exception("invalid parse token in " + " ".join(i_form))

		out_form.append(out_parsed)

	return out_form
		

	



def parse_instruction(LINE, FORMATS, instruction, LINE_OBJ):

	opcode = -1


	FORMS = [(parse_format(F[0]), F[1]) for F in FORMATS]

	good_formats = []

	LINE = LINE[1:]


	for F in FORMS:

		form = F[0]

		if len(form) > len(LINE):
			# skip format if longer than line
			continue


		for L in range(len(LINE)+1): # one longer to account for break if condition good (cleaner code) 

			if L >= len(form):
				good_formats.append(F)
				break

			el = LINE[L]

			f = form[L]

			if el["type"] == f["type"]:
				if f["type"] == util.DATA_TYPES.INDIRECT_START:
					pass
				elif f["type"] == util.DATA_TYPES.INDIRECT_END:
					pass
				elif f["type"] == util.DATA_TYPES.INDIRECT_LONG_START:
					pass
				elif f["type"] == util.DATA_TYPES.INDIRECT_LONG_END:
					pass
				elif f["type"] == util.DATA_TYPES.SEPARATOR:
					pass
				elif f["type"] == util.DATA_TYPES.TYPE:

					if el["valtype"] == f["valtype"]:
						pass
					elif el["valtype"] in ("bank", "offset", "high", "low", "const"):

						if f["valtype"] != "const":
							break
					else:
						break

				elif f["type"] == util.DATA_TYPES.REGISTER:
					if el["register"] != f["register"]:
						break

				else:
					break
			else:
				break



	longest = -1


	for f, op in good_formats:
		if len(f) > longest:
			longest = len(f)
			opcode = op



	if opcode == -1:
		raise LineException(LINE_OBJ.get_line_num(), "Cannot encode instruction " + instruction + ". Improper format. " + str(LINE_OBJ.get_raw()) + "\n" + str(LINE_OBJ.get_parsed()), LINE_OBJ.get_file_name())


	return opcode




def make_length_bytes(L):

	size_bytes = []

	while L != 0:
		size_bytes.append(L % 256)

		L = L // 256

	if len(size_bytes) == 1:
		if size_bytes[0] < 0x80:
			size_bytes[0] = size_bytes[0] | 0x80
		else:
			size_bytes.append(1)
	else:
		size_bytes.append(len(size_bytes))

	return [x for x in reversed(size_bytes)]


















def assembleFile(filename, ext_vars={}):

	global EXTERNAL_SYMBOLS

	get_symbols(SYMBOLS_FILE)


	LINES = []
	lnum = 1
	for line in read_file(filename):
		LINES.append(LineObject.Line(line, file=filename, line_number=lnum, include_level=0))
		lnum += 1



	FILE_NAME = LINES[0].get_file_name()
	FILE_PATH = LINES[0].get_file_path()


	tempvar = 0 # temp variable indicator number


	localvars = [
		{"name": "   ", "value": 0, "offset": None, "section": None, "type": "exact", "is_temp": True}, 
		{"name": "REL", "value": 0, "offset": None, "section": None, "type": "exact", "is_temp": True}
	]
	globalvars = [""]
	externalvars = [""]

	# add external symbols to local variable pool
	for var in EXTERNAL_SYMBOLS:
		vartype, varval = EXTERNAL_SYMBOLS[var]

		localvars.append({"name": var, "type": vartype, "value": varval, "is_temp": True, "is_external": True, "section": None, "offset": varval})



	# step 0: handle IF statements
	if_condition = True

	temp_lines = LINES

	LINES = []

	for l in temp_lines:
		LINE = l.get_parsed()

		if LINE != []:

			if LINE[0]["type"] == util.DATA_TYPES.CONDITIONAL_IF:
				condition = LINE[0]["condition"]

				try:
					if_condition = int(condition)
				except:
					# not a bool
					if not condition in ext_vars:
						if_condition = False
					else:
						if_condition = ext_vars[condition]

			elif LINE[0]["type"] == util.DATA_TYPES.CONDITIONAL_ENDIF:
				if_condition = True

			else:
				if if_condition:
					LINES.append(l)

			if if_condition == 0:
				if_condition = False
			elif if_condition == 1:
				if_condition = True





	# step 1: include files

	while True:
		lnum = len(LINES)-1
		while lnum >= 0:
			LINE_OBJ = LINES[lnum]

			LINE = LINE_OBJ.get_parsed()

			break_out = False
			
			cind = 0
			while cind < len(LINE):
				chunk = LINE[cind]

				# if the current chunk is an include
				if chunk["type"] == util.DATA_TYPES.INCLUDE:
					if not LINE_OBJ.already_included():
						# if not already undergone the include process

						file = chunk["filename"]  # include file
						path = LINE_OBJ.get_file_path() # file path relative to source file


						#extension = file.split(".")[-1] # file extension


						file_lines = read_file(path + file)  # code file

						ind = 0
						for line in file_lines:
							LINES.insert(lnum + ind, LineObject.Line(line, file=path+file, line_number=ind+1, include_level=LINE_OBJ.get_include_level() + 1))  # insert included file lines
							ind += 1


						#LINES.pop(lnum)
						LINE_OBJ.set_already_included() # so include doesnt happen again

						break_out = True
						break

				cind += 1

			if break_out: # to roll back to top of file when include statement finished (in case of nested includes)
				break

			lnum -= 1

		if lnum < 0:
			break



	# step 2: combine expressions into a single piece, and label external variables as such
	for LINE_OBJ in LINES:

		LINE = LINE_OBJ.get_parsed()


		cind = 0
		while cind < len(LINE):
			chunk = LINE[cind]

			if chunk["type"] == util.DATA_TYPES.GLOBAL:
				if not (chunk["varname"] in globalvars):
					globalvars.append(chunk["varname"])

				vind = 0
				while vind < len(localvars):
					var = localvars[vind]
					
					if var["name"] == chunk["varname"]:
						localvars = localvars[:vind] + localvars[vind+1:]
						vind -= 1

					vind += 1

				if chunk["varname"] in externalvars:
					externalvars.remove(chunk["varname"])

			elif chunk["type"] == util.DATA_TYPES.EXTERNAL:
				#print(chunk["varname"])
				if not (chunk["varname"] in externalvars):
					externalvars.append(chunk["varname"])
				if not (chunk["varname"] in globalvars):
					globalvars.append(chunk["varname"])

			cind += 1
	


	# expression combine
	for LINE_OBJ in LINES:

		LINE = LINE_OBJ.get_parsed()


		cind = 0
		while cind < len(LINE):
			chunk = LINE[cind]

			if chunk["type"] == util.DATA_TYPES.OPERATOR:
				ind = 0
				ended = False
				prev_was_operator = True
				while (not ended) and (cind + ind < len(LINE)):

					if LINE[cind+ind]["type"] == util.DATA_TYPES.OPERATOR:
						prev_was_operator = True
					else:
						if not prev_was_operator:
							ended = True
							break
						prev_was_operator = False

					ind += 1



				# turn into an expression string
				prev_off = 1
				'''
				if LINE[cind-1]["type"] == util.DATA_TYPES.EQU:
					prev_off = 0
				if LINE[cind-1]["type"] == util.DATA_TYPES.TYPE:
					prev_off = 0
				'''

				if LINE[cind]["operator"] == "(":
					prev_off = 0

				expression_data = LINE[cind-prev_off:cind+ind]
				line_data = [LINE[:cind-prev_off], LINE[cind+ind:]]

				expression = ""
				expression_vars = [] # keep track of variables used


				# pre-check to make sure external labels dont get parsed incorrectly
				if expression_data[0]["type"] == util.DATA_TYPES.VARIABLE:
					# external label expression MUST start with external label
					var_name = expression_data[0]["varname"]
					
					if var_name in externalvars:
						# must be an imported symbol

	
						if expression_data[1]["type"] == util.DATA_TYPES.OPERATOR and expression_data[1]["operator"] == "+":
							line_data.insert(1, {"type": util.DATA_TYPES.VARIABLE, "varname": var_name, "label": var_name, "is_external_label": True, "external_offset": 0})

							expression_data = expression_data[2:] # skip over addition symbol 
						else:
							raise LineException(LINE_OBJ.get_line_num(), "External label offsets can only be expressed as positive offsets from that label.\n" + LINE_OBJ.get_raw(), LINE_OBJ.get_file_name())





				for e in expression_data:
					expression += " "

					if e["type"] == util.DATA_TYPES.VARIABLE:
						expression += str(e["varname"])
						expression_vars.append(e["varname"])

					elif e["type"] == util.DATA_TYPES.LABEL:
						expression += str(e["varname"])
						expression_vars.append(e["varname"])

					elif e["type"] == util.DATA_TYPES.VALUE:
						expression += str(e["value"])

					elif e["type"] == util.DATA_TYPES.OPERATOR:
						expression += str(e["operator"])

				line_data.insert(len(line_data) - 1, {"type": util.DATA_TYPES.EXPRESSION, "expression": expression, "expression_vars": expression_vars})

				line_data = util.flatten_list(line_data)

				LINE = line_data
				LINE_OBJ.set_parsed(line_data)

			cind += 1









	# step 3: set EQU values, labels, and processor offsets


	section = "P" + FILE_NAME.split(".")[0]
	data_bank = 0
	data_page = 0

	mem = 16
	idx = 16


	ORGANIZATION_TAGS = ["sect", "org", "rel"]


	groups = ["", "PROG", "DATA"]

	section_offsets = {
		"P" + FILE_NAME.split(".")[0]: 0,
		"D" + FILE_NAME.split(".")[0]: 0}

	sections = [
		{"secname": None, "group": None, "code_data": [], "type": None, "offset": None, "size": 0}, 
		{"secname": "P" + FILE_NAME.split(".")[0], "group": "PROG", "code_data": [], "type": util.DATA_TYPES.SECTION, "offset": None, "size": 0}
		]
	processor_flags = []
	sec_ind = 1
	sec_len = 0
	org_ind = 1
	for LINE_OBJ in LINES:

		LINE = LINE_OBJ.get_parsed()

		cind = 0

		
		

		while cind < len(LINE):
			chunk = LINE[cind]



			# refine section data

			if chunk["type"] in (util.DATA_TYPES.SECTION, util.DATA_TYPES.ORG): # add others later
				#sec_ind += 1 

				section = LINE[cind-1]["varname"]

				if chunk["type"] == util.DATA_TYPES.ORG:
					section = "A" + str(org_ind) + section
					org_ind += 1

				if not section in section_offsets:
					section_offsets[section] = 0

				sections[-1]["size"] = sec_len

				sec_len = 0

				if chunk["type"] == util.DATA_TYPES.SECTION:
					# section
					group = section
					if section.lower() == "comn":
						group = "PROG"
					sections.append({"secname": section, "group": group, "code_data": [], "type": util.DATA_TYPES.SECTION, "offset": None, "size": 0})

				elif chunk["type"] == util.DATA_TYPES.ORG:
					# org
					sections.append({"secname": section, "group": section, "code_data": [], "type": util.DATA_TYPES.ORG, "offset": chunk["offset"], "size": 0})

				if chunk["type"] == util.DATA_TYPES.SECTION:
					sect_class = chunk["SECTION_CLASS"]

					if not (sect_class in ORGANIZATION_TAGS):
						ORGANIZATION_TAGS.append(sect_class)
					
					if not (section in ORGANIZATION_TAGS):
						ORGANIZATION_TAGS.append(section)

				sec_ind += 1 


			elif chunk["type"] == util.DATA_TYPES.GROUP:

				group = LINE[cind-1]["varname"]

				if not group in groups:
					groups.append(group)

				secname = chunk["SECTION_GROUP"]

				if not (section in ORGANIZATION_TAGS):
					ORGANIZATION_TAGS.append(secname)


				for i in range(len(sections)):

					if sections[i]["secname"] == secname:
						sections[i]["group"] = group




			elif chunk["type"] == util.DATA_TYPES.EXPRESSION:

				# temporary variable to be evaluated later. its easier this way
				varname = TEMP_LEFT + "TEMPVAR" + str(tempvar) + TEMP_RIGHT
				localvars.append({"name": varname, "value": "( " + chunk["expression"] + " )", "offset": None, "section": getsecind(sec_ind), "type": util.DATA_TYPES.EXPRESSION, "expression": chunk["expression"], "expression_vars": chunk["expression_vars"], "is_temp": True})
				
				LINE[cind] = {"type": util.DATA_TYPES.VARIABLE, "varname": varname, "label": varname, "size": 0}

				
				if LINE[cind-1]["type"] != util.DATA_TYPES.TYPE and LINE[cind-1]["type"] != util.DATA_TYPES.EQU:
					#LINE.insert(cind-1, {"type": util.DATA_TYPES.TYPE, "valtype": "addr", "size": 2})
					LINE[cind]["size"] = 2

					#cind += 1

				tempvar += 1



			elif chunk["type"] == util.DATA_TYPES.EQU:

				variable_name = chunk["varname"]


				if LINE[cind+1]["type"] == util.DATA_TYPES.VALUE:
					value = LINE[cind+1]["value"]

					localvars.append({"name": variable_name, "value": value, "offset": None, "section": getsecind(sec_ind), "type": "exact"})

				elif LINE[cind+1]["type"] == util.DATA_TYPES.EXPRESSION:

					varname = TEMP_LEFT + "TEMPVAR" + str(tempvar) + TEMP_RIGHT
					localvars.append({"name": varname, "value": "( " + LINE[cind+1]["expression"] + " )", "offset": None, "section": getsecind(sec_ind), "type": util.DATA_TYPES.EXPRESSION, "expression": LINE[cind+1]["expression"], "expression_vars": LINE[cind+1]["expression_vars"], "is_temp": True})
					
					LINE[cind+1] = {"type": util.DATA_TYPES.VARIABLE, "varname": varname, "label": varname, "size": 0}

					localvars.append({"name": variable_name, "value": varname, "label": varname, "type": util.DATA_TYPES.EXPRESSION, "offset": None, "section": getsecind(sec_ind), "expression": varname, "expression_vars": [varname]})

					tempvar += 1

				elif LINE[cind+1]["type"] == util.DATA_TYPES.VARIABLE:
					try:
						if not (LINE[cind+1]["varname"] in ORGANIZATION_TAGS):

							localvars.append({"name": variable_name, "value": "( " + LINE[cind+1]["varname"] + " )", "offset": None, "section": getsecind(sec_ind), "type": util.DATA_TYPES.EXPRESSION, "expression": LINE[cind+1]["varname"], "expression_vars": [LINE[cind+1]["varname"]]})
					except:
						pass


				#localvars.append({"name": variable_name, "value": "( " + LINE[cind+1]["varname"] + " )", "offset": None, "section": None, "type": util.DATA_TYPES.EXPRESSION, "is_temp": True, "is_external": True})

			elif chunk["type"] == util.DATA_TYPES.OPCODE:

				if chunk["opcode"].lower() == "jmp":
					if LINE[cind+1]["type"] in (util.DATA_TYPES.INDIRECT_START, util.DATA_TYPES.INDIRECT_LONG_START):

						if LINE[cind+2]["type"] != util.DATA_TYPES.TYPE:
							LINE[cind+2]["size"] = 2


				elif chunk["opcode"].lower() in ("adc", "and", "cmp", "eor", "lda", "ora", "sbc", "sta"):
					try:
						if LINE[cind+1]["type"] == util.DATA_TYPES.INDIRECT_LONG_START:
							if LINE[cind+3]["type"] == util.DATA_TYPES.INDIRECT_LONG_END:
								LINE[cind+2]["size"] = 1
					except:
						pass


			elif chunk["type"] == util.DATA_TYPES.VARIABLE:   # FOR DEBUGGING
				if "is_external_label" in chunk:
					if chunk["is_external_label"]:
						#print(str(LINE))
						pass

					


			cind += 1


		if LINE != []:
			if LINE[0]["type"] in (util.DATA_TYPES.LABEL, util.DATA_TYPES.OPCODE, util.DATA_TYPES.DBYTE, util.DATA_TYPES.DWORD, util.DATA_TYPES.DLONG, util.DATA_TYPES.DATA_BANK, util.DATA_TYPES.DATA_PAGE): 
				# code line

				LINE_OBJ.set_is_code()

				if LINE[0]["type"] in (util.DATA_TYPES.DATA_BANK, util.DATA_TYPES.DATA_PAGE):
					LINE_OBJ.set_is_not_code()

				LINE_OBJ.set_parsed(LINE)
				LINE_OBJ.set_offset(section_offsets[section])
				sections[-1]["code_data"].append(LINE_OBJ)

				if LINE[0]["type"] == util.DATA_TYPES.LABEL:
					is_label = True
					if len(LINE) > 1:
						if LINE[1]["type"] in (util.DATA_TYPES.SECTION, util.DATA_TYPES.GROUP, util.DATA_TYPES.ORG):
							is_label = False
					if is_label:
						localvars.append({"name": LINE[0]["label"], "value": None, "offset": section_offsets[section], "section": getsecind(sec_ind), "type": "label", "is_external": False})


				# format data in tables as correct size
				for IND in range(len(LINE)):
					if LINE[IND]["type"] in (util.DATA_TYPES.DBYTE, util.DATA_TYPES.DWORD, util.DATA_TYPES.DLONG):

						for cind in range(IND + 1, len(LINE)):

							if LINE[cind]["type"] in (util.DATA_TYPES.VALUE, util.DATA_TYPES.EXPRESSION, util.DATA_TYPES.VARIABLE):
								if LINE[IND]["type"] == util.DATA_TYPES.DBYTE:
									LINE[cind]["size"] = 1
								elif LINE[IND]["type"] == util.DATA_TYPES.DWORD:
									LINE[cind]["size"] = 2
								elif LINE[IND]["type"] == util.DATA_TYPES.DLONG:
									LINE[cind]["size"] = 3

							elif not (LINE[cind]["type"] in (util.DATA_TYPES.SEPARATOR)):
								raise LineException(LINE_OBJ.get_line_num(), "invalid data in data table", LINE_OBJ.get_file_name())





				for cind in range(len(LINE)):
					chunk = LINE[cind]
					if chunk["size"] != None:
						if chunk["type"] == util.DATA_TYPES.VARIABLE:
							if chunk["varname"].lower() in ORGANIZATION_TAGS:	# change to "if not in rel group names"
								LINE[cind]["size"] = 0
								chunk = LINE[cind]

							if "is_external_label" in chunk and chunk["is_external_label"]:
								if cind+1 < len(LINE):
									if LINE[cind+1]["type"] == util.DATA_TYPES.VARIABLE:
										LINE[cind+1]["size"] = 0


						
						section_offsets[section] += chunk["size"]
						sec_len += chunk["size"]

					else:
						# base off of processor size

						if LINE[cind-1]["reg"].lower() == "a":
							section_offsets[section] += mem//8
							LINE[cind]["size"] = mem//8
							sec_len += mem//8
						elif LINE[cind-1]["reg"].lower() in "xy":
							section_offsets[section] += idx//8
							LINE[cind]["size"] = idx//8
							sec_len += idx//8
						elif LINE[cind-1]["reg"].lower() == "p":
							section_offsets[section] += 1
							LINE[cind]["size"] = 1
							sec_len += 1
						elif LINE[cind-1]["reg"].lower() == "s":
							section_offsets[section] += 2
							LINE[cind]["size"] = 2
							sec_len += 2


			elif LINE[0]["type"] == util.DATA_TYPES.PFLAG:
				# processor flag

				if LINE[0]["flag"].lower() == "mem8":
					mem = 8
				elif LINE[0]["flag"].lower() == "mem16":
					mem = 16
				elif LINE[0]["flag"].lower() == "idx8":
					idx = 8
				elif LINE[0]["flag"].lower() == "idx16":
					idx = 16

				processor_flags.append({"type": LINE[0]["flag"].lower(), "offset": section_offsets[section], "section": getsecind(sec_ind)})

			elif LINE[0]["type"] == util.DATA_TYPES.DATA_BANK:
				pass

			elif LINE[0]["type"] == util.DATA_TYPES.DATA_PAGE:
				pass







		LINE_OBJ.set_parsed(LINE)
		# TO DO: data bank + page fixing


	sections[-1]["size"] = sec_len



	sections.insert(2, {"secname": "D" + FILE_NAME.split(".")[0], "group": "DATA", "code_data": [], "type": util.DATA_TYPES.SECTION, "offset": None, "size": 0})



	#for s in sections:
	#	print(s["secname"])



	###############################################################################################

	###############################################################################################



	# step 4: expression evaluation for variables


	# ensure that all external vars are handled as such
	for vind in range(len(localvars)):
		var = localvars[vind]

		if not "is_external" in localvars[vind]:
			localvars[vind]["is_external"] = False

		for var2 in externalvars:
			if var["name"] == var2:
				localvars[vind]["is_external"] = True
				break








	

	# evaluate expressions in variables
	num_exact = 0
	p_num_exact = -1

	while num_exact != p_num_exact:

		p_num_exact = num_exact

		num_exact = 0


		for vind in range(1, len(localvars)):
			var = localvars[vind]

			try:
				if var["type"] != util.DATA_TYPES.EXPRESSION:

					if not ("is_temp" in var):
						localvars[vind]["is_temp"] = False

					num_exact += 1
					name = var["name"]

					if var["type"] == "exact":
						val = var["value"]
					elif var["type"] == "label":
						val = var["offset"]
					



					for ind in range(1, len(localvars)):
						var2 = localvars[ind]

						if var2["type"] == util.DATA_TYPES.EXPRESSION:

							if not ("is_temp" in var2):
								localvars[ind]["is_temp"] = False
								var2["is_temp"] = False



							if name in var2["expression_vars"]:

								var2["expression_vars"].remove(name)
								var2["expression"] = var2["expression"].replace(name, str(val))

								localvars[ind]["expression_vars"] = var2["expression_vars"]
								localvars[ind]["expression"] = var2["expression"]


							if len(localvars[ind]["expression_vars"]) == 0:
								try:
									VAR_TYPE = "exact"
									if var["type"] == "label":
										VAR_TYPE = "label"

									VAL = util.evaluateExpression(localvars[ind]["expression"])
									localvars[ind] = {"name": localvars[ind]["name"], "value": VAL, "offset": VAL, "section": localvars[ind]["section"], "type": VAR_TYPE, "is_temp": localvars[ind]["is_temp"], "is_external": localvars[ind]["is_external"]}

									num_exact += 1
								except Exception as e:
									raise Exception("Error during parsing of " + localvars[ind]["name"] + " : " + localvars[ind]["expression"] + ", \n" + str(e))
			except Exception as e:
				raise Exception("Error when using " + localvars[vind]["name"] + "  " + str(localvars[vind]) + " as parsing variable: \n" + str(e))


					



	# check to see if all expressions evaluated
	for var in localvars[1:]:
		if var["type"] in ("expression"):
			raise Exception("Variable " + var["name"] + " is not evaluateable.   " + var["expression"] + "   vars: " + ", ".join(var["expression_vars"]))

		
		if var["type"] == "exact":
			#print(var["name"], var["value"])
			pass
		elif var["type"] == "label":
			#print(var["name"], var["offset"])
			pass


	# ensure that "is_external" is set for all variables
	for vind in range(len(localvars)):
		var = localvars[vind]
		if not "is_external" in localvars[vind]:
			localvars[vind]["is_external"] = False

		for var2 in externalvars:
			if var["name"] == var2:
				localvars[vind]["is_external"] = True






	###############################################################################################

	###############################################################################################




	# step 5: gather all "near" variables, and convert branch instructions to near labels
	for ind in range(1, len(localvars)):
		var = localvars[ind]

		if var["name"][-1] == "$":
			# if "near" variable

			localvars[ind]["is_temp"] = True

		if not var["is_external"]:
			if var["type"] == "label":
				sec_ind = var["section"]

				section = sections[sec_ind]["secname"]
				off = 0

				for s in range(1, sec_ind):
					if sections[s]["secname"] == section:
						off += sections[s]["size"]


				localvars[ind] = {"name": var["name"], "type": "label", "value": None, "offset": off + var["offset"], "section": section, "is_temp": var["is_temp"], "is_external": False}



	#for v in localvars:
	#	print(str(v))


	# convert variables in code into variable values
	for sec_ind in range(1, len(sections)):

		sec = sections[sec_ind]

		lnum = 0
		for LINE_OBJ in sec["code_data"]:

			LINE = LINE_OBJ.get_parsed()


			for ind in range(len(LINE)):
				chunk = LINE[ind]

				if chunk["type"] == util.DATA_TYPES.VARIABLE and ((not ("is_external_label" in chunk)) or chunk["is_external_label"] == False):

					if not ("vartype" in chunk):
						chunk["vartype"] = util.DATA_TYPES.NORMALVAR

					if chunk["vartype"] != util.DATA_TYPES.NEARVAR:
						# if actual label, and not near label

						if ind != 0:
							fnd = False
							v = None
							#print("\n\n\n")
							for var in localvars[1:]:
								#print(var["name"])
								if var["name"] == chunk["varname"]:
									if not fnd:
										fnd = True

										v = var

									else:
										raise LineException(LINE_OBJ.get_line_num(), "Multiple instances of variable \"" + str(chunk["varname"]) + "\"", LINE_OBJ.get_file_name())

							if not fnd:
								for var in externalvars:
									if var == chunk["varname"]:
										fnd = True

								if not fnd:
									raise LineException(LINE_OBJ.get_line_num(), "Could not find variable \"" + str(chunk["varname"]) + "\"", LINE_OBJ.get_file_name())

								LINE[ind] = {"type": util.DATA_TYPES.EXTERNAL, "varname": chunk["varname"], "label": chunk["varname"]}
							else:
								try:
									if v["is_external"]:
										LINE[ind] = {"type": util.DATA_TYPES.EXTERNAL, "varname": chunk["varname"], "label": chunk["varname"]}
									else:

										if v["type"] == "exact":
											if not v["name"].lower() in ORGANIZATION_TAGS:	# change to "if not in rel group names"
												LINE[ind] = {"type": util.DATA_TYPES.VALUE, "value": v["value"]}



										elif v["type"] == "label":
											LINE[ind] = {"type": util.DATA_TYPES.VARIABLE, "varname": v["name"], "label": v["name"], "section": v["section"], "offset": v["offset"]}
								except Exception as e:
									print(v)
									raise e

							if LINE[ind-1]["type"] != util.DATA_TYPES.TYPE:
								LINE[ind]["size"] = 2



					else:
						# if near label

						if ind != 0:

							if LINE[ind-1]["type"] == util.DATA_TYPES.OPCODE and LINE[ind-1]["opcode"] in ("bcc", "blt", "bcs", "bge", "beq", "bmi", "bne", "bpl", "bra", "bvc", "bvs", "brl", "per"):
								if chunk["size"] == 1:
									# regular branch
									closest = 0x81
									
									for var in localvars[1:]:
										if var["name"] == chunk["varname"]:

											if var["section"] == sections[sec_ind]["secname"]:

												dist = var["offset"] - (LINE_OBJ.get_offset() + 2)

												if abs(dist) < abs(closest):
													closest = dist

									if closest > 0x7f or closest < -0x80:
										raise LineException(LINE_OBJ.get_line_num(), "No label \"" + str(chunk["varname"]) + "\" near enough for branch instruction.  " + str(LINE_OBJ.get_offset()), LINE_OBJ.get_file_name())

									LINE[ind] = {"type": util.DATA_TYPES.VALUE, "value": closest, "size": 1}

								elif chunk["size"] == 2:
									# brl and per
									closest = 0x8001

									for var in localvars[1:]:
										if var["name"] == chunk["varname"]:

											if var["section"] == sections[sec_ind]["secname"]:

												dist = var["offset"] - (LINE_OBJ.get_offset() + 3)

												if abs(dist) < abs(closest):
													closest = dist

									if closest > 0x7fff or closest < -0x8000:
										raise LineException(LINE_OBJ.get_line_num(), "No label \"" + str(chunk["varname"]) + "\" near enough for branch instruction", LINE_OBJ.get_file_name())

									LINE[ind] = {"type": util.DATA_TYPES.VALUE, "value": closest, "size": 2}

							else:
								fnd = False
								v = None
								for vind in range(1, len(localvars)):
									var = localvars[vind]
									if var["name"] == chunk["varname"]:
										v = var
										fnd = True
										break



								if not fnd:
									for var in externalvars:
										if var == chunk["varname"]:
											fnd = True

									if not fnd:
										raise LineException(LINE_OBJ.get_line_num(), "Could not find variable \"" + str(chunk["varname"]) + "\"", LINE_OBJ.get_file_name())

									LINE[ind] = {"type": util.DATA_TYPES.EXTERNAL, "varname": chunk["varname"], "label": chunk["varname"]}
								else:
									try:
										if v["is_external"]:
											LINE[ind] = {"type": util.DATA_TYPES.EXTERNAL, "varname": chunk["varname"], "label": chunk["varname"]}
										else:

											if v["type"] == "exact":
												if not v["name"].lower() in ORGANIZATION_TAGS:	# change to "if not in rel group names"
													LINE[ind] = {"type": util.DATA_TYPES.VALUE, "value": v["value"]}


											elif v["type"] == "label":
												LINE[ind] = {"type": util.DATA_TYPES.VARIABLE, "varname": v["name"], "label": v["name"], "section": v["section"], "offset": v["offset"]}
									
									except Exception as e:
										print(v)
										raise e

								if LINE[ind-1]["type"] != util.DATA_TYPES.TYPE:
									LINE[ind]["size"] = 2










			sections[sec_ind]["code_data"][lnum].set_parsed(LINE)

			lnum += 1



	# set external variables to have correct tags, external labels have correct offset
	for sec_ind in range(1, len(sections)):

		sec = sections[sec_ind]

		lnum = 0
		for LINE_OBJ in sec["code_data"]:

			LINE = LINE_OBJ.get_parsed()

			ind = 0
			while ind < len(LINE):

				if LINE[ind]["type"] == util.DATA_TYPES.VARIABLE:

					if not "external_offset" in LINE[ind]:
						LINE[ind]["external_offset"] = 0


					if ("is_external_label" in LINE[ind]) and LINE[ind]["is_external_label"]:

						if not "external_offset" in LINE[ind]:
							LINE[ind]["external_offset"] = 0


						if ind+1 < len(LINE):

							if LINE[ind+1]["type"] == util.DATA_TYPES.VALUE:
								LINE[ind]["external_offset"] = LINE[ind+1]["value"]
								LINE[ind]["type"] = util.DATA_TYPES.EXTERNAL

								# parse rest of line
								LINE = LINE[:ind+1] + LINE[ind+2:]

							else:

								raise LineException(LINE_OBJ.get_line_num(), "Error parsing external label offset...:\n" + LINE_OBJ.get_raw(), LINE_OBJ.get_file_name())



				ind += 1


			LINE_OBJ.set_parsed(LINE)




	# parse branch nearlabel labels as such
	for sec in sections[1:]:

		lnum = 0
		for LINE_OBJ in sec["code_data"]:

			LINE = LINE_OBJ.get_parsed()


			for ind in range(len(LINE)):
				chunk = LINE[ind]

				if chunk["type"] == util.DATA_TYPES.OPCODE:
					op = chunk["opcode"].lower()

					if op in ("bcc", "blt", "bcs", "bge", "beq", "bmi", "bne", "bpl", "bra", "bvc", "bvs", "brl", "per"):
						if LINE[ind+1]["type"] == util.DATA_TYPES.VARIABLE:

							fnd = False
							v = None
							for var in localvars[1:]:
								if var["name"] == LINE[ind+1]["varname"]:
									fnd = True
									v = var

							if v["type"] == "label":
								LINE[ind+1] = {"type": util.DATA_TYPES.VALUE, "value": var["offset"] - (LINE_OBJ.get_offset() + 2), "size": 1}

								if op in ("brl", "per"):
									LINE[ind+1]["size"] = 2

			LINE_OBJ.set_parsed(LINE)





	# convert data types into a parseable format

	sec_ind = 1
	for sec in sections[1:]:


		for LINE_OBJ in sec["code_data"]:
			LINE = LINE_OBJ.get_parsed()


			ind = 0
			while ind < len(LINE):
				if LINE[ind]["type"] == util.DATA_TYPES.TYPE:
					LINE[ind]["value"] = LINE[ind+1]

					LINE = LINE[:ind+1] + LINE[ind+2:]

				ind += 1

			LINE_OBJ.set_parsed(LINE)


	sec_ind = 1
	for sec in sections[1:]:


		for LINE_OBJ in sec["code_data"]:
			LINE = LINE_OBJ.get_parsed()


			ind = 0
			while ind < len(LINE):
				if LINE[ind]["type"] == util.DATA_TYPES.VALUE:

					if LINE[ind-1]["type"] == util.DATA_TYPES.INDIRECT_LONG_START:
						if ind+1 < len(LINE):
							if LINE[ind+1]["type"] == util.DATA_TYPES.INDIRECT_LONG_END:
								if ind-2 >= 0:
									if LINE[ind-2]["type"] == util.DATA_TYPES.OPCODE:
										if LINE[ind-2]["opcode"] in ("jmp", "jml"):
											LINE[ind]["size"] = 2
										else:
											LINE[ind]["size"] = 1

					
					valtype = "const"

					if LINE[ind]["size"] == 1:
						valtype = "dp"
					elif LINE[ind]["size"] == 2:
						valtype = "addr"
					elif LINE[ind]["size"] == 3:
						valtype = "long"

					LINE[ind] = {"type": util.DATA_TYPES.TYPE, "valtype": valtype, "size": LINE[ind]["size"], "value": LINE[ind]}

				elif LINE[ind]["type"] == util.DATA_TYPES.VARIABLE:

					if not LINE[ind]["varname"].lower() in ORGANIZATION_TAGS:	# change to "if not in rel group names"

						if LINE[ind]["offset"] != None:

							ctype = "const"
							if LINE[ind]["size"] == 1:
								ctype = "dp"
							elif LINE[ind]["size"] == 2:
								ctype = "addr"
							elif LINE[ind]["size"] == 3:
								ctype = "long"


							LINE[ind] = {"type": util.DATA_TYPES.TYPE, "valtype": ctype, "size": LINE[ind]["size"], "value": LINE[ind]}

						else:
							LINE[ind] = {"type": util.DATA_TYPES.TYPE, "valtype": "const", "size": LINE[ind]["size"], "value": LINE[ind]}	

				elif LINE[ind]["type"] == util.DATA_TYPES.EXTERNAL:
					LINE[ind] = {"type": util.DATA_TYPES.TYPE, "valtype": "addr", "size": 2, "value": LINE[ind]}


				ind += 1

			LINE_OBJ.set_parsed(LINE)




	###############################################################################################

	###############################################################################################


	# convert opcode mnemonics into opcodes, and values into correct hex 


	sec_ind = 1
	for sec in sections[1:]:


		for LINE_OBJ in sec["code_data"]:
			LINE = LINE_OBJ.get_parsed()


			ind = 0
			while ind < len(LINE):

				if LINE[ind]["type"] == util.DATA_TYPES.OPCODE:
					# convert each individual opcode based on the most matched type


					op = LINE[ind]["opcode"].lower()

					


					if op == "adc":
						# 

						formats = [
							("( dp , x )",     0x61),
							("sr , S",         0x63),
							("dp",             0x65),
							("[ dp ]",         0x67),
							("#const",         0x69),
							("addr",           0x6d),
							("long",           0x6f),
							("( dp ) , y",     0x71),
							("( dp )",         0x72),
							("( sr , S ) , y", 0x73),
							("dp , x",         0x75),
							("[ dp ] , y",     0x77),
							("addr , y",       0x79),
							("addr , x",       0x7d),
							("long , x",       0x7f)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "and":
						# 
						formats = [
							("( dp , x )",     0x21),
							("sr , S",         0x23),
							("dp",             0x25),
							("[ dp ]",         0x27),
							("#const",         0x29),
							("addr",           0x2d),
							("long",           0x2f),
							("( dp ) , y",     0x31),
							("( dp )",         0x32),
							("( sr , S ) , y", 0x33),
							("dp , x",         0x35),
							("[ dp ] , y",     0x37),
							("addr , y",       0x39),
							("addr , x",       0x3d),
							("long , x",       0x3f)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "asl":
						# 
						formats = [
							("dp",             0x06),
							("a",              0x0a),
							("addr",           0x0e),
							("dp , x",         0x16),
							("addr , x",       0x1e)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "bcc":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x90], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "blt":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x90], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bcs":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xb0], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bge":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xb0], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "beq":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xf0], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bit":
						# 
						formats = [
							("dp",             0x24),
							("addr",           0x2c),
							("dp , x",         0x34),
							("addr , x",       0x3c),
							("#const",         0x89)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "bmi":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x30], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bne":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xd0], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bpl":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x10], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bra":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x80], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "brk":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x00], "size": 1}
						if ind+1 <= len(LINE):
							LINE.append({"type": util.DATA_TYPES.TYPE, "valtype": "const", "size": 1, "value": {"type": util.DATA_TYPES.VALUE, "value": 0, "size": 1}}) 
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "brl":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x82], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 2

					elif op == "bvc":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x50], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "bvs":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x70], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "clc":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x18], "size": 1}

					elif op == "cld":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xd8], "size": 1}

					elif op == "cli":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x58], "size": 1}

					elif op == "clv":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xb8], "size": 1}

					elif op == "cmp":
						# 
						formats = [
							("( dp , x )",     0xc1),
							("sr , S",         0xc3),
							("dp",             0xc5),
							("[ dp ]",         0xc7),
							("#const",         0xc9),
							("addr",           0xcd),
							("long",           0xcf),
							("( dp ) , y",     0xd1),
							("( dp )",         0xd2),
							("( sr , S ) , y", 0xd3),
							("dp , x",         0xd5),
							("[ dp ] , y",     0xd7),
							("addr , y",       0xd9),
							("addr , x",       0xdd),
							("long , x",       0xdf)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "cop":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x02], "size": 1}
						if ind+1 > len(LINE):
							LINE.append({"type": util.DATA_TYPES.TYPE, "valtype": "const", "size": 1, "value": {"type": util.DATA_TYPES.VALUE, "value": 0, "size": 1}}) 
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "cpx":
						# 
						formats = [
							("#const",         0xe0),
							("dp",             0xe4),
							("addr",           0xec)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "cpy":
						# 
						formats = [
							("#const",         0xc0),
							("dp",             0xc4),
							("addr",           0xcc)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "dea":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x3a], "size": 1}

					elif op == "dec":
						# 
						formats = [
							("a",              0x3a),
							("dp",             0xc6),
							("addr",           0xce),
							("dp , x",         0xd6),
							("addr , x",       0xde)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "dex":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xca], "size": 1}

					elif op == "dey":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x88], "size": 1}

					elif op == "eor":
						# 
						formats = [
							("( dp , x )",     0x41),
							("sr , S",         0x43),
							("dp",             0x45),
							("[ dp ]",         0x47),
							("#const",         0x49),
							("addr",           0x4d),
							("long",           0x4f),
							("( dp ) , y",     0x51),
							("( dp )",         0x52),
							("( sr , S ) , y", 0x53),
							("dp , x",         0x55),
							("[ dp ] , y",     0x57),
							("addr , y",       0x59),
							("addr , x",       0x5d),
							("long , x",       0x5f)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "ina":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x1a], "size": 1}

					elif op == "inc":
						#
						formats = [
							("a",              0x1a),
							("dp",             0xe6),
							("addr",           0xee),
							("dp , x",         0xf6),
							("addr , x",       0xfe)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "inx":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xe8], "size": 1}

					elif op == "iny":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xc8], "size": 1}

					elif op == "jmp":
						# 
						formats = [
							("addr",           0x4c),
							("long",           0x5c),
							("( addr )",       0x6c),
							("( addr , x )",   0x7c),
							("[ addr ]",       0xdc)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "jml":
						# 
						formats = [
							("long",           0x5c),
							("[ addr ]",       0xdc)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}
						LINE[ind+1]["size"] = 3

					elif op == "jsr":
						# 
						formats = [
							("addr",           0x20),
							("long",           0x22),
							("( addr , x )",   0xfc)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "jsl":
						# 
						formats = [
							("long",           0x22)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}
						LINE[ind+1]["size"] = 3

					elif op == "lda":
						# 
						formats = [
							("( dp , x )",     0xa1),
							("sr , S",         0xa3),
							("dp",             0xa5),
							("[ dp ]",         0xa7),
							("#const",         0xa9),
							("addr",           0xad),
							("long",           0xaf),
							("( dp ) , y",     0xb1),
							("( dp )",         0xb2),
							("( sr , S ) , y", 0xb3),
							("dp , x",         0xb5),
							("[ dp ] , y",     0xb7),
							("addr , y",       0xb9),
							("addr , x",       0xbd),
							("long , x",       0xbf)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "ldx":
						# 
						formats = [
							("#const",         0xa2),
							("dp",             0xa6),
							("addr",           0xae),
							("dp , y",         0xb6),
							("addr , y",       0xbe)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "ldy":
						# 
						formats = [
							("#const",         0xa0),
							("dp",             0xa4),
							("addr",           0xac),
							("dp , x",         0xb4),
							("addr , x",       0xbc)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "lsr":
						# 
						formats = [
							("dp",             0x46),
							("a",              0x4a),
							("addr",           0x4e),
							("dp , x",         0x56),
							("addr , x",       0x5e)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "mvn":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x54], "size": 1}

					elif op == "mvp":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x44], "size": 1}

					elif op == "nop":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xea], "size": 1}

					elif op == "ora":
						# 
						formats = [
							("( dp , x )",     0x01),
							("sr , S",         0x03),
							("dp",             0x05),
							("[ dp ]",         0x07),
							("#const",         0x09),
							("addr",           0x0d),
							("long",           0x0f),
							("( dp ) , y",     0x11),
							("( dp )",         0x12),
							("( sr , S ) , y", 0x13),
							("dp , x",         0x15),
							("[ dp ] , y",     0x17),
							("addr , y",       0x19),
							("addr , x",       0x1d),
							("long , x",       0x1f)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "pea":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xf4], "size": 1}

					elif op == "pei":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xd4], "size": 1}

					elif op == "per":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x62], "size": 1}
						LINE[ind+1]["size"] = 2

					elif op == "pha":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x48], "size": 1}

					elif op == "phb":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x8b], "size": 1}

					elif op == "phd":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x0b], "size": 1}

					elif op == "phk":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x4b], "size": 1}

					elif op == "php":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x08], "size": 1}

					elif op == "phx":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xda], "size": 1}

					elif op == "phy":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x5a], "size": 1}

					elif op == "pla":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x68], "size": 1}

					elif op == "plb":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xab], "size": 1}

					elif op == "pld":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x2b], "size": 1}

					elif op == "plp":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x28], "size": 1}

					elif op == "plx":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xfa], "size": 1}

					elif op == "ply":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x7a], "size": 1}

					elif op == "rep":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xc2], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "rol":
						# 
						formats = [
							("dp",             0x26),
							("a",              0x2a),
							("dp , x",         0x36),
							("addr , x",       0x3e)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "ror":
						# 
						formats = [
							("dp",             0x66),
							("a",              0x6a),
							("dp , x",         0x76),
							("addr , x",       0x7e)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "rti":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x40], "size": 1}

					elif op == "rtl":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x6b], "size": 1}

					elif op == "rts":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x60], "size": 1}

					elif op == "sbc":
						# 
						formats = [
							("( dp , x )",     0xe1),
							("sr , S",         0xe3),
							("dp",             0xe5),
							("[ dp ]",         0xe7),
							("#const",         0xe9),
							("addr",           0xed),
							("long",           0xef),
							("( dp ) , y",     0xf1),
							("( dp )",         0xf2),
							("( sr , S ) , y", 0xf3),
							("dp , x",         0xf5),
							("[ dp ] , y",     0xf7),
							("addr , y",       0xf9),
							("addr , x",       0xfd),
							("long , x",       0xff)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "sec":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x38], "size": 1}

					elif op == "sed":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xf8], "size": 1}

					elif op == "sei":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x78], "size": 1}

					elif op == "sep":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xe2], "size": 1}
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "sta":
						# 
						formats = [
							("( dp , x )",     0x81),
							("sr , S",         0x83),
							("dp",             0x85),
							("[ dp ]",         0x87),
							("addr",           0x8d),
							("long",           0x8f),
							("( dp ) , y",     0x91),
							("( dp )",         0x92),
							("( sr , S ) , y", 0x93),
							("dp , x",         0x95),
							("[ dp ] , y",     0x97),
							("addr , y",       0x99),
							("addr , x",       0x9d),
							("long , x",       0x9f)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "stp":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xdb], "size": 1}

					elif op == "stx":
						# 
						formats = [
							("dp",             0x86),
							("addr",           0x8e),
							("dp , y",         0x96)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "sty":
						# 
						formats = [
							("dp",             0x84),
							("addr",           0x8c),
							("dp , y",         0x94)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "stz":
						# 
						formats = [
							("dp",             0x64),
							("dp , x",         0x74),
							("addr",           0x9c),
							("addr , x",       0x9e)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "tax":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xaa], "size": 1}

					elif op == "tay":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xa8], "size": 1}

					elif op == "tcd":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x5b], "size": 1}

					elif op == "tcs":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x1b], "size": 1}

					elif op == "tdc":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x7b], "size": 1}

					elif op == "trb":
						# 
						formats = [
							("dp",             0x14),
							("addr",           0x1c)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "tsb":
						# 
						formats = [
							("dp",             0x04),
							("addr",           0x0c)
							]

						opcode = parse_instruction(LINE[ind:], formats, op.upper(), LINE_OBJ)
						
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [opcode], "size": 1}

					elif op == "tsc":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x3b], "size": 1}

					elif op == "tsx":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xba], "size": 1}

					elif op == "txa":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x8a], "size": 1}

					elif op == "txs":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x9a], "size": 1}

					elif op == "txy":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x9b], "size": 1}

					elif op == "tya":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x98], "size": 1}

					elif op == "tyx":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xbb], "size": 1}

					elif op == "wai":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xcb], "size": 1}

					elif op == "wdm":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0x42], "size": 1}
						if ind+1 > len(LINE):
							LINE.append({"type": util.DATA_TYPES.TYPE, "valtype": "const", "size": 1, "value": {"type": util.DATA_TYPES.VALUE, "value": 0, "size": 1}}) 
						if ind+1 <= len(LINE):
							LINE[ind+1]["size"] = 1

					elif op == "xba":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xeb], "size": 1}

					elif op == "xce":
						# 
						LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": [0xfb], "size": 1}

					
				
				# do encoding of data bvtes??? nah
					
					
					

					

				ind += 1
			LINE_OBJ.set_parsed(LINE)




		sec_ind += 1


	# convert all hard data and variables back into respective types

	sec_ind = 1
	for sec in sections[1:]:


		for LINE_OBJ in sec["code_data"]:
			LINE = LINE_OBJ.get_parsed()


			ind = 0
			while ind < len(LINE):

				if LINE[ind]["type"] == util.DATA_TYPES.TYPE:
					valtype = LINE[ind]["valtype"]

					size = LINE[ind]["size"]
					LINE[ind] = LINE[ind]["value"]
					LINE[ind]["size"] = size

					if valtype == "bank":
						LINE[ind]["bank_type"] = "bank"
					elif valtype == "offset":
						LINE[ind]["bank_type"] = "offset"
					elif valtype == "high":
						LINE[ind]["bank_type"] = "high"
					elif valtype == "low":
						LINE[ind]["bank_type"] = "low"
					else:
						LINE[ind]["bank_type"] = "NONE"


				if LINE[ind]["type"] == util.DATA_TYPES.VALUE:

					data = []
					val = LINE[ind]["value"]

					if val < 0:
						val = val + 0x1000000

					for i in range(LINE[ind]["size"]):
						data.append(val % 256)
						val = val // 256

					LINE[ind] = {"type": util.DATA_TYPES.RAW_BYTES, "bytes": data, "size": len(data)} 

				ind += 1



			LINE_OBJ.set_parsed(LINE)

		sec_ind += 1


	#print(globalvars)





	###############################################################################################

	###############################################################################################



	# convert section code into bytes per line

	sec_ind = 1
	for sec in sections[1:]:


		for LINE_OBJ in sec["code_data"]:
			LINE = LINE_OBJ.get_parsed()

			LINE_BYTES = [0x57]


			# add line number
			LINE_NUM = LINE_OBJ.get_line_num()
			LINE_BYTES.append((LINE_NUM // 256) % 256)
			LINE_BYTES.append(LINE_NUM % 256)


			final_consecutive_bytes = []

			ind = 0
			while ind < len(LINE) + 1:
				end_consec = True

				if ind < len(LINE):
					chunk = LINE[ind]
					end_consec = True


					if chunk["type"] == util.DATA_TYPES.RAW_BYTES:
						end_consec = False
					elif chunk["type"] == util.DATA_TYPES.VARIABLE or chunk["type"] == util.DATA_TYPES.EXTERNAL:
						pass
					elif chunk["type"] == util.DATA_TYPES.STORAGE_DIRECTIVE:
						pass
					else:
						end_consec = False


				# patch in bytes BEFORE the next variable data
				if end_consec:

					size = len(final_consecutive_bytes)

					if size > 0:

						LINE_BYTES.append(0x11) # raw data 

						size_bytes = make_length_bytes(size)

						for b in size_bytes:
							LINE_BYTES.append(b)

						for b in final_consecutive_bytes:
							LINE_BYTES.append(b)

					final_consecutive_bytes = []



				if ind < len(LINE):


					if chunk["type"] == util.DATA_TYPES.RAW_BYTES:
						for b in chunk["bytes"]:
							final_consecutive_bytes.append(b)

						end_consec = False

					elif chunk["type"] == util.DATA_TYPES.VARIABLE or chunk["type"] == util.DATA_TYPES.EXTERNAL:
						# variable type

						if chunk["type"] == util.DATA_TYPES.VARIABLE and ind == 0:
							break

						if chunk["varname"].lower() in ORGANIZATION_TAGS:	# change to "if not in rel group names"
							break

						var_bytes = [0x12]

						size = chunk["size"]

						if size == 1:
							var_bytes.append(0x11) # byte

						elif size == 2:
							var_bytes.append(0x12) # word

						elif size == 3:
							var_bytes.append(0x13) # long

						if not "bank_type" in chunk:
							LINE[ind]["bank_type"] = "NONE"
							chunk = LINE[ind]

						var_type = 0

						# variable reference type
						if chunk["bank_type"] == "NONE":
							pass

						elif chunk["bank_type"] == "bank":
							# bank of variable
							var_type |= 0b01001000  # bank

						elif chunk["bank_type"] == "offset":
							# offset of variable
							var_type |= 0b01100000  # offset

						elif chunk["bank_type"] == "high":
							# high byte of variable
							var_type |= 0b01000000  # high

						elif chunk["bank_type"] == "low":
							# low byte of variable
							var_type |= 0b00111000  # low



						if chunk["type"] == util.DATA_TYPES.VARIABLE:
							var_type |= 0b00000001  # local variable

							var_bytes.append(var_type) # variable type

							v = chunk["varname"]

							INDEX = -1
							v_ind = 0
							for var in localvars:
								if var["name"] == v:
									INDEX = v_ind 
									break

								v_ind += 1

							if INDEX == -1:
								raise LineException(LINE_OBJ.get_line_num(), "Error converting variable: " + str(chunk), LINE_OBJ.get_file_name())


							VAR = localvars[INDEX]
							section = VAR["section"]

							s_ind = 0
							for sec in sections:
								if sec["secname"] == section:
									break
								s_ind += 1

							var_bytes.append((s_ind // 256) % 256)   # section number
							var_bytes.append(s_ind % 256)

							offset = VAR["offset"]
							offset_bytes = []
							for _ in range(4):
								offset_bytes.append(offset % 256)
								offset = offset // 256

							for b in reversed(offset_bytes):
								var_bytes.append(b)  # section offset



						elif chunk["type"] == util.DATA_TYPES.EXTERNAL:
							var_type |= 0b00000000  # external variable

							var_bytes.append(var_type) # variable type


							v = chunk["varname"]

							INDEX = -1
							v_ind = 0
							for var in globalvars:
								if var == v:
									INDEX = v_ind 
									break

								v_ind += 1

							if INDEX == -1:
								raise LineException(LINE_OBJ.get_line_num(), "Error converting variable: " + str(chunk), LINE_OBJ.get_file_name())

							var_bytes.append((INDEX // 256) % 256)  # variable offset
							var_bytes.append(INDEX % 256)

							label_offset = 0
							label_offset_bytes = []

							if "is_external_label" in chunk:
								label_offset = chunk["external_offset"]

							for i in range(4):
								label_offset_bytes.append(label_offset % 256)
								label_offset = label_offset // 256


							for b in reversed(label_offset_bytes):
								var_bytes.append(b)  # external label offset bytes


						for v in var_bytes:
							LINE_BYTES.append(v)

					elif chunk["type"] == util.DATA_TYPES.STORAGE_DIRECTIVE:
						# storage directive
						pass

					else:
						end_consec = False



				

				ind += 1

			LINE_OBJ.set_bytes(LINE_BYTES)
			LINE_OBJ.set_parsed(LINE)



		sec_ind += 1


	###############################################################################################

	###############################################################################################

	# populate section code with code bytes
	
	#
	sec_ind = 0
	for sec in sections:

		sec_bytes = []

		for LINE_OBJ in sec["code_data"]:
			for b in LINE_OBJ.get_bytes():
				sec_bytes.append(b)

		sections[sec_ind]["REL_DATA"] = sec_bytes

		sec_ind += 1




	ASSEMBLED_CODE = []

	sec_ind = 0
	for sec in sections:
		#print(sec["secname"], sec["size"])

		if sec["group"] != "DATA" or (sec["group"] == "DATA" and sec["REL_DATA"] != []):

			INDEX = -1
			i = 0
			for s in sections:
				if s["secname"] == sec["secname"]:
					INDEX = i
					break
				i += 1
			if INDEX > 0:
				ASSEMBLED_CODE.append(0x01)
				ASSEMBLED_CODE.append(0x00)
				ASSEMBLED_CODE.append(INDEX)

			if INDEX != sec_ind:
				sections[INDEX]["size"] += sec["size"]

			for b in sec["REL_DATA"]:
				ASSEMBLED_CODE.append(b)

				if INDEX != sec_ind:
					sections[INDEX]["REL_DATA"].append(b)

		sec_ind += 1


	final_sections = []

	sec_ind = 0
	for sec in sections:

		INDEX = -1
		i = 0
		for s in sections:
			if s["secname"] == sec["secname"]:
				INDEX = i
				break
			i += 1

		if INDEX == sec_ind:
			final_sections.append(sec)

		sec_ind += 1



	sections_to_indexes = {}

	ind = 0
	for s in final_sections:
		sections_to_indexes[s["secname"]] = ind
		ind += 1





	###############################################################################################

	###############################################################################################


	# step 6: convert into REL file format

	REL_DATA = []

	###############################################################################################

	# REL file header

	REL_DATA.append(0x33)
	REL_DATA.append(0x61)  # REL header
	REL_DATA.append(0x01)

	REL_DATA.append(0x00)  # ?? data
	REL_DATA.append(0x00)


	# compilation date
	today = date.today()
	year, month, day = tuple([int(d) for d in today.strftime("%y/%m/%d").split("/")])

	REL_DATA.append(year%100)
	REL_DATA.append(month)
	REL_DATA.append(day)

	# compilation time
	now = datetime.now()
	hours, minutes, seconds = tuple([int(d) for d in now.strftime("%H:%M:%S").split(":")])

	REL_DATA.append(hours)
	REL_DATA.append(minutes)
	REL_DATA.append(seconds)

	REL_DATA.append(0x00)  # garbage byte, probably milliseconds or something


	REL_DATA.append(len("65C816 V2.11"))
	for b in "65C816 V2.11":
		REL_DATA.append(ord(b))

	for _ in range(7):
		REL_DATA.append(0x00)


	###############################################################################################


	# group data
	GROUP_DATA = []

	for g in groups[1:]:

		GROUP_DATA.append(len(g))

		for b in g:
			GROUP_DATA.append(ord(b))

		for _ in range(8):
			GROUP_DATA.append(0x00) # still no idea what this is

		GROUP_DATA.append(0x00) # to end section????????



	len_bytes = make_length_bytes(len(GROUP_DATA) + 1)


	for b in len_bytes:
		REL_DATA.append(b)

	for b in GROUP_DATA:
		REL_DATA.append(b)

	REL_DATA.append(0x00) # end group data



	###############################################################################################

	# section data

	SECTION_DATA = []

	for s in final_sections[1:]:

		SECTION_DATA.append(len(s["secname"]))

		for b in s["secname"]:
			SECTION_DATA.append(ord(b))

		group_ind = 0

		for g in range(len(groups)):
			if groups[g] == s["group"]:
				group_ind = g



		if s["type"] == util.DATA_TYPES.ORG:
			# org section
			SECTION_DATA.append(0x02) # org

			SECTION_DATA.append(0x00) # technically should be full "group" index, but Im lazy and this is a prototype
			SECTION_DATA.append(0x00)

			SECTION_DATA.append(group_ind)

			SECTION_DATA.append(0x08)
			for _ in range(4):
				SECTION_DATA.append(0x00)

			for _ in range(9, 28):
				SECTION_DATA.append(0x00)

			location_bytes = []
			loc = s["offset"]

			for _ in range(4):
				location_bytes.append(loc % 256)
				loc = loc // 256

			for b in reversed(location_bytes):
				SECTION_DATA.append(b)



		else:

			if s["secname"].lower() == "comn":
				# COMN section
				SECTION_DATA.append(0x00) # comn

				SECTION_DATA.append(0x00) # technically should be full "group" index, but Im lazy and this is a prototype
				SECTION_DATA.append(0x00)

				SECTION_DATA.append(group_ind)

				SECTION_DATA.append(0x08)
				for _ in range(4):
					SECTION_DATA.append(0x00)

				for _ in range(9, 32):
					SECTION_DATA.append(0x00)

			else:
				# regular section
				SECTION_DATA.append(0x01) # section

				SECTION_DATA.append(0x00) # technically should be full "group" index, but Im lazy and this is a prototype
				SECTION_DATA.append(0x00)

				SECTION_DATA.append(group_ind)

				SECTION_DATA.append(0x08)
				for _ in range(4):
					SECTION_DATA.append(0x00)

				for _ in range(9, 32):
					SECTION_DATA.append(0x00)


		size = s["size"]
		size_bytes = []

		for _ in range(4):
			size_bytes.append(size % 256)
			size = size // 256

		for b in reversed(size_bytes):
			SECTION_DATA.append(b)

	len_bytes = make_length_bytes(len(SECTION_DATA) + 1)


	for b in len_bytes:
		REL_DATA.append(b)

	for b in SECTION_DATA:
		REL_DATA.append(b)

	REL_DATA.append(0x00)  # end section data block 




	###############################################################################################


	# global var data

	GLOBAL_DATA = []


	for g in globalvars[1:]:

		GLOBAL_DATA.append(len(g))

		for b in g:
			GLOBAL_DATA.append(ord(b))


		is_global = True

		for e in externalvars:
			if g == e:
				is_global = False
				break


		if not is_global:
			GLOBAL_DATA.append(0x04) # external variable

			for _ in range(8):
				GLOBAL_DATA.append(0x00)



		else:
			var = None
			for v in localvars:
				if v["name"] == g:
					var = v

					val = -1
					if v["type"] == "label":
						val = v["offset"]
					elif v["type"] == "exact":
						val = v["value"]

					EXTERNAL_SYMBOLS[v["name"]] = (v["type"], val)

					break

			if var == None:
				raise Exception("Global isnt local: " + g)


			if var["type"] == "label":
				GLOBAL_DATA.append(0x05) # label value

				section_bytes = []
				sec = sections_to_indexes[var["section"]]

				for _ in range(4):
					section_bytes.append(sec % 256)
					sec = sec // 256

				for b in reversed(section_bytes):
					GLOBAL_DATA.append(b)

				offset_bytes = []
				offset = var["offset"]

				for _ in range(4):
					offset_bytes.append(offset % 256)
					offset = offset // 256

				for b in reversed(offset_bytes):
					GLOBAL_DATA.append(b)


			elif var["type"] == "exact":
				GLOBAL_DATA.append(0x06) # exact value


				val_bytes = []
				val = var["value"]

				for _ in range(8):
					val_bytes.append(val % 256)
					val = val // 256

				for b in reversed(val_bytes):
					GLOBAL_DATA.append(b)



	len_bytes = make_length_bytes(len(GLOBAL_DATA) + 1)

	for b in len_bytes:
		REL_DATA.append(b)

	for b in GLOBAL_DATA:
		REL_DATA.append(b)

	REL_DATA.append(0x00)  # end global vars block 



	###############################################################################################



	# processor status data
	PROCESSOR_DATA = []


	for p in reversed(processor_flags):
		PROCESSOR_DATA.append(0x00)

		if p["type"] == "idx8":
			PROCESSOR_DATA.append(0x01)
		elif p["type"] == "idx16":
			PROCESSOR_DATA.append(0x02)
		elif p["type"] == "mem8":
			PROCESSOR_DATA.append(0x03)
		elif p["type"] == "mem16":
			PROCESSOR_DATA.append(0x04)

		PROCESSOR_DATA.append(0x01) # dont know... but needed


		section_bytes = []
		sec = sections_to_indexes[sections[p["section"]]["secname"]]

		for _ in range(4):
			section_bytes.append(sec % 256)
			sec = sec // 256

		for b in reversed(section_bytes):
			PROCESSOR_DATA.append(b)


		offset_bytes = []
		offset = p["offset"]

		for _ in range(4):
			offset_bytes.append(offset % 256)
			offset = offset // 256

		for b in reversed(offset_bytes):
			PROCESSOR_DATA.append(b)



	len_bytes = make_length_bytes(len(PROCESSOR_DATA) + 2)

	for b in len_bytes:
		REL_DATA.append(b)

	for b in PROCESSOR_DATA:
		REL_DATA.append(b)


	REL_DATA.append(0x00)
	REL_DATA.append(0x00)  # end processor data block 




	###############################################################################################


	# file name data????????
	REL_DATA.append(len(FILE_NAME))

	for b in FILE_NAME:
		REL_DATA.append(ord(b))


	###############################################################################################


	# local variable data
	LOCAL_DATA = []

	for var in localvars:
		
		if (not "is_temp" in var) or (not var["is_temp"]):

			LOCAL_DATA.append(len(var["name"]))

			for b in var["name"]:
				LOCAL_DATA.append(ord(b))


			if var["type"] == "label":
				LOCAL_DATA.append(0x01) # label


				section_bytes = []
				sec = sections_to_indexes[var["section"]]

				for _ in range(4):
					section_bytes.append(sec % 256)
					sec = sec // 256

				for b in reversed(section_bytes):
					LOCAL_DATA.append(b)


				offset_bytes = []
				offset = var["offset"]

				for _ in range(4):
					offset_bytes.append(offset % 256)
					offset = offset // 256

				for b in reversed(offset_bytes):
					LOCAL_DATA.append(b)


			elif var["type"] == "exact":
				LOCAL_DATA.append(0x02) # equ


				val_bytes = []
				val = var["value"]

				for _ in range(8):
					val_bytes.append(val % 256)
					val = val // 256

				for b in reversed(val_bytes):
					LOCAL_DATA.append(b)




	len_bytes = make_length_bytes(len(LOCAL_DATA) + 1)

	for b in len_bytes:
		REL_DATA.append(b)

	for b in LOCAL_DATA:
		REL_DATA.append(b)


	REL_DATA.append(0x00)  # end local variable data


	###############################################################################################


	# finally, code data


	for b in ASSEMBLED_CODE:
		REL_DATA.append(b)


	REL_DATA.append(0x00)  # end code data
	REL_DATA.append(0x00)





	###############################################################################################

	###############################################################################################

	# output REL formatted assembled code




	set_symbols(SYMBOLS_FILE)



	
	# section testing
	with open(FILE_PATH + FILE_NAME.split(".")[0] + ".lis", "w") as LIS_FILE:
		for S in sections:
			for LINE in S["code_data"]:
				#print(LINE._raw_line.encode("utf-8"))

				text = format(LINE.get_offset(), "04x") + "    " + " ".join([format(x, "02x") for x in LINE.get_bytes()]).ljust(80) + str(LINE.get_raw()).ljust(50)
				#print(LINE.get_bytes(), str(LINE.get_raw()))

				#print("")
				LIS_FILE.write(text + "\n")



	with open(FILE_PATH + FILE_NAME.split(".")[0] + ".rel", "wb") as REL_FILE:
		REL_FILE.write(bytes(REL_DATA))


	
	

	print("Finished writing " + FILE_NAME.split(".")[0] + ".rel")





				








if __name__ == "__main__":


	parser = argparse.ArgumentParser(description="Assemble a .asm file into a .rel file")

	parser.add_argument("file", metavar="file", type=str, help="Name of file to assemble")

	parser.add_argument("--options", dest="asm_args", nargs="+", action="append", default=[], help="Optional arguments for assembler")



	ARGS = vars(parser.parse_args())

	ASM_ARGS = []

	if len(ARGS["asm_args"]) > 0:
		ASM_ARGS = ARGS["asm_args"][0]

	optional_args = {}
	i = 0
	while i < len(ASM_ARGS):

		if i+1 < len(ASM_ARGS):
			optional_args[ASM_ARGS[i]] = int(ASM_ARGS[i+1])
		
		i += 2

	if i == len(ASM_ARGS) + 1:
		raise Exception("Invalid args " + str(ASM_ARGS))


	assembleFile(ARGS["file"], optional_args)




#assembleFile("Pause.asm", {"ENG_VER": 1})

#assembleFile("sfxdos.asm", {})

#assembleFile("kart-init.asm")




