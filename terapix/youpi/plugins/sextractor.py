# vim: set ts=4

import sys, os.path, re, time, string
import marshal, base64, zlib
import xml.dom.minidom as dom
from pluginmanager import Spica2Plugin, PluginError
from terapix.youpi.models import *
#
from terapix.settings import *

class Sextractor(Spica2Plugin):
	"""
	Sextractor plugin

	Source extractor for FITS image
	- Need FITS image
	- Produce catalogs
	"""
	def __init__(self):
		Spica2Plugin.__init__(self)
		#
		# REQUIRED members (see doc/writing_plugins/writing_plugins.pdf)
		#
		self.id = 'sex'
		self.optionLabel = 'Sources extractor'
		self.description = 'Sextractor'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SEX'
		self.index = 1

		# Main template, rendered in the processing page
		self.template = 'plugin_sextractor.html'
		# Template for custom rendering into the shopping cart
		self.itemCartTemplate = 'plugin_sextractor_item_cart.html'
		# Custom javascript
		self.jsSource = 'plugin_sextractor.js'

		self.jobCount = 10

	def saveCartItem(self, request):
		post = request.POST
		try:
			idList = post['IdList'].split(',')
			itemID = str(post['ItemID'])
			flagPath = post['FlagPath']
			weightPath = post['WeightPath']
			psfPath = post['PsfPath']
			config = post['Config']
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		items = CartItem.objects.filter(kind__name__exact = self.id)
		itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' 			: idList,
				 'flagPath' 		: flagPath,
				 'weightPath' 		: weightPath,
				 'psfPath' 			: psfPath,
				 'resultsOutputDir' : resultsOutputDir, 
				 'config' 			: config
				 }
		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user)
		cItem.data = sdata
		cItem.save()

		return "Item %s saved" % itemName

	def getSavedItems(self, request):
		"""
		Returns a user's saved items. 
		"""
		# TODO: Only items related to user's groups are returned.

		items = CartItem.objects.filter(kind__name__exact = self.id, user = request.user).order_by('-date')
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({
						'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username' 			: str(it.user.username),
						'idList' 			: [str(i) for i in data['idList']], 
						'flagPath' 			: str(data['flagPath']), 
						'weightPath' 		: str(data['weightPath']), 
						'psfPath' 			: str(data['psfPath']), 
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
						'name' 				: str(it.name),
						'config' 			: str(data['config'])
						})
		return res 

	def hasSavedItems(self):
		sItems = CartItem.object.filter(kind__name__exact = self.id)
		return 'mat1!'


	def format(self, data, format):
		try:
			if data:
				return format % data
			else:
				return None
		except TypeError:
			return None



	def process(self, request):
		"""
		Do the job.
		1. Generates a condor submission file
		2. Executes condor_submit on that file
		3. Returns info related to ClusterId and number of jobs submitted
		"""
		post = request.POST

		csfContent, csfPath = self.__getCondorSubmissionFile(request)

		f = open(csfPath, 'w')
		f.write(csfContent)
		f.close()

		pipe = os.popen("/opt/condor/bin/condor_submit %s 2>&1" % csfPath) 
		data = pipe.readlines()
		pipe.close()

		return self.getClusterId(data)

	def __getCondorSubmissionFile(self, request):
		"""
		Generates a suitable Condor submission for processing /usr/bin/uptime jobs on the cluster.
		"""

		post = request.POST
		try:
			#
			# Retreive your POST data here
			#
			idList = post['IdList'].split(',')
			itemId = str(post['ItemId'])
			flagPath = post['FlagPath']
			weightPath = post['WeightPath']
			psfPath = post['PsfPath']
			config = post['Config']
			sexId = post['sexId']
			resultsOutputDir = post['ResultsOutputDir']
			condorHosts = post['CondorHosts'].split(',')
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		now = time.time()
		# Condor submission file
		csfPath = "/tmp/skel-%s.txt" % now

		# Content of SPICA_USER_DATA env variable passed to Condor
		# At least those 3 keys
		userData = {'Descr' 		: str("%s trying /usr/bin/uptime" % self.optionLabel),		# Mandatory for Active Monitoring Interface (AMI)
					'Kind'	 		: self.id,												# Mandatory for AMI
					'UserID' 		: str(request.user.id)									# Mandatory for AMI
				} 

		# Base64 encoding + marshal serialization
		# Will be passed as argument 1 to the wrapper script
		try:
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
		except ValueError:
			raise ValueError, userData

		# Real command to perform here
		args = ''
		for x in range(self.jobCount):
			args += "arguments = %s /usr/bin/uptime\nqueue\n" % encUserData

		# Builds Condor requirements string
		req = self.getCondorRequirementString(condorHosts)

		submit_file_path = os.path.join(TRUNK, 'terapix')

	 	# Generates CSF
		condor_submit_file = """
#
# Condor submission file
# Please not that this file has been generated automatically by Spica2
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
# SPICA_USER_DATA = %s
environment             = PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; SPICA_USER_DATA=%s
log                     = /tmp/SKEL.log.$(Cluster).$(Process)
error                   = /tmp/SKEL.err.$(Cluster).$(Process)
output                  = /tmp/SKEL.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
requirements            = %s
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

		return (condor_submit_file, csfPath)


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



	def getConfigFileContent(self, request):
		post = request.POST
		try:
			name = str(post['Name'])
		except:
			raise PluginError, "Invalid POST parameters"

		# Updates entry
		try:
			config = ConfigFile.objects.filter(kind__name__exact = self.id, name = name)[0]
		except:
			raise PluginError, "No config file with that name: %s" % name

		return str(config.content)

	def saveConfigFile(self, request):
		"""
		Save configuration file to DB
		"""
		post = request.POST
		try:
			name = str(post['Name'])
			config = str(post['Content'])
		except Exception, e:
			raise PluginError, "Unable to save config file: no name given"

		try:
			# Updates entry
			m = ConfigFile.objects.filter(kind__name__exact = self.id, name = name)[0]
			m.content = config
		except:
			# ... or inserts a new one
			k = Processing_kind.objects.filter(name__exact = self.id)[0]
			m = ConfigFile(kind = k, name = name, content = config, user = request.user)

		m.save()

		return name + ' saved'


	def jobStatus(self, request):
		"""
		Parses XML output from Condor and returns a JSON object.
		Only Spica's related job are monitored. A Spica job must have 
		an environment variable named SPICA_USER_DATA which can contain
		serialized base64-encoded data to be parsed.

		nextPage: id of the page of 'limit' results to display
		"""

		try:
			nextPage = int(request.POST['NextPage'])
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		pipe = os.popen("/opt/condor/bin/condor_q -xml")
		data = pipe.readlines()
		pipe.close()

		res = []
		# Max jobs per page
		limit = 10

		# Removes first 3 lines (not XML)
		doc = dom.parseString(string.join(data[3:]))
		jNode = doc.getElementsByTagName('c')

		# Spica Condor job count
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

				elif a.getAttribute('n') == 'Args':
					fitsFile = str(a.firstChild.firstChild.nodeValue)
					jobData['FitsFile'] = fitsFile.split('/')[-1]
				
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
					# Try to look for SPICA_USER_DATA environment variable
					# If this is variable is found then this is a Spica's job so we can keep it
					env = str(a.firstChild.firstChild.nodeValue)
					if env.find('SPICA_USER_DATA') >= 0:
						m = re.search('SPICA_USER_DATA=(.*?)$', env)
						userData = m.groups(0)[0]	
						c = userData.find(';')
						if c > 0:
							userData = userData[:c]
						jobData['UserData'] = marshal.loads(base64.decodestring(str(userData)))

						if jobData['UserData'].has_key('Kind'):
							if jobData['UserData']['Kind'] == self.id:
								res.append(jobData)
								jobCount += 1

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

		return [res, jobCount, pageCount, nextPage]

	def cancelJob(self, request):
		"""
		Cancel a Job. POST arg used are clusterId and procId
		"""

		post = request.POST
		cluster = str(post['ClusterId'])
		proc = str(post['ProcId'])

		pipe = os.popen("/opt/condor/bin/condor_rm %s.%s" % (cluster, proc))
		data = pipe.readlines()
		pipe.close()

		return 'Job cancelled'


	def getConfigFileNames(self, request):
		# Updates entry
		configs = ConfigFile.objects.filter(kind__name__exact = self.id)
		if not len(configs):
			self.__saveDefaultConfigFileToDB(request)
			configs = ConfigFile.objects.filter(kind__name__exact = self.id)

		res = []
		for config in configs:
			res.append(str(config.name))

		return { 'configs' : res }

	def deleteConfigFile(self, request):
		"""
		Deletes configuration file to DB
		"""
		post = request.POST
		try:
			name = str(post['Name'])
		except Exception, e:
			raise PluginError, "Unable to delete config file: no name given"

		try:
			config = ConfigFile.objects.filter(kind__name__exact = self.id, name = name)[0]
		except:
			raise PluginError, "No config file with that name: %s" % name

		config.delete()

		return name + ' deleted'

	def __saveDefaultConfigFileToDB(self, request):
		"""
		Looks into DB (youpi_configfiles table) if an entry for a default configuration file 
		for SExtractor exits. If not creates one with the embedded default content.
		"""

		config = """

