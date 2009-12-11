"""

 (C) 2009 - Jonas Drewsen

 Environment, commandline, configuration file and default values
 configuration handling.

"""
import os, sys, os.path
from optparse import OptionParser
import ConfigParser

def get_config(setup, usage = None):
	"""
	Configuration options default values.
	Can be overridden using configuration file (default /etc/zbuild.conf)
	Can be overridden using environment variables
	Can be overridden using command line parameters
	Command line parameters is favoured in in front of config file which are
	favoured in front of environment vars

	The setup argument must be a list on the form:

	[ ( option, long-option, help text, default value) , ( ... ), ... ]

	e.g.

	[ ('l', 'log-filename', 'log file location', '/var/log/zbuild.log'), ... ]

	@return an object which has all the options defined as attributes

	"""
	
	# Handle command line args and config file params
	try:

		if usage is None:
			parser = OptionParser()
		else:
			parser = OptionParser(usage=usage)

		config_filename = ''

		for i in setup:
			if i[1] == 'config-filename':
				config_filename = os.environ.get('CONFIG_FILENAME', i[3])
			if type(i[3]) is bool:
				parser.add_option("-" + i[0], "--" + i[1], help=i[2], action="store_true", default=None, dest=i[1].replace('-','_'))
			else:
				parser.add_option("-" + i[0], "--" + i[1], help=i[2], default=None, dest=i[1].replace('-','_'))
				
		(options, args) = parser.parse_args()
				
		config = ConfigParser.SafeConfigParser()
		config.add_section('general')
		for i in setup:
			name = i[1].replace('-','_')
			config.set('general', name, str(i[3]))
		
		cfg = options.config_filename or config_filename
		if cfg is not None:
			if os.path.isfile(cfg):
				print "Using config file " + str(cfg)
				config.read(cfg)
	
		for i in setup:
			name = i[1].replace('-','_')
			if getattr(options, name) is None:

				# No command line argument for this field.
				# Use environment variable if present else
				# use the one from config file or default 

				if os.environ.has_key(name):
					setattr(options, name, os.environ[name])
				else:
					setattr(options, name, config.get('general', name))

		return options, args
	
	except SystemExit, e:
		if str(e) != "0":
			print "Error handling command line args"
			print str(e)
			sys.exit(0)
		return None, []
