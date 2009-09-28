##############################################################################
#
# Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################

import cjson as json
import MySQLdb, pyfits
import pprint, re, glob, string
import math, md5, random
import marshal, base64, zlib
import os, os.path, sys, pprint
import socket, time
import xml.dom.minidom as dom
from types import *
from stat import *
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.db.models import get_models
from django.utils.datastructures import *
from django.template import Template, Context, RequestContext
from django.contrib.auth.models import User
#
from terapix.youpi.auth import *
from terapix.youpi.cviews import *
from terapix.youpi.cviews.condreqstr import *
from terapix.youpi.models import *
from terapix.youpi.pluginmanager import PluginManagerError
#
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *

def condor_status(request):
	return HttpResponse(str({'results' : get_condor_status()}), mimetype = 'text/plain')

@login_required
@profile
def ingestion_img_count(request):
	"""
	Returns number of ingested images
	"""

	try:
		releaseId = request.POST.get('ReleaseId', None)
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	if releaseId:
		q = Rel_imgrel.objects.filter(release__id = int(releaseId)).count()
	else:
		q = Image.objects.all().count()

	return HttpResponse(str({'Total' : int(q)}), mimetype = 'text/plain')

@login_required
@profile
def image_grading(request, pluginName, fitsId):
	"""
	Image grading template.
	"""

	plugin = manager.getPluginByName(pluginName)
	if plugin:
		try:
			path = plugin.getUrlToGradingData(request, fitsId)
		except IndexError:
			return HttpResponseRedirect(settings.AUP + '/results/')
	else:
		return HttpResponseRedirect(settings.AUP + '/results/')

	return render_to_response('grading.html', {'www' : path, 'pluginName' : pluginName, 'fitsId' : fitsId}, context_instance = RequestContext(request))

