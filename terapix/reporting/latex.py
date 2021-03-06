##############################################################################
#
# Copyright (c) 2008-2010 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################

"""
Stuff to generate LaTeX reports
"""

import types, time
import string, os.path
from django.conf import settings
from terapix.lib.common import Template

report_conf_dir = os.path.join(settings.TRUNK, 'terapix', 'reporting', 'tex')

class LaTeXReport(object):
	def __init__(self, outfile, user, name = 'Report name', landscape = False):
		self.name = name
		self.user = user
		self.header_params = {
			'generated': "Generated by user %s at %s" % (user.username, time.strftime('%H:%M')), 
			'reportName': self.name,
		}
		self.__outfile = outfile
		self.__raw = ''

	def __getHeader(self, headerFile):
		h = open(headerFile)
		data = ''.join(h.readlines())
		t = Template(data)
		h.close()
		return t.substitute(**self.header_params)

	def __getFooter(self, footerFile):
		h = open(footerFile)
		data = ''.join(h.readlines())
		t = Template(data)
		h.close()
		return t.substitute()

	def addTable(self, header, data, caption = None):
		for i in (header, data):
			if type(i) != types.ListType and type(i) != types.TupleType:
				raise ValueError, "%s must be a list or tuple" % i
		t = """
\\begin{landscape}\n
\\begin{longtable}{%s}\n""" % ('l' * len(header))
		if caption:
			t += """
	\caption{Le tableau}\\\\\n"""

		fhead = ' & '.join(["\\bfseries " + h for h in header])
		fhead += "\\\\ \hline\n"
		t += fhead + "\\endfirsthead\n" + fhead + "\\endhead\n"
		t += """
	\hline \multicolumn{%d}{r}{\emph{Continued on next page}}\n""" % len(header)
		t += """
\\endfoot
	\hline
\\endlastfoot\n"""

		for d in data:
			t += ' & '.join([str(i).replace('_', '\\_') for i in d]) + '\\\\\hline\n'

		t += "\\end{longtable}\n"
		t += "\\end{landscape}\n"
		self.__raw += t

	def addRawContent(self, raw):
		"""
		Add raw TeX content
		"""
		self.__raw += raw + '\n'

	def save(self, 	header = os.path.join(report_conf_dir, 'report-header.tex'),
					footer = os.path.join(report_conf_dir, 'report-footer.tex')):
		# Header
		self.__outfile.write(self.__getHeader(header))
		# content
		self.__outfile.write(self.__raw)
		# Footer
		self.__outfile.write(self.__getFooter(footer))