# Default configuration file for SExtractor 2.7.1
# EB 2008-05-19
#
 
#-------------------------------- Catalog ------------------------------------
 
CATALOG_NAME     test.cat       # name of the output catalog
CATALOG_TYPE     ASCII_HEAD     # NONE,ASCII,ASCII_HEAD, ASCII_SKYCAT,
                                # ASCII_VOTABLE, FITS_1.0 or FITS_LDAC
PARAMETERS_NAME  default.param  # name of the file containing catalog contents
 
#------------------------------- Extraction ----------------------------------
 
DETECT_TYPE      CCD            # CCD (linear) or PHOTO (with gamma correction)
DETECT_MINAREA   5              # minimum number of pixels above threshold
DETECT_THRESH    1.5            # <sigmas> or <threshold>,<ZP> in mag.arcsec-2
ANALYSIS_THRESH  1.5            # <sigmas> or <threshold>,<ZP> in mag.arcsec-2
 
FILTER           Y              # apply filter for detection (Y or N)?
FILTER_NAME      default.conv   # name of the file containing the filter
 
DEBLEND_NTHRESH  32             # Number of deblending sub-thresholds
DEBLEND_MINCONT  0.005          # Minimum contrast parameter for deblending
 
CLEAN            Y              # Clean spurious detections? (Y or N)?
CLEAN_PARAM      1.0            # Cleaning efficiency
 