@login_required
@profile
def grading_panel(request, pluginId, fitsId):
	"""
	Image grading panel.
	"""
	plugin = manager.getPluginByName(pluginId)
	path = plugin.getUrlToGradingData(request, fitsId)

	# TODO: handle cases other than qfits-in
	# Looks for existing grade
	f = Plugin_fitsin.objects.filter(id = int(fitsId))[0]
	m = FirstQEval.objects.filter(user = request.user, fitsin = f)
	evals = FirstQEval.objects.filter(fitsin = f).order_by('-date')
	comments = FirstQComment.objects.all()
	prev_releaseinfo =  Plugin_fitsin.objects.filter(id = int(fitsId))

	if m:
		grade = m[0].grade
		userPCommentId = m[0].comment.id
		customComment = m[0].custom_comment
	else:
		grade = None
		userPCommentId = None
		customComment = None
	
	return render_to_response('grading_panel.html', {	
						'www' 		: path, 
						'pluginId' 	: pluginId,
						'fitsId' 	: fitsId,
						'userGrade'	: grade,
						'comments'	: comments,
						'userPCommentId' : userPCommentId,
						'customComment' : customComment,
						'evals' 	: evals,
						'prev_releaseinfo'	: prev_releaseinfo,
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def grading_cancel(request, pluginId, fitsId):
	"""
	Cancels a grade.
	"""

	plugin = manager.getPluginByName(pluginId)

	# TODO: handle cases other than qfits-in
	# Looks for existing grade
	f = Plugin_fitsin.objects.filter(id = int(fitsId))[0]
	m = FirstQEval.objects.filter(user = request.user, fitsin = f)
	evals = FirstQEval.objects.filter(fitsin = f).order_by('-date')
	comments = FirstQComment.objects.all()
	prev_releaseinfo =  Plugin_fitsin.objects.filter(id = int(fitsId))

	if m:
		m.delete()
	
	return render_to_response('grading_panel.html', {	'pluginId' 	: pluginId,
														'fitsId' 	: fitsId,
														'comments'	: comments,
														'evals' 	: evals,
														'prev_releaseinfo'	: prev_releaseinfo,
													}, 
													context_instance = RequestContext(request))

def dir_stats(request):
	"""
	From the results page, return statistics about finished processing in result output dir.
	"""

	try:
		dir = request.POST['ResultsOutputDir']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	task = Processing_task.objects.filter(results_output_dir = dir)[0]
	plugin = manager.getPluginByName(task.kind.name)
	stats = plugin.getOutputDirStats(dir)

	return HttpResponse(str({	'PluginId' 	: str(plugin.id),
								'Stats'		: stats }),
								mimetype = 'text/plain')

def task_filter(request):
	try:
		owner = request.POST['Owner']
		status = request.POST['Status']
		kindid = request.POST['Kind']
		filterText = request.POST['FilterText'].strip().lower()
		# Max results per page
		maxPerPage = int(request.POST['Limit'])
		# page # to return
		targetPage = int(request.POST['Page'])
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	lenAllTasks = Processing_task.objects.count()

	anyStatus = False
	if status == 'successful': success = 1
	elif status == 'failed': success = 0
	else: anyStatus = True

	from django.db import connection
	cur = connection.cursor()
	q = """
	SELECT t.id FROM youpi_processing_task AS t, youpi_processing_kind AS k
	WHERE t.kind_id=k.id
	AND k.name = '%s'
	%s
	ORDER BY end_date DESC
	"""
	filtered = False
	user_id = request.user.id

	if owner == 'all':
		if anyStatus: cur.execute(q % (kindid, ''))
		else: cur.execute(q % (kindid, "AND t.success = %d" % success))

	elif owner == 'my':
		if anyStatus: cur.execute(q % (kindid, "AND t.user_id=%d" % user_id))
		else: cur.execute(q % (kindid, "AND t.user_id=%d AND t.success = %d" % (user_id, success)))

	elif owner == 'others':
		if anyStatus: cur.execute(q % (kindid, "AND t.user_id != %d" % user_id))
		else: cur.execute(q % (kindid, "AND t.user_id != %d AND t.success = %d" % (user_id, success)))
	else:
		cur.execute(q % (kindid, ''))
			
	res = cur.fetchall()
	tasksIds = [{'id': r[0]} for r in res]
	res = []
	nb_suc = nb_failed = 0
	if filterText:
		keepIds = []
		for t in tasksIds:
			rels = Rel_it.objects.filter(task__id = t['id'])
			for r in rels:
				if r.image.name.find(filterText) >= 0:
					keepIds.append(t['id'])

#			if (t.user.username.lower().find(filterText) >= 0 or
#				t.user.first_name.lower().find(filterText) >= 0 or
#				t.user.last_name.lower().find(filterText) >= 0 or
#				t.kind.name.lower().find(filterText) >= 0 or
#				t.hostname.lower().find(filterText) >= 0 or
#				t.title.lower().find(filterText) >= 0 or
#				("%s" % t.start_date).find(filterText) >= 0 or
#				("%s" % t.end_date).find(filterText) >= 0):

		tasksIds = keepIds
	else:
		tasksIds = [t['id'] for t in tasksIds]

	plugin = manager.getPluginByName(kindid)

	# Plugins can optionally filter/alter the result set
	try:
		tasksIds = plugin.filterProcessingHistoryTasks(request, tasksIds)
	except AttributeError:
		# Not implemented
		pass

	if len(tasksIds) > maxPerPage:
		pageCount = len(tasksIds)/maxPerPage
		if len(tasksIds) % maxPerPage > 0:
			pageCount += 1
	else:
		pageCount = 1

	# Tasks ids for the page
	tasksIds = tasksIds[(targetPage-1)*maxPerPage:targetPage*maxPerPage]
	tasks = Processing_task.objects.filter(id__in = tasksIds).order_by('-end_date')
	for t in tasks:
		if t.success:
			nb_suc += 1
		else:
			nb_failed += 1

		tdata = {	'Success' 		: t.success,
					'Name' 			: str(t.kind.name),
					'Label' 		: str(t.kind.label),
					'Id' 			: str(t.id),
					'User' 			: str(t.user.username),
					'Start' 		: str(t.start_date),
					'End' 			: str(t.end_date),
					'Duration' 		: str(t.end_date-t.start_date),
					'Node' 			: str(t.hostname),
					'Title'			: str(t.title),
		}
		
		# Looks for plugin extra data, if any
		try:
			extra = plugin.getProcessingHistoryExtraData(t.id)
			if extra:
				tdata['Extra'] = extra
		except AttributeError:
			# No method for extra data
			pass
		res.append(tdata)

	resp = {
		'filtered' : filtered,
		'results' : res, 
		'Stats' : {	
			'nb_success' 	: nb_suc, 
			'nb_failed' 	: nb_failed, 
			'nb_total' 		: nb_suc + nb_failed,
			'pageCount'		: pageCount,
			'curPage'		: targetPage,
			'TasksIds' 		: tasksIds,
			'nb_big_total' 	: lenAllTasks,
		},
	} 

	# Looks for plugin extra data, if any
	try:
		extraHeader = plugin.getProcessingHistoryExtraHeader(request)
		if extraHeader: resp['ExtraHeader'] = extraHeader
	except AttributeError:
		# No method for extra header data
		pass

	return HttpResponse(json.encode(resp), mimetype = 'text/plain')

@login_required
@profile
def autocomplete(request, key, value):
	"""
	Auto-completes <input> fields
	"""

	value = value.split('=')[1]
	res = []

	if key == 'IngestionName':
		data = Ingestion.objects.filter(label__istartswith = value)
		for d in data:
			res.append({'value' : str(d.label), 'info' : str("%s - %s" % (d.user.username, d.start_ingestion_date))})

	elif key == 'ImageSelections':
		data = ImageSelections.objects.filter(name__istartswith = value)
		for d in data:
			res.append({'value' : str(d.name), 'info' : str("%s - %s" % (d.user.username, d.date))})

	elif key == 'ConfigFile':
		data = ConfigFile.objects.filter(name__istartswith = value)
		for d in data:
			res.append({'value' : str(d.name), 'info' : str("%s - %s" % (d.user.username, d.date))})

	elif key == 'CondorSavedSelections':
		data = CondorNodeSel.objects.filter(label__istartswith = value, is_policy = False)

		for d in data:
			res.append({'value' : str(d.label), 'info' : str("%s - %s" % (d.user.username, d.date))})

	elif key == 'CondorSavedPolicies':
		data = CondorNodeSel.objects.filter(label__istartswith = value, is_policy = True)

		for d in data:
			res.append({'value' : str(d.label), 'info' : str("%s - %s" % (d.user.username, d.date))})

	elif key == 'Tag':
		data = Tag.objects.filter(name__istartswith = value).order_by('name')

		for d in data:
			res.append({'value' : str(d.name), 'info' : str("%s - %s" % (d.user.username, d.date))})

	return HttpResponse(str({'results' : res}), mimetype = 'text/plain')

def get_live_monitoring(request, nextPage = -1):
	"""
	Parses XML output from Condor and returns a JSON object.
	Only Youpi's related job are monitored. A Youpi job must have 
	an environment variable named YOUPI_USER_DATA which can contain
	serialized base64-encoded data to be parsed.

	nextPage: id of the page of 'limit' results to display. If nextPage == -1
	then full data set is returned.
	"""

	pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, 'condor_q -xml'))
	data = pipe.readlines()
	pipe.close()

	res = []
	# Max jobs per page
	limit = 10

	# Removes first 3 lines (not XML)
	doc = dom.parseString(string.join(data[3:]))
	jNode = doc.getElementsByTagName('c')

	# Youpi Condor job count
	jobCount = 0

	for job in jNode:
		jobData = {}
		data = job.getElementsByTagName('a')

		for a in data:
			if a.getAttribute('n') == 'ClusterId':
				jobData['ClusterId'] = str(a.firstChild.firstChild.nodeValue)

			elif a.getAttribute('n') == 'ProcId':
				jobData['ProcId'] = str(a.firstChild.firstChild.nodeValue)

			elif a.getAttribute('n') == 'JobStatus':
				# 2: running, 1: pending
				jobData['JobStatus'] = str(a.firstChild.firstChild.nodeValue)

			elif a.getAttribute('n') == 'RemoteHost':
				jobData['RemoteHost'] = str(a.firstChild.firstChild.nodeValue)

			elif a.getAttribute('n') == 'JobStartDate':
				secs = (time.time() - int(a.firstChild.firstChild.nodeValue))
				h = m = 0
				s = int(secs)
				if s > 60:
					m = s/60
					s = s%60
					if m > 60:
						h = m/60
						m = m%60

				jobData['JobDuration'] = "%02d:%02d:%02d" % (h, m, s)

			elif a.getAttribute('n') == 'Env':
				# Try to look for YOUPI_USER_DATA environment variable
				# If this is variable is found then this is a Youpi's job so we can keep it
				env = str(a.firstChild.firstChild.nodeValue)
				if env.find('YOUPI_USER_DATA') >= 0:
					m = re.search('YOUPI_USER_DATA=(.*?)$', env)
					userData = m.groups(0)[0]	
					c = userData.find(';')
					if c > 0:
						userData = userData[:c]
					jobData['UserData'] = marshal.loads(base64.decodestring(str(userData)))
					# Add 'Owner' field to dict
					jobData['UserData']['Owner'] = str(User.objects.filter(id = int(jobData['UserData']['UserID']))[0].username)

					res.append(jobData)
					jobCount += 1

	if nextPage >= 1:
		# Computes total pages
		pageCount = 1
		if jobCount  > limit:
			pageCount = jobCount / limit
			if jobCount % limit > 0:
				pageCount += 1
	
		# Selects res subset according to NextPage and limit
		if nextPage > pageCount:
			nextPage = pageCount

		res = res[(nextPage-1)*limit:limit*nextPage]
		retval = (res, jobCount, pageCount, nextPage)
	else:
		retval = (res, jobCount)

	return retval

