# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil -*- 
"""

   2009 (C) - Jonas Drewsen

   Configuration handling from environment variables, command line
   arguments and configuration files.
   
"""

import os, sys
from optparse import OptionParser, IndentedHelpFormatter
import ConfigParser

class RawEpilogIndentedHelpFormatter(IndentedHelpFormatter):
    """
    A normal optparse.IndentedHelpFormatter where the epilog
    is not formatted but used as is.
    """
    def format_epilog(self, epilog):
        return epilog or ""

def get_config(setup, setup2 = [], **argv):
    """
    Configuration options default values.
    Can be overridden using configuration file 
    Can be overridden using environment variables
    Can be overridden using command line parameters
    Command line parameters is favoured in in front of config file which are
    favoured in front of environment vars
    
    The setup argument must be a list on the form:
    
    [ ( option, long-option, help text, default value) , ( ... ), ... ]
    
    e.g.
    
    [ ('l', 'log-filename', 'log file location', '/var/log/mysoftware.log'), ... ]
    
    setup2 is an additional but optional list on the same format as
    the setup parameter

    @return an object which has all the options defined as attributes
    
    """

    setup.extend(setup2)
    
    # Handle command line args and config file params
    try:
        
        argv['formatter'] = RawEpilogIndentedHelpFormatter()
		parser = OptionParser(**argv)
        config_filename = ''
        
        for i in setup:
            if i[1] == 'config-filename':
                config_filename = os.environ.get('CONFIG_FILENAME', i[3])
            help_text = i[2]

            # add possible values if this is a enumeration
            if len(i) > 4:
                help_text = "[" + (", ".join(map(lambda a: str(a), i[4]))) + "]"

            if len(i) <= 3:
                # simple flag
                parser.add_option("-" + i[0], "--" + i[1], help=help_text, action="store_true",
                                  default=False, dest=i[1].replace('-','_'))
            else:
                # an option with an argument

                # Add default value to help text if present
                help_text = help_text + " (default " + str(i[3]) + ")" 
                parser.add_option("-" + i[0], "--" + i[1], help=help_text,
                                  default=None, dest=i[1].replace('-','_'))

        (options, args) = parser.parse_args()
                
        config = ConfigParser.SafeConfigParser()
        config.add_section('general')
        for i in setup:
            name = i[1].replace('-','_')
            if len(i) > 3:
                config.set('general', name, str(i[3]))
            else:
                config.set('general', name, "False")
		
        cfg = options.config_filename or config_filename
        if cfg is not None:
			if getattr(options,'verbose',0) >= 1:
				print "Using config file " + str(cfg)
            config.read(cfg)
	
        for i in setup:
            name = i[1].replace('-','_')
			val = getattr(options, name)
            if val is None:

                # No command line argument for this field.
                # Use environment variable if present else
                # use the one from config file or default 

                if os.environ.has_key(name.upper()):
                    val = os.environ[name.upper()]
                else:
					val = config.get('general', name)
				try:
                    typ = bool
                    if len(i) > 3:
                        typ = type(i[3])
                    cval = typ(val)
					setattr(options, name, cval)
				except:
					print "Error casting option '%s' with the value '%s' to type %s" % (name, val, str(typ))

			try:

				# parse true and false values since they are not
				# castable directly
				if str(val).lower() == 'true':
					val = True
				elif str(val).lower() == 'false':
					val = False

                typ = bool
                if len(i) > 3:
                    typ = type(i[3])
                cval = typ(val)

                #if len(i) > 3:
                #    print ("opt %s is %s %s %s " % 
                #             (str(name), cval, str(type(cval)), str(type(i[3]))))

				# If the values is restricted to an specific set then
				# verify that it is actually within that set
				if len(i) >= 5 and cval not in i[4]:
					vals = ",".join(map(lambda a: str(a), i[4]))
                    errmsg = "Error: value must be one of (" + vals + ") for option '%s' with the value '%s' to type %s" % (name, val, str(type(i[3])))
                    log.error(errmsg)
					print errmsg
				else:
					setattr(options, name, cval)
			except:
				print "Error casting option '%s' with the value '%s' to type %s" % (name, val, str(typ))
				
        import __builtin__
        __builtin__.OPTIONS = options
        __builtin__.ARGS = args
        return options, args
	
    except SystemExit, e:
        if str(e) != "0":
            print "Error handling command line args"
        sys.exit(0)

