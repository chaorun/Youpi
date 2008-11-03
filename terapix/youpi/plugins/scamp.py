# vim: set ts=4

import sys, os.path, time, string
import xml.dom.minidom as dom
import marshal, base64, zlib
from types import *
from pluginmanager import Spica2Plugin, PluginError
from terapix.youpi.models import *
#
from terapix.settings import *

class Scamp(Spica2Plugin):
	"""	
	Class: Scamp
	Plugin for Scamp.
	
	Astro-Photo Calibration.
	- Needs "ldac" catalogs from Sextractor
	- Computes astrometric/Photometric solution from FITS images sequence
	"""	
	def __init__(self):
		Spica2Plugin.__init__(self)

		self.id = 'scamp'
		self.optionLabel = 'Astro-Photo calibration'
		self.description = 'Scamp'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SCAMP'
		self.index = 20

		# Main template, rendered in the processing page
		self.template = 'plugin_scamp.html'
		# Template for custom rendering into the shopping cart
		self.itemCartTemplate = 'plugin_scamp_item_cart.html'
		# Custom javascript
		self.jsSource = 'plugin_scamp.js'

		# Decomment to disable the plugin
		#self.enable = False

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

	def __saveDefaultConfigFileToDB(self, request):
		"""
		Looks into DB (youpi_configfiles table) if an entry for a default configuration file 
		for scamp exits. If not creates one with the embedded default content.
		"""

		config = """
# Default configuration file for SCAMP 1.4.7-MP
# EB 2008-08-02
#
 
#----------------------------- Field grouping ---------------------------------
 
FGROUP_RADIUS          1.0             # Max dist (deg) between field groups
 
#---------------------------- Reference catalogs ------------------------------
 
REF_SERVER         cocat1.u-strasbg.fr # Internet addresses of catalog servers
ASTREF_CATALOG         USNO-B1         # NONE, FILE, USNO-A1, USNO-A2, USNO-B1,
                                       # GSC-1.3, GSC-2.2, UCAC-1, UCAC-2,
                                       # NOMAD-1, 2MASS, DENIS-3,
                                       # SDSS-R3, SDSS-R5 or SDSS-R6
ASTREF_BAND            DEFAULT         # Photom. band for astr.ref.magnitudes
                                       # or DEFAULT, BLUEST, or REDDEST
ASTREFCAT_NAME         astrefcat.cat   # Local astrometric reference catalogs
ASTREFCENT_KEYS        X_WORLD,Y_WORLD # Local ref.cat.centroid parameters
ASTREFERR_KEYS         ERRA_WORLD, ERRB_WORLD, ERRTHETA_WORLD
                                       # Local ref.cat.error ellipse parameters
ASTREFMAG_KEY          MAG             # Local ref.cat.magnitude parameter
SAVE_REFCATALOG        N               # Save ref catalogs in FITS-LDAC format?
REFOUT_CATPATH         .               # Save path for reference catalogs
 
#--------------------------- Merged output catalogs ---------------------------
 
MERGEDOUTCAT_NAME      scamp.cat       # Merged output catalog filename
MERGEDOUTCAT_TYPE      NONE            # NONE, ASCII_HEAD, ASCII, FITS_LDAC
 
#----------------------------- Pattern matching -------------------------------
 
MATCH                  Y               # Do pattern-matching (Y/N) ?
MATCH_NMAX             0               # Max.number of detections for MATCHing
                                       # (0=auto)
PIXSCALE_MAXERR        1.2             # Max scale-factor uncertainty
POSANGLE_MAXERR        5.0             # Max position-angle uncertainty (deg)
POSITION_MAXERR        1.0             # Max positional uncertainty (arcmin)
MATCH_RESOL            0               # Matching resolution (arcsec); 0=auto
MATCH_FLIPPED          N               # Allow matching with flipped axes?
MOSAIC_TYPE            UNCHANGED       # UNCHANGED, SAME_CRVAL, SHARE_PROJAXIS,
                                       # FIX_FOCALPLANE or LOOSE
 
#---------------------------- Cross-identification ----------------------------
 
CROSSID_RADIUS         2.0             # Cross-id initial radius (arcsec)
 
#---------------------------- Astrometric solution ----------------------------
 
SOLVE_ASTROM           Y               # Compute astrometric solution (Y/N) ?
ASTRINSTRU_KEY         FILTER,QRUNID   # FITS keyword(s) defining the astrom
STABILITY_TYPE         INSTRUMENT      # EXPOSURE, GROUP, INSTRUMENT or FILE
CENTROID_KEYS          XWIN_IMAGE,YWIN_IMAGE # Cat. parameters for centroiding
CENTROIDERR_KEYS       ERRAWIN_IMAGE,ERRBWIN_IMAGE,ERRTHETAWIN_IMAGE
                                       # Cat. params for centroid err ellipse
DISTORT_KEYS           XWIN_IMAGE,YWIN_IMAGE # Cat. parameters or FITS keywords
DISTORT_GROUPS         1,1             # Polynom group for each context key
DISTORT_DEGREES        3               # Polynom degree for each group
 
#---------------------------- Photometric solution ----------------------------
 
SOLVE_PHOTOM           Y               # Compute photometric solution (Y/N) ?
MAGZERO_OUT            0.0             # Magnitude zero-point(s) in output
MAGZERO_INTERR         0.01            # Internal mag.zero-point accuracy
MAGZERO_REFERR         0.03            # Photom.field mag.zero-point accuracy
PHOTINSTRU_KEY         FILTER          # FITS keyword(s) defining the photom.
MAGZERO_KEY            PHOT_C          # FITS keyword for the mag zero-point
EXPOTIME_KEY           EXPTIME         # FITS keyword for the exposure time (s)
AIRMASS_KEY            AIRMASS         # FITS keyword for the airmass
EXTINCT_KEY            PHOT_K          # FITS keyword for the extinction coeff
PHOTOMFLAG_KEY         PHOTFLAG        # FITS keyword for the photometry flag
PHOTFLUX_KEY           FLUX_AUTO       # Catalog param. for the flux measurement
PHOTFLUXERR_KEY        FLUXERR_AUTO    # Catalog parameter for the flux error
 
#------------------------------- Check-plots ----------------------------------
 
CHECKPLOT_DEV          PNG             # NULL, XWIN, TK, PS, PSC, XFIG, PNG,
                                       # JPEG or AQT
CHECKPLOT_TYPE         FGROUPS,DISTORTION,ASTR_INTERROR2D,ASTR_INTERROR1D,ASTR_REFERROR2D,ASTR_REFERROR1D,ASTR_CHI2,PHOT_ERROR
CHECKPLOT_NAME         fgroups,distort,astr_interror2d,astr_interror1d,astr_referror2d,astr_referror1d,astr_chi2,psphot_error # Check-plot filename(s)
 
#------------------------------ Miscellaneous ---------------------------------
 
SN_THRESHOLDS          10.0,100.0      # S/N thresholds (in sigmas) for all and
                                       # high-SN sample
FWHM_THRESHOLDS        0.0,100.0       # FWHM thresholds (in pixels) for sources
AHEADER_SUFFIX         .ahead          # Filename extension for additional
                                       # INPUT headers
HEADER_SUFFIX          .head           # Filename extension for OUTPUT headers
VERBOSE_TYPE           NORMAL          # QUIET, NORMAL, LOG or FULL
WRITE_XML              Y               # Write XML file (Y/N)?
XML_NAME               scamp.xml       # Filename for XML output
NTHREADS               0               # Number of simultaneous threads for
                                       # the SMP version of SCAMP
                                       # 0 = automatic
"""

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		try:
			m = ConfigFile(kind = k, name = 'default', content = config, user = request.user)
			m.save()
		except:
			# Cannot save, already exits: do nothing
			pass

		return config

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

	def getSavedItems(self, request):
		"""
		Returns a user's saved items. 
		"""

		# per-user items
		items = CartItem.objects.filter(kind__name__exact = self.id, user = request.user).order_by('-date')
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username' 			: str(it.user.username),
						#'idList' 			: [str(i) for i in data['idList']], 
						'idList' 			: str(data['idList']), 
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
						'name' 				: str(it.name),
						'config' 			: str(data['config'])})

		return res

	def saveCartItem(self, request):
		"""
		Serialize cart item into DB.
	
		@param request Django HTTP request object
		@return Name of saved item when successful
		"""
		post = request.POST
		try:
			idList = eval(post['IdList'])
			itemID = str(post['ItemID'])
			config = post['Config']
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, ("POST argument error. Unable to process data: %s" % e)

		items = CartItem.objects.filter(kind__name__exact = self.id)
		itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' : idList, 
				 'resultsOutputDir' : resultsOutputDir, 
				 'config' : config }
		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user)
		cItem.data = sdata
		cItem.save()

		return "Item %s saved" % itemName

	def process(self, request):
		"""
		Do the job.
		1. Generates a condor submission file
		2. Executes condor_submit on that file
		3. Returns info related to ClusterId and number of jobs submitted
		"""

		try:
			idList = eval(request.POST['IdList'])	# List of lists
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		post = request.POST
		for imgList in idList:
			if not len(imgList):
				continue
			csfPath = self.__getCondorSubmissionFile(request, imgList)
			pipe = os.popen("/opt/condor/bin/condor_submit %s 2>&1" % csfPath) 
			data = pipe.readlines()
			pipe.close()

		# FIXME: returns only latest data
		return self.getClusterId(data)

	def __getCondorSubmissionFile(self, request, idList):
		"""
		Generates a suitable Condor submission for processing images on the cluster.

		Note that the scampId variable is used to bypass the config variable: it allows to get the 
		configuration file content for an already processed image rather by selecting content by config 
		file name.
		"""

		post = request.POST
		try:
			itemId = str(post['ItemId'])
			condorHosts = post['CondorHosts'].split(',')
			config = post['Config']
			scampId = post['ScampId']
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		#
		# Config file selection and storage.
		#
		# Rules: 	if scampId has a value, then the config file content is retreive
		# 			from the existing scamp processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
		#
		try:
			if len(scampId):
				config = Plugin_scamp.objects.filter(id = int(scampId))[0]
				content = str(zlib.decompress(base64.decodestring(config.qfconfig)))
			else:
				config = ConfigFile.objects.filter(kind__name__exact = self.id, name = config)[0]
				content = config.content
		except Exception, e:
			raise PluginError, "Unable to use a suitable config file: %s" % e

		if not len(condorHosts):
			raise PluginError, "No cluster host supplied. Unable to generate a condor submission file."

		now = time.time()
		customrc = os.path.join('/tmp/', "scamp-%s.rc" % now)
		scamprc = open(customrc, 'w')
		scamprc.write(content)
		scamprc.close()

		# Condor submission file
		csfPath = "/tmp/scamp-condor-%s.txt" % now

		images = Image.objects.filter(id__in = idList)
		# Content of SPICA_USER_DATA env variable passed to Condor
		userData = {'ItemID' 			: itemId, 
					'ScampId' 			: str(scampId),
					'Warnings' 			: {}, 
					'SubmissionFile'	: csfPath, 
					'ConfigFile' 		: customrc, 
					'Descr' 			: '',									# Mandatory for Active Monitoring Interface (AMI) - Will be filled later
					'Kind'	 			: self.id,								# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),					# Mandatory for AMI, WP
					'ResultsOutputDir'	: str(resultsOutputDir),				# Mandatory for WP
					'Config' 			: str(post['Config'])} 

		step = 0 							# At least step seconds between two job start

		csf = open(csfPath, 'w')

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
executable              = %s/wrapper_processing.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %s/settings.py, %s/DBGeneric.py, %s, %s/NOP
initialdir				= %s
transfer_output_files   = NOP
log                     = /tmp/SCAMP.log.$(Cluster).$(Process)
error                   = /tmp/SCAMP.err.$(Cluster).$(Process)
output                  = /tmp/SCAMP.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
requirements            = %s
""" % (	os.path.join(submit_file_path, 'script'),
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		customrc,
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		req )

		csf.write(condor_submit_file)

		ldac_files = self.getLDACPathsFromImageSelection(request, idList)
		# Keep data path only
		ldac_files = [dat[1] for dat in ldac_files]

		#
		# $(Cluster) and $(Process) variables are substituted by Condor at CSF generation time
		# They are later used by the wrapper script to get the name of error log file easily
		#
		userData['ImgID'] = idList
		userData['Descr'] = str("%s from %d SExtractor catalogs" % (self.optionLabel, len(images)))		# Mandatory for Active Monitoring Interface (AMI)
		userData['LDACFiles'] = ldac_files

		#
		# Delaying job startup will prevent "Too many connections" MySQL errors
		# and will decrease the load of the node that will receive all qualityFITS data
		# results (PROCESSING_OUTPUT) back. Every job queued will be put to sleep StartupDelay 
		# seconds
		#
		userData['StartupDelay'] = step
		userData['Warnings'] = {}

		# Base64 encoding + marshal serialization
		# Will be passed as argument 1 to the wrapper script
		try:
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
		except ValueError:
			raise ValueError, userData

		scamp_params = "-XSL_URL %s/scamp.xsl" % os.path.join(	WWW_SCAMP_PREFIX, 
																		request.user.username, 
																		userData['Kind'], 
																		userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:] )
		condor_submit_entry = """