@login_required
@profile
def live_monitoring(request):
	try:
		nextPage = request.POST['NextPage']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	res, jobCount, pageCount, nextPage = get_live_monitoring(request, int(nextPage))
	return HttpResponse(str({'results' : res, 'JobCount' : jobCount, 'PageCount' : pageCount, 'nextPage' : nextPage}), mimetype = 'text/plain')

def condor_hosts(request):
	vms = get_condor_status()
	hosts = []
	for vm in vms:
		host = vm[0][vm[0].find('@')+1:]
		if host not in hosts:
			hosts.append(str(host))

	return HttpResponse(str({'Hosts' : hosts}), mimetype = 'text/plain')

def condor_softs(request):
	return HttpResponse(str({'Softs' : [str(soft[0]) for soft in SOFTS]}), mimetype = 'text/plain')

def get_softs_versions(request):
	"""
	Looks for stored softwares version information in DB
	"""

	misc = MiscData.objects.filter(key = 'software_version')
	versions = [] 
	if misc:
		data = marshal.loads(base64.decodestring(misc[0].data))
		for host, info in data.iteritems():
			versions.append([host, info])

	return versions

def clear_softs_versions(request):
	"""
	Delete stored softwares versions stored into DB
	"""

	misc = MiscData.objects.filter(key = 'software_version')
	misc.delete()

	return HttpResponse(str({'Versions' : 'deleted'}), mimetype = 'text/plain')

