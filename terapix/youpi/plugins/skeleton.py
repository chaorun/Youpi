# vim: set ts=4

#
# Mandatory data members
#
# def __getCondorSubmissionFile(self, request)
# def getOutputDirStats(self, outputDir)
# def getResultEntryDescription(self, task)
# def getSavedItems(self, request)
# def getTaskInfo(self, request)
# def process(self, request)
# def reprocessAllFailedProcessings(self, request)
# def saveCartItem(self, request)
#

import sys, os.path, re, time, string
import marshal, base64, zlib
from pluginmanager import ProcessingPlugin, PluginError, CondorSubmitError
from terapix.youpi.models import *
#
from terapix.settings import *

class Skeleton(ProcessingPlugin):
	"""
	This plugin does nothing but can serve as a base for writing processing plugins
	"""
	def __init__(self):
		ProcessingPlugin.__init__(self)
		#
		# REQUIRED members (see doc/writing_plugins/writing_plugins.pdf)
		#
		self.id = 'skel'
		self.optionLabel = 'Skeleton (DEMO)'
		self.description = 'Skeleton DEMO processing'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SKEL'
		self.index = 65535

		self.template = 'plugins/skeleton.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/skeleton_item_cart.html' 		# Template for custom rendering into the shopping cart
		self.jsSource = 'plugins/skeleton.js' 							# Custom javascript

		# Decomment to disable the plugin
		self.enable = PROCESSING_SKELETON_ENABLE

		# Will queue jobCount jobs on the cluster
		self.jobCount = 5
		self.command = '/usr/bin/uptime'

	def process(self, request):
		"""
		Do the job.
		1. Generates a condor submission file
		2. Executes condor_submit on that file
		3. Returns info related to ClusterId and number of jobs submitted
		"""
		post = request.POST

		cluster_ids = []
		error = condorError = '' 

		try:
			csfPath = self.__getCondorSubmissionFile(request)
			pipe = os.popen("/opt/condor/bin/condor_submit %s 2>&1" % csfPath) 
			data = pipe.readlines()
			pipe.close()
			cluster_ids.append(self.getClusterId(data))
		except CondorSubmitError, e:
				condorError = str(e)
		except Exception, e:
				error = "Error while processing item: %s" % e

		return {'ClusterIds': cluster_ids, 'Error': error, 'CondorError': condorError}

	def __getCondorSubmissionFile(self, request):
		"""
		Generates a suitable Condor submission for processing self.command jobs on the cluster.
		"""

		post = request.POST
		try:
			#
			# Retreive your POST data here
			#
			resultsOutputDir = post['ResultsOutputDir']
			itemId = str(post['ItemId'])
		except Exception, e:
				raise PluginError, "POST argument error. Unable to process data: %s" % e

		now = time.time()
		# Condor submission file
		csfPath = "/tmp/skel-%s.txt" % now
		csf = open(csfPath, 'w')

		# Content of YOUPI_USER_DATA env variable passed to Condor
		# At least those 3 keys
		userData = {'Descr' 			: str("%s trying %s" % (self.optionLabel, self.command)),		# Mandatory for Active Monitoring Interface (AMI)
					'Kind'	 			: self.id,														# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),											# Mandatory for AMI, WP
					'ItemID' 			: itemId, 
					'ResultsOutputDir'	: str(resultsOutputDir)											# Mandatory for WP
				} 

		# Builds realtime Condor requirements string
		req = self.getCondorRequirementString(request)

		# Base64 encoding + marshal serialization
		# Will be passed as argument 1 to the wrapper script
		try:
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
		except ValueError:
			raise ValueError, userData

		# Real command to perform here
		args = ''
		for x in range(self.jobCount):
			args += "arguments = %s %s\nqueue\n" % (encUserData, self.command)

		submit_file_path = os.path.join(TRUNK, 'terapix')

	 	# Generates CSF
		condor_submit_file = """
#
# Condor submission file
# Please not that this file has been generated automatically by Youpi
# http://clix.iap.fr/youpi/
#

# Plugin: %s

executable              = %s/wrapper_processing.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %s/settings.py, %s/DBGeneric.py, %s/NOP
initialdir				= %s
transfer_output_files   = NOP
# YOUPI_USER_DATA = %s
environment             = PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; YOUPI_USER_DATA=%s
log                     = /tmp/SKEL.log.$(Cluster).$(Process)
error                   = /tmp/SKEL.err.$(Cluster).$(Process)
output                  = /tmp/SKEL.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
# Computed Req string
%s
%s""" % (	self.description,
			os.path.join(submit_file_path, 'script'),
			submit_file_path, 
			os.path.join(submit_file_path, 'script'),
			submit_file_path, 
			os.path.join(submit_file_path, 'script'),
			userData, 
			base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
			req, 
			args )

		csf.write(condor_submit_file)
		csf.close()

		return csfPath


	def getTaskInfo(self, request):
		"""
		Returns information about a finished processing task. Used on the results page.
		"""

		post = request.POST
		try:
			taskid = post['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		task = Processing_task.objects.filter(id = taskid)[0]

		# Error log content
		if task.error_log:
			err_log = str(zlib.decompress(base64.decodestring(task.error_log)))
		else:
			err_log = ''

		#
		# Result log content, if any show be saved in a custom DB table for the plugin
		#
		# data = YourDjangoModel.objects.filter(task__id = taskid)[0]
		# if data.rlog:
		#	rlog = str(zlib.decompress(base64.decodestring(data.qflog)))
		# else:
		#	rlog = ''
		#

		return {	'TaskId'	: str(taskid),
					'Title' 	: str("%s" % self.description),
					'User' 		: str(task.user.username),
					'Success' 	: task.success,
					'Start' 	: str(task.start_date),
					'End' 		: str(task.end_date),
					'Duration' 	: str(task.end_date-task.start_date),
					'Log' 		: err_log
			}

	def getResultEntryDescription(self, task):
		"""
		Returns custom result entry description for a task.
		task: django object

		returned value: HTML tags allowed
		"""

		return "%s <tt>%s</tt>" % (self.optionLabel, self.command)

	def saveCartItem(self, request):
		"""
		Save cart item custom data to DB
		"""

		post = request.POST
		try:
			itemID = str(post['ItemID'])
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		items = CartItem.objects.filter(kind__name__exact = self.id)
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'Descr' : "Runs %d %s commands on the cluster" % (self.jobCount, self.command),
				 'resultsOutputDir' : resultsOutputDir }
		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user)
		cItem.data = sdata
		cItem.save()

		return "Item %s saved" % itemName

	def reprocessAllFailedProcessings(self, request):
		"""
		Returns parameters to allow reprocessing of failed processings
		"""
		pass

	def getSavedItems(self, request):
		"""
		Returns a user's saved items for this plugin 
		"""
		# TODO: Only items related to user's groups are returned.

		items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username'			: str(it.user.username),
						'descr' 			: str(data['Descr']),
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
						'name' 				: str(it.name) })

		return res
