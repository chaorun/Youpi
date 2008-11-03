
import MySQLdb, pyfits
import pprint, re, glob, string
import math, md5, random
import marshal, base64
import os, os.path, sys, pprint
import socket, time
from types import *
#
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.db.models import get_models
from django.utils.datastructures import *
from django.template import Template, Context, RequestContext
#
from terapix.youpi.forms import *
from terapix.youpi.models import *
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *
from terapix.youpi.cviews import *
from terapix.youpi.pluginmanager import PluginManagerError, PluginError
#
from terapix.settings import *

def processing_save_image_selection(request):
	"""
	Saves image selection to DB.
	"""
	try:
		name = request.POST['Name']
		idList = eval(request.POST['IdList'])
	except Exception, e:
		return HttpResponseForbidden()

	# Base64 encoding + marshal serialization
	sList = base64.encodestring(marshal.dumps(idList)).replace('\n', NULLSTRING)

	try:
		# Updates entry
		imgSelEntry = ImageSelections.objects.filter(name = name)[0]
		imgSelEntry.data = sList
	except:
		# ... or inserts a new one
		imgSelEntry = ImageSelections(name = name, data = sList, user = request.user)

	imgSelEntry.save()

	return HttpResponse(str({'name' : str(name), 'id' : int(imgSelEntry.id)}), mimetype = 'text/plain')

def processing_check_config_file_exists(request):
	"""
	Checks if a config file with that name (for a given processing plugin) already exists.
	"""
	try:
		kind = request.POST['Kind']
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseForbidden()

	config = ConfigFile.objects.filter(kind__name__exact = kind, name = name)

	if config:
		exists = 1
	else:
		exists = 0

	return HttpResponse(str({'result' : exists}), mimetype = 'text/plain')

def processing_get_image_selections(request):
	"""
	Returns image selections.
	"""
	try:
		name = request.POST['Name']
		all = False
	except Exception, e:
		all = True

	mode = request.POST.get('Mode', 'Single') # Single or Batch

	if not all:
		try:
			sel = ImageSelections.objects.filter(name = name)[0]
			# marshal de-serialization + base64 decoding
			idList = marshal.loads(base64.decodestring(str(sel.data)))
			if mode == 'Single' and len(idList) > 1:
				idList = []
		except:
			# Not found
			idList = []
	else:
		sel = ImageSelections.objects.all().order_by('name')
		idList = []
		for s in sel:
			sList = marshal.loads(base64.decodestring(str(s.data)))
			if mode == 'Single' and len(sList) == 1:
				idList.append([str(s.name), sList])
			elif mode == 'Batch' and len(sList) > 1:
				idList.append([str(s.name), sList])

	count = len(idList)

	return HttpResponse(str({'data' : idList, 'count' : count}), mimetype = 'text/plain')

def processing_delete_image_selection(request):
	"""
	Deletes one (stored) image selection
	"""
	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseForbidden()

	try:
		sel = ImageSelections.objects.filter(name = name)[0]
		sel.delete();
	except:
		# FIXME: do something if not sel !
		pass

	return HttpResponse(str({'data' : str(name)}), mimetype = 'text/plain')

def getSQLSignComparator(condTxt):
	c = '='
	if condTxt == 'is different from':
		c = '<>'
	elif condTxt == 'is equal to':
		c = '='
	elif condTxt == 'is greater than':
		c = '>='
	elif condTxt == 'is lower than':
		c = '<='
	elif condTxt == 'contains':
		c = 'LIKE'
	else:
		c = 'LIKE'

	return c

def getConditionalQueryText(request):
	try:
		lines = request.POST['Lines'].split(',')
	except Exception, e:
		return HttpResponseForbidden()

	try:
		# List of selectd values, if any
		multiSel= request.POST['MultiSelection'].split(',')
		hasMultiSel = True
	except:
		hasMultiSel = False

	query = ''
	for i in range(len(lines)):
		# Line number
		j = int(lines[i])
		lineField = request.POST["Line%dField" % j]
		lineCond = request.POST["Line%dCond" % j]
		lineText = request.POST["Line%dText" % j]
	
		if i > 0:
			query += request.POST["Line%dBoolSelect" % j] + WHITESPACE

		if hasMultiSel:
			query += '('

		query += lineField + WHITESPACE
		signCond = getSQLSignComparator(lineCond)

		if signCond == 'LIKE':
			query += signCond + WHITESPACE + '\"%' + lineText + '%\" '
		else:
			query += "%s \"%s\" " % (signCond, lineText)

		if hasMultiSel:
			# For multi-selections, cond will never be LIKE
			k = 'OR'
			if signCond == '<>':
				k = 'AND'
			for sel in multiSel:
				query += "%s %s %s \"%s\" " % (k, lineField, signCond, sel)
			query += ') '

	return query