def softs_versions(request):
	return HttpResponse(str({'Versions' : get_softs_versions(request)}), mimetype = 'text/plain')

def query_condor_node_for_versions(request):
	"""
	Sends a Condor job on a given host to retrieve softwares versions.
	First checks that a pending or running Condor job for this task is not running (to prevent job flooding)
	"""
	try:
		node = request.POST['Node']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	descr = str("Sofware version check on %s" % node)

	# Check if information is stored
	misc = MiscData.objects.filter(key = 'software_version')
	if misc:
		data = marshal.loads(base64.decodestring(misc[0].data))
		for host, info in data.iteritems():
			if host == node:
				return HttpResponse(str({'Versions' : get_softs_versions(request)}), mimetype = 'text/plain')

	# Find what's running
	res, count =  get_live_monitoring(request)

	for job in res:
		if job['UserData']['Descr'] == descr:
			# NOP
			return HttpResponse(str({'Versions' : 0}), mimetype = 'text/plain')


	# Content of YOUPI_USER_DATA env variable passed to Condor
	userData = {'Descr' 		: descr,
				'Node' 			: str(node),
				'UserID' 		: str(request.user.id)}

 	# Generates CSF
	submit_file_path = os.path.join(settings.TRUNK, 'terapix')
	condor_submit_file = """
#
# Condor submission file
# Please not that this file has been generated automatically by Youpi
#
executable              = %s/soft_version_check.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %s/local_conf.py, %s/settings.py, %s/DBGeneric.py, %s/NOP
initialdir				= %s
transfer_output_files   = NOP
# YOUPI_USER_DATA = %s
environment             = PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; YOUPI_USER_DATA=%s
arguments               = "%s"
log                     = /tmp/VCHECK.log.$(Cluster).$(Process)
error                   = /tmp/VCHECK.err.$(Cluster).$(Process)
output                  = /tmp/VCHECK.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
requirements            = Machine == "%s"
queue
""" % (	os.path.join(submit_file_path, 'script'),
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		userData, 
		base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
		base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
		node )

	csf = "/tmp/csf_version_check-%s-%s.txt" % (node, time.time())
	f = open(csf, 'w')
	f.write(condor_submit_file);
	f.close();

	job = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % csf))
	job.close()

	return HttpResponse(str({'Versions' : []}), mimetype = 'text/plain')

