#!/usr/bin/env python


"""
Makefile Debugging Helper Script
================================

This script is intended to be used in place of a file building program (e.g.
your compiler).  It will capture the arguments passed to it, and generate
reports (to a log file or stdout) to assist with how your real program is
being used by the build system (e.g. make).

In an attempt to simulate an actual compiler, it will build artifacts to
assist with debugging prerequisite specifications.  Keep this in mind if you
don't want to overwrite any existing artifacts in your project.
"""


import hashlib
import json
import os
import re
import sys


__version__ = '0.0.0'

#=============================================================================

# Default Configuration
config = {

    # how to pretend to be a compiler
    'compiler' : [

        # flag-specified debug switch
        [ 'debug', '-g', { 'type' : 'switch' } ],

        # flag-specified optimization (switch)
        [ 'optimize', '-O(.*)', {} ],

        # flag-specified warnings
        [ 'warn', '-W(.*)', {} ],

        # library modules
        [ 'lib', '-l(.+)', { 'count' : '*' } ],

        # library search paths
        [ 'libsearch', '-L(.+)', { 'count' : '*' } ],

        # include search paths
        [ 'incsearch', '-I(.+)', { 'count' : '*' } ],

        # flag-specified intermediate compile switch
        [ 'compile', '-c', { 'type' : 'switch' } ],

        # flag-specified output argument
        [ 'output', '-o', { 'type' : 'next', 'default' : 'a.out' } ],

        # all unknown options
        [ 'unknown', '-(.+)', { 'count' : '*' } ],

        # positional input arguments
        [ 'input', None, { 'count' : '+' } ]
    ]
}


#=============================================================================
class DictObject( object ):
    """
    Object-like container that can be initialized with a dictionary.
    """

    #=========================================================================
    def __init__( self, **kwargs ):
        """
        Initializes a DictObject object.
        """
        self.__dict__.update( kwargs )