def preingestion_tables_count(request):
	"""
	"""
	try:
		path = request.POST['path']
	except:
		return HttpResponseForbidden()

	# Look for data
	data = glob.glob("%s*" % path)
	regFitsSearchPattern = '^mcmd\..*\.fits$'

	tables = []
	for file in data:
		if os.path.isfile(file):
			sfile = os.path.basename(file)
			if re.match(regFitsSearchPattern, sfile):
				# This is a fits table file
				tables.append(sfile)

	# Return a basic JSON object
	return HttpResponse(str([{'path' : str(path), 'tables' : [str(e) for e in tables] }]), mimetype = 'text/plain')


def preingestion_run(request):
	"""
	"""

	try:
		table = request.POST['table']
		path = request.POST['path']
	except Exception, e:
		return HttpResponseForbidden()

	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)

	# Do the job
	try:
		preingest_table(g, table, path)
	except Exception ,e:
		return HttpResponseServerError("Script error: %s" % e)

	return HttpResponse(table + ' done.', mimetype = 'text/plain')

def history_preingestion(request):
	"""
	Return a JSON object with data related to preingestions' history
	"""

	try:
		limit = request.POST['limit']
	except Exception, e:
		return HttpResponseServerError("Script error: %s" % e)

	try:
		limit = int(limit)
	except ValueError, e:
		# Unlimitted
		limit = 0

	res = Fitstables.objects.all()

	if limit > 0:
		res = res[:limit]

	#
	# We build a standard header that can be used for table's header.
	# header var must be a list not a tuple since it get passed 'as is' to the json 
	# dictionary
	#
	header = ['Image', 'Instrument', 'Channel', 'Run', 'QSO status', 'Path']

	data = []
	for r in res:
			#
			# Unicode strings have to be converted to basic strings with str()
			# in order to get a valid JSON object
			#
			data.append({	header[0] 	: str(r.name), 
							header[1] 	: str(r.instrument),
							header[2] 	: str(r.channel),
							header[3] 	: str(r.run),
							header[4] 	: str(r.QSOstatus),
							header[5] 	: str(r.fitstable)
			})

	# Be aware that JS code WILL search for data and header members
	json = { 'data' : data, 'header' : header }

	# Return a JSON object
	return HttpResponse(str(json), mimetype = 'text/plain')

def preingestion_table_fields(request):
	"""
	Return a JSON object with data related to table's fields
	"""

	try:
		table = request.POST['table']
	except Exception, e:
		return HttpResponseForbidden()

	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)

	try:
		res = g.execute("Desc " + table);
	except MySQLdb.DatabaseError, e:
		return HttpResponseServerError("Error: %s" % e)

	return HttpResponse(str({'fields' : [r[0] for r in res]}), mimetype = 'text/plain')