def job_cancel(request):
	"""
	Cancel one Job or more job. POST arg used are clusterId and procId.
	"""

	post = request.POST
	rmJobs = []

	what = post.get('What', None)
	if what == 'allmine':
		res, count = get_live_monitoring(request)
		for job in res:
			if int(job['UserData']['UserID']) == int(request.user.id):
				rmJobs.append("%s.%s" % (job['ClusterId'], job['ProcId']))

	elif what == 'all':
		res, count = get_live_monitoring(request)
		rmJobs = ["%s.%s" % (job['ClusterId'], job['ProcId']) for job in res]

	elif what is None:
		cluster = str(post['ClusterId'])
		proc = str(post['ProcId'])
		rmJobs = ["%s.%s" % (cluster, proc)]
	
	pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_rm %s" % string.join(rmJobs, ' ')))
	data = pipe.readlines()
	pipe.close()

	return HttpResponse(str({'CancelCount' : len(rmJobs)}), mimetype = 'text/plain')

def condor_ingestion(request):
	"""
	Callback for running a Condor ingestion.
	"""

	# HOST_DOMAIN
	try:
		path = request.POST['Path']
		ingestionId = request.POST['IngestionId']
		email = request.POST.get('ReportEmail', settings.CONDOR_NOTIFY_USER)
		checkAllowSeveralTimes = request.POST.get('CheckAllowSeveralTimes', 'no')
		checkSkipVerify = request.POST.get('CheckSkipVerify', 'no')
		checkQSOStatus = request.POST.get('CheckQSOStatus', 'no')
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	# Find machine
	clean_path = re.sub(settings.FILE_BROWSER_ROOT_DATA_PATH, '', path)
	m = re.search(settings.INGESTION_HOST_PATTERN, clean_path)
	if m: 
		host = m.group(1)
		# Now searches among user-defined mappings
		for pattern, value in settings.INGESTION_HOSTS_MAPPING.iteritems():
			if re.match(pattern, host):
				machine = value.replace('\1', host)
				break
	else: 
		machine = settings.INGESTION_DEFAULT_HOST

	#
	# Dictionnary that will be serialized with marshal module and passed
	# to the script as a string (argument 1). Note that the result of the serialization 
	# is base64 encoded to avoid bad caracter handling. The condor ingestion script 
	# will then de-serialize its first argument to access the data
	#
	script_args = { 'path' : path,
					'email' : email,
					'user_id' : request.user.id,
					'ingestion_id' : ingestionId,
					'allow_several_ingestions' : checkAllowSeveralTimes,
					'skip_fitsverify' : checkSkipVerify,
					'skip_qso_status' : checkQSOStatus,
					'host' : machine
	}

	# Content of YOUPI_USER_DATA env variable passed to Condor
	userData = { 'Descr' 		: str("Ingestion (%s) of FITS images " % ingestionId),
				'UserID' 		: str(request.user.id)}

	submit_file_path = os.path.join(settings.TRUNK, 'terapix')
	node = "Machine == \"%s\"" % machine

	# Add any custom Condor requirements, if any
	custom_req = request.user.get_profile().custom_condor_req

	# if custom_rep exists machine is composed by node and custom condor requirements from the condor setup panel
	if custom_req:
		machine = "((%s) && (%s))" % (node, custom_req)
	else:
		# if not machine only compose the requirements
		machine = node

	f = open(settings.CONDORFILE + '_' + ingestionId, 'w')
	f.write("""
executable = %(script)s/ingestion.py
universe                = vanilla
transfer_executable     = True
requirements            = %(req)s

# Arguments (base64 encoded + python serialization with marshal)
# Args equal to: %(clear_args)s
arguments               = "%(args)s"

should_transfer_files   = YES
when_to_transfer_output = ON_EXIT_OR_EVICT
transfer_input_files    = %(project_root)s/local_conf.py, %(project_root)s/settings.py, %(script)s/DBGeneric.py, %(project_root)s/NOP
initialdir				= %(script)s
transfer_output_files   = NOP
# Logs
# YOUPI_USER_DATA = %(clear_userdata)s
environment             = PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin:/opt/condor/bin; YOUPI_USER_DATA=%(userdata)s
output                  = %(log_output)s
error                   = %(log_error)s
log                     = %(log_log)s
queue
""" % {	
	'script'		: os.path.join(submit_file_path, 'script'), 
	'req'			: machine, 
	'clear_args'	: str(script_args),
	'args'			: base64.encodestring(marshal.dumps(script_args)).replace('\n', NULLSTRING),
	'project_root'	: submit_file_path,
	'clear_userdata': userData,
	'userdata'		: base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
	'log_output'	: settings.CONDOR_OUTPUT + '_' + ingestionId,
	'log_error'		: settings.CONDOR_ERROR + '_' + ingestionId,
	'log_log'		: settings.CONDOR_LOG + '_' + ingestionId,
})

	f.close()

	job = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % (settings.CONDORFILE + '_' + ingestionId)))
	resp = job.readlines()
	job.close()

	try:
		error = ''
		jobid = re.findall('(\d+)', resp[2])[1]
	except Exception, e:
		error = resp
		jobid = 'null'

	return HttpResponse(json.encode({
		'Path' 			: path, 
		'IngestionId' 	: ingestionId, 
		'Host' 			: node,
		'JobId' 		: jobid,
		'Error'			: error,
	}), mimetype = 'text/plain')