arguments               = %s /usr/local/bin/condor_transfert.pl /usr/local/bin/scamp %s %s -c %s 2>/dev/null
# SPICA_USER_DATA = %s
environment             = TPX_CONDOR_UPLOAD_URL=%s; PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; SPICA_USER_DATA=%s
queue""" %  (	encUserData, 
				scamp_params,
				string.join(ldac_files), 
				os.path.basename(customrc),
				userData, 
				FTP_URL + resultsOutputDir,
				base64.encodestring(marshal.dumps(userData)).replace('\n', '') )

		csf.write(condor_submit_entry)
		csf.close()

		return csfPath

	def checkForSelectionLDACData(self, request, imgList = None):
		"""
		Check if every image in this selection has associated LDAC data.
		Policy: only the lastest successful qfits-in of current logged-in user is looked for.

		@return Dictionnary {'missingLDAC' : list of images names without LDAC data, 'tasksIds' : list of matching tasks}
		"""

		post = request.POST
		if imgList:
			idList = imgList
		else:
			try:
				idList = request.POST['IdList'].split(',')
			except Exception, e:
				raise PluginError, "POST argument error. Unable to process data."

		tasksIds = []
		missing = []
		imgList = Image.objects.filter(id__in = idList)
		curTask = None

		for img in imgList:
			rels = Rel_it.objects.filter(image = img)
			if not rels:
				missing.extend([str(img.name)])
				continue

			relTaskIds = [rel.task.id for rel in rels]

			# Valid task is only the lastest successful qfits-in of current logged-in user
			tasks = Processing_task.objects.filter(	id__in = relTaskIds, 
													user = request.user, 
													kind__name__exact = 'fitsin',
													success = True).order_by('-end_date')

			if not tasks:
				missing.append(str(img.name))
				continue

			tasksIds.append(int(tasks[0].id))

		return {'missingLDACImages' : missing, 'tasksIds' : tasksIds}

	def getLDACPathsFromImageSelection(self, request, imgList = None):
		"""
		Compute LDAC data path for a given image selection

		@return List of paths to LDAC files
		"""

		post = request.POST
		try:
			idList = request.POST['IdList'].split(',')
			checks = self.checkForSelectionLDACData(request)
		except Exception, e:
			if imgList:
				idList = imgList
				checks = self.checkForSelectionLDACData(request, idList)
			else:
				raise PluginError, "POST argument error. Unable to process data."

		ldac_files = []
		tasks = Processing_task.objects.filter(id__in = checks['tasksIds'])

		for task in tasks:
			img = Rel_it.objects.filter(task = task)[0].image
			ldac_files.append([int(img.id), str(os.path.join(task.results_output_dir, img.name, 'qualityFITS', img.name + '.ldac'))])

		return ldac_files

	def getResultEntryDescription(self, task):
		"""
		Returns custom result entry description for a task.
		task: django object

		returned value: HTML tags allowed
		"""

		img = Rel_it.objects.filter(task = task)[0].image
		return "%s of image <b>%s</b>" % (self.optionLabel, img.name)

	def getTaskInfo(self, request):
		"""
		Returns information about a finished processing task
		"""
		post = request.POST
		try:
			taskid = post['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		task = Processing_task.objects.filter(id = taskid)[0]
		data = Plugin_scamp.objects.filter(task__id = taskid)[0]

		if task.error_log:
			log = str(zlib.decompress(base64.decodestring(task.error_log)))
		else:
			log = ''

		if data.log:
			scamplog = str(zlib.decompress(base64.decodestring(data.log)))
		else:
			scamplog = ''

		# Get related images
		rels = Rel_it.objects.filter(task__id = taskid)
		imgs = []
		for r in rels:
			imgs.append(r.image)

		# Looks for groups of scamps
		scampHistory = Rel_it.objects.filter(image__in = imgs, task__kind__name = self.id).order_by('task')
		old_task = scampHistory[0].task
		gtasks= [old_task]
		for h in scampHistory:
			task = h.task
			if old_task != task:
				# Other scamp
				gtasks.append(task)
				old_task = task

		history = []
		for st in gtasks:
			history.append({'User' 			: str(st.user.username),
							'Success' 		: st.success,
							'Start' 		: str(st.start_date),
							'Duration' 		: str(st.end_date-st.start_date),
							'Hostname' 		: str(st.hostname),
							'TaskId'		: str(st.id),
							})

		return {	'TaskId'			: str(taskid),
					'Title' 			: str("%s processing" % self.description),
					'User' 				: str(task.user.username),
					'Hostname'			: str(task.hostname),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'WWW' 				: str(data.www),
					'LDACFiles'			: marshal.loads(base64.decodestring(data.ldac_files)),
					'Duration' 			: str(task.end_date-task.start_date),
					'ResultsOutputDir' 	: str(task.results_output_dir),
					'Log' 				: log,
					'ResultsLog'		: scamplog,
					'Config' 			: str(zlib.decompress(base64.decodestring(data.config))),
					'History'			: history,
			}