def preingestion_custom_query(request):
	"""
	Builds an SQL query based on POST data, executes it and returns a JSON object containing results.
	"""

	try:
		table = request.POST['Table']
		displayField = request.POST['DisplayField']
		#
		# Line'n'Field, Line'n'Cond, Line'n'Text for n>=0
		# and Line'n'BoolSelect for n>0
		#
		lines = request.POST['Lines'].split(',')
		orderBy = request.POST['OrderBy']
		hide = request.POST['Hide']
	except Exception, e:
		return HttpResponseForbidden()

	try:
		limit = int(request.POST['Limit'])
	except Exception, e:
		# No limit
		limit = 0

	simpleQuery = False
	try:
		ftable = request.POST['Ftable']
		ftableField = request.POST['FtableField']
		ftableFieldValue = request.POST['FtableFieldValue']
		ftableId = request.POST['FtableId']
		fkId = request.POST['FkId']
	except Exception, e:
		simpleQuery = True

	try:
		# Search through subset only
		idList = request.POST['IdList']
		idField = request.POST['IdField']
	except Exception, e:
		idList = None

	try:
		# Search through subset only
		dist = request.POST['Distinct']
		distinct = True
	except:
		distinct = False

	try:
		revert = request.POST['Revert']
		revert = True
	except:
		revert = False

	try:
		condTxt = request.POST["Line0Cond"]
		contTxt = True
	except:
		contTxt = False

	query = 'SELECT' + WHITESPACE

	try:
		# List of selectd values, if any
		multiSel= request.POST['MultiSelection'].split(',')
		hasMultiSel = True
	except:
		hasMultiSel = False

	if simpleQuery:
		try:
			tableField = request.POST['TableField']
			tableFieldValue = request.POST['TableFieldValue']
		except:
			tableField = None

		if distinct:
			query += "DISTINCT("

		if displayField == 'all':
			query += '*'
		else:
			query += displayField

		if distinct:
			query += ")"
	
		query += WHITESPACE + "FROM %s WHERE " % table
		if not idList:
			query += getConditionalQueryText(request)
			
		if tableField:
			c = getSQLSignComparator(condTxt)
			query += "%s %s \"%s\" " % (tableField, c, tableFieldValue)

		if idList:
			line0 = True
			try:
				line0Field = request.POST['Line0Field']
				line0Text = request.POST['Line0Text']
			except Exception, e:
				line0 = False

			c = getSQLSignComparator(condTxt)

			if not line0:
				query += "%s IN (%s) " % (idField, idList)
			else:
				if hasMultiSel:
					query += "%s IN (%s) AND ( %s %s \"%s\" " % (idField, idList, line0Field, c, line0Text)
					k = 'OR'
					if c == '<>':
						k = 'AND'
					for sel in multiSel:
						query += "%s %s %s \"%s\" " % (k, line0Field, c, sel)
					query += ') '
				else:
					query += "%s IN (%s) AND %s %s \"%s\" " % (idField, idList, line0Field, c, line0Text)

		query += "ORDER BY %s" % orderBy
	
		if limit > 0:
			query += " LIMIT %d;" % limit

	else:
		# Join 2 tables, more complex query
		query += 'a.'
		if displayField == 'all':
			query += '*'
		else:
			query += displayField

		if idList:
			c = getSQLSignComparator(condTxt)
			query += " FROM %s AS a, %s AS b WHERE a.%s=b.%s AND " % (table, ftable, fkId, ftableId)

			if hasMultiSel:
				query += "(b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)
				k = 'OR'
				if c == '<>':
					k = 'AND'

				for sel in multiSel:
					query += " %s b.%s %s \"%s\"" % (k, ftableField, c, sel)
				query += ')'
			else:
				query += "b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)

			if revert:
				query += " AND b.%s " % idField
			else:
				query += " AND a.%s " % idField

			query += "IN (%s)" % idList
		else:
			query += " FROM %s AS a, %s AS b WHERE a.%s=b.%s AND (" % (table, ftable, fkId, ftableId)
			c = getSQLSignComparator(condTxt)

			if hasMultiSel:
				query += "b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)
				k = 'OR'
				if c == '<>':
					k = 'AND'

				# For multi-selections, cond will never be LIKE
				for sel in multiSel:
					query += " %s b.%s %s \"%s\"" % (k, ftableField, c, sel)
			else:
				query += "b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)

			query += ')'

	# Now executes query
	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)

	try:
		res = g.execute(query);
	except MySQLdb.DatabaseError, e:
		return HttpResponseServerError("Error: %s [Query: \"%s\"]" % (e, query))
	except Exception, e:
		return HttpResponse(str({'query' : "%s [Error] %s" % (str(query), e), 'fields' : [], 'data' : [], 'hidden' : str(hide).split(',')}), mimetype = 'text/plain')

	data = []
	for r in res:
		line = []
		for f in r:
			line.append(str(f))
		data.append(line)

	# See PEP-0249 for further details
	tableFields = [r[0] for r in g.cursor.description]

	return HttpResponse(str({'query' : str(query), 'fields' : tableFields, 'data' : data, 'hidden' : str(hide).split(',')}), mimetype = 'text/plain')