@login_required
@profile
def delete_processing_task(request):
	"""
	Delete a processing task
	"""
	try:
		taskId = request.POST['TaskId']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	success = False
	try:
		task = Processing_task.objects.filter(id = taskId)[0]
		rels = Rel_it.objects.filter(task = task)
		if task.kind.name == 'fitsin':
			data =  Plugin_fitsin.objects.filter(task = task)[0]
			grades = FirstQEval.objects.filter(fitsin = data)
			for g in grades:
				g.delete()
		elif task.kind.name == 'fitsout':
			data =  Plugin_fitsout.objects.filter(task = task)[0]
		elif task.kind.name == 'scamp':
			data =  Plugin_scamp.objects.filter(task = task)[0]
		elif task.kind.name == 'swarp':
			data =  Plugin_swarp.objects.filter(task = task)[0]
		elif task.kind.name == 'skel':
			data = None
		elif task.kind.name == 'sex':
			data =  Plugin_sex.objects.filter(task = task)[0]
		else:
			raise TypeError, 'Unknown data type to delete:' + task.kind.name

		for r in rels: r.delete()
		if data: data.delete()
		task.delete()
		success = True
	except Exception, e:
		return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

	resp = {
		'success' 	: success,
		'pluginId'  : task.kind.name,
		'results_output_dir' : task.results_output_dir,
	} 
	return HttpResponse(json.encode(resp), mimetype = 'text/plain')

@login_required
@profile
def get_condor_requirement_string(request):
	"""
	Get requirement string from saved policy
	"""
	try:
		name = request.POST['Name']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	error = req = '' 
	try:
		policy = CondorNodeSel.objects.filter(label = name, is_policy = True)[0]
		vms = get_condor_status()
		req = get_requirement_string(policy.nodeselection, vms)
	except Exception, e:
		error = e

	return HttpResponse(str({	'ReqStr': str(req), 
								'Error'	: str(error)
							}), mimetype = 'text/plain')


@login_required
@profile
def compute_requirement_string(request):
	"""
	Compute Condor's requirement string
	"""
	try:
		params = request.POST['Params']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	vms = get_condor_status()
	req = get_requirement_string(params, vms)

	return HttpResponse(str({'ReqString': str(req)}), mimetype = 'text/plain')