MASK_TYPE        CORRECT        # type of detection MASKing: can be one of
                                # NONE, BLANK or CORRECT
 
#------------------------------ Photometry -----------------------------------
 
PHOT_APERTURES   5              # MAG_APER aperture diameter(s) in pixels
PHOT_AUTOPARAMS  2.5, 3.5       # MAG_AUTO parameters: <Kron_fact>,<min_radius>
PHOT_PETROPARAMS 2.0, 3.5       # MAG_PETRO parameters: <Petrosian_fact>,
                                # <min_radius>
 
SATUR_LEVEL      50000.0        # level (in ADUs) at which arises saturation
SATUR_KEY        SATURATE       # keyword for saturation level (in ADUs)
 
MAG_ZEROPOINT    0.0            # magnitude zero-point
MAG_GAMMA        4.0            # gamma of emulsion (for photographic scans)
GAIN             0.0            # detector gain in e-/ADU
GAIN_KEY         GAIN           # keyword for detector gain in e-/ADU
PIXEL_SCALE      1.0            # size of pixel in arcsec (0=use FITS WCS info)
 
#------------------------- Star/Galaxy Separation ----------------------------
 
SEEING_FWHM      1.2            # stellar FWHM in arcsec
STARNNW_NAME     default.nnw    # Neural-Network_Weight table filename
 
#------------------------------ Background -----------------------------------
 
BACK_SIZE        64             # Background mesh: <size> or <width>,<height>
BACK_FILTERSIZE  3              # Background filter: <size> or <width>,<height>
 
BACKPHOTO_TYPE   GLOBAL         # can be GLOBAL or LOCAL
 
#------------------------------ Check Image ----------------------------------
 
CHECKIMAGE_TYPE  NONE           # can be NONE, BACKGROUND, BACKGROUND_RMS,
                                # MINIBACKGROUND, MINIBACK_RMS, -BACKGROUND,
                                # FILTERED, OBJECTS, -OBJECTS, SEGMENTATION,
                                # or APERTURES
CHECKIMAGE_NAME  check.fits     # Filename for the check-image
 
#--------------------- Memory (change with caution!) -------------------------
 
MEMORY_OBJSTACK  3000           # number of objects in stack
MEMORY_PIXSTACK  300000         # number of pixels in stack
MEMORY_BUFSIZE   1024           # number of lines in buffer
 
#----------------------------- Miscellaneous ---------------------------------
 
VERBOSE_TYPE     NORMAL         # can be QUIET, NORMAL or FULL
WRITE_XML        N              # Write XML file (Y/N)?
XML_NAME         sex.xml        # Filename for XML output
"""

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		try:
			m = ConfigFile(kind = k, name = 'default', content = config, user = request.user)
			m.save()
		except:
			# Cannot save, already exits: do nothing
			pass

		return config
