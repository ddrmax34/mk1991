



class Error(Exception):
	"""Base class for other exceptions"""

	def __init__(self, msg=""):
		self.msg = msg

		super().__init__(self.msg)



class LineException(Exception):
	"""General exception for errors in asm code
	
	Attributes:
		line_num -- line number where error occured
		line_ind -- index of character in line where error occured
		msg -- error message
		file -- file that error occured in
	"""

	def __init__(self, line_num=-1, msg=None, file=None, line_ind=-1):
		self.line_num = line_num
		self.line_ind = line_ind
		self.msg = msg
		self.file = file

		err_msg = "Error"

		if self.file != None:
			err_msg += " in " + self.file

		if self.line_num != -1:
			err_msg += " at line " + str(self.line_num)

			if self.line_ind != -1:
				err_msg += ", index " + str(self.line_ind)

		if self.msg != None:
			err_msg += ":\n\t" + str(self.msg)

		super().__init__(err_msg)



	