#=============================================================================
class Cargs( object ):
    """
    Compiler Argument Handler/"Parser"
    I'm a fan of the built-in argparse module, but it won't let me easily
    emulate the standard `cc` argument format (e.g. "-Wall", "-O3", etc).
    This does only enough "parsing" to help the script pretend to be a C
    compiler console.
    """

    #=========================================================================
    def __init__( self ):
        """
        Initializes a Cargs object.
        """
        self.arguments  = []
        self._opt_specs = []
        self._pos_specs = []
        self._values    = {}


    #=========================================================================
    def add_argument( self, key, pattern = None, **kwargs ):
        """
        Adds an argument specification to the object state.
        """

        # pattern given, create an option argument
        if pattern is not None:

            # unspecified list option argument
            if 'count' in kwargs:

                # look for self-capturing option
                match = re.match( r'[^(]*\([^)]+\).*', pattern )
                if match is not None:
                    kwargs.setdefault( 'type', 1 )

                # otherwise, assume this captures next value
                else:
                    kwargs.setdefault( 'type', 'next' )

            # unspecified scalar option arguments are assumed to be switches
            else:
                kwargs.setdefault( 'type', 'switch' )

            # switch-type options get an automatic default
            if kwargs[ 'type' ] == 'switch':
                kwargs.setdefault( 'default', False )

            # check for number specification
            if 'count' in kwargs:
                default = kwargs.get( 'default', [] )
            else:
                default = kwargs.get( 'default', None )

            # set the initial value
            self._values[ key ] = default

            # add the option argument
            self._opt_specs.append( [ key, pattern, kwargs ] )

        # no pattern given, create a positional argument
        else:

            # check for number specification
            if 'count' in kwargs:
                default = kwargs.get( 'default', [] )
            else:
                default = kwargs.get( 'default', None )

            # set the initial value
            self._values[ key ] = default

            # add the positional argument
            self._pos_specs.append( [ key, None, kwargs ] )


    #=========================================================================
    def get( self, key ):
        """
        Retrieves a value for the requested argument.
        """
        if key not in self._values:
            raise ValueError( 'Invalid argument key "{}".'.format( key ) )
        return self._values[ key ]


    #=========================================================================
    def load( self, arguments = None ):
        """
        Loads the argument list into object state.
        """

        # determine list of arguments to load
        if arguments is None:
            arguments = sys.argv[ 1 : ]
        num_arguments = len( arguments )

        # index into positional argument specifications
        pos_index = 0

        # scan through each argument in the argument list
        for position in range( num_arguments ):

            # flag to indicate if this argument has been captured
            captured = False

            # value of current argument
            arg = arguments[ position ]

            # check for an option argument
            for key, patt, conf in self._opt_specs:

                # test this option's pattern
                match = re.match( patt, arg )
                if match is not None:

                    # see if this argument captures the next as its value
                    if conf[ 'type' ] == 'next':
                        if position >= ( num_arguments - 1 ):
                            raise ValueError(
                                'No value given for "{}" argument.'.format(
                                    key
                                )
                            )
                        position += 1
                        value = arguments[ position ]

                    # switch-style arguments
                    elif conf[ 'type' ] == 'switch':
                        value = True

                    # self-capturing arguments (capture offset in type)
                    else:
                        value = match.group( conf[ 'type' ] )

                    # set the value for this argument
                    self._set( ( key, patt, conf ), value )

                    # continue to next argument
                    captured = True
                    break

            # this is a positional argument
            if captured == False:

                # current positional specifier
                key, patt, conf = spec = self._pos_specs[ pos_index ]

                # set the value for this argument
                self._set( spec, arg )

                # check for lists of positional argument lists
                if 'count' in conf:

                    # fixed-length value list
                    if type( conf[ 'count' ] ) is int:

                        # see if the value list is complete
                        if len( self._values[ key ] ) >= conf[ 'count' ]:
                            pos_index += 1

                # single-value positional argument
                else:

                    # move to the next positional argument
                    pos_index += 1

        ### ZIH - validate here

        # store the list of arguments we loaded for future reference
        self.arguments = arguments

        # return an object container for the arguments
        return DictObject( **self._values )


    #=========================================================================
    def _set( self, spec, value ):
        """
        Set or append an argument value.
        """
        key, patt, conf = spec
        if 'count' in conf:
            self._values[ key ].append( value )
        else:
            self._values[ key ] = value


#=============================================================================
class Helper( object ):
    """
    Helper Container Implementation
    """

    #=========================================================================
    def __init__( self, out = None ):
        """
        Initializes a Helper object.
        """
        self._out = out if out is not None else sys.stdout


    #=========================================================================
    def make( self, arguments = None ):
        """
        Executes the helper as if it was being called as a compiler.
        """

        # no arguments given, assume the command-line arguments are needed
        if arguments is None:
            arguments = sys.argv

        # set up a compiler argument handler
        parser = Cargs()

        # configure the argument parser
        for key, patt, conf in config[ 'compiler' ]:
            parser.add_argument( key, patt, **conf )

        # load the argument list
        args = parser.load()

        # write input hashes to output file
        with open( args.output, 'w' ) as ofh:
            for inp in args.input:
                with open( inp, 'r' ) as ifh:
                    ofh.write(
                        '{} {}\n'.format(
                            hashlib.sha1( ifh.read() ).hexdigest(),
                            inp
                        )
                    )

        # report what was done (ZIH - could use some more detail/results)
        event = {
            'arguments' : arguments
        }
        self._out.write( '{}\n'.format( json.dumps( event, indent = 4 ) ) )

        # return success
        return 0


#=============================================================================
def make( arguments = None ):
    """
    Provides a simplified interface to the helper implementation.

    @param arguments A list of command-line arguments
    @return          The return code for the shell (0 = success)
    """
    logfile = re.sub( r'\.py$', '.log', os.path.basename( __file__ ) )
    status  = 1
    with open( logfile, 'w' ) as fh:
        helper = Helper( fh )
        status = helper.make( arguments )
    return status


#=============================================================================
if __name__ == "__main__":

    # execute the helper with all defaults
    sys.exit( make() )

