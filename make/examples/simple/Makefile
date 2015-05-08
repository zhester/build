##############################################################################
#
#   Makefile
#
#   Note: This assumes you have at least one header (.h) file in your project.
#   If that is not the case, remove the "*.h" dependency from the rule to
#   build object files.  Or, just start using headers like a normal person.
#
##############################################################################

# Basic compile environment settings
CC = ./maker.py
CFLAGS = -Wall
LD = $(CC)
LDFLAGS = $(CFLAGS)
AR = ./maker.py
ARFLAGS = -cr
SHELL = /usr/bin/sh

# Add debug symbols for any debug target.
debug: CFLAGS += -ggdb
debug: LDFLAGS += -ggdb

# Detect build environment.
UNAME := $(shell uname)

# Base name of the project and final binary
PROJ := $(shell basename `pwd`)

# Project source files
SOURCES := $(wildcard *.c)

# Build directory
BLDDIR = build

# Derive object targets from source files
OBJECTS := $(patsubst %.c, $(BLDDIR)/%.o, $(SOURCES))

# Default target
all: $(BLDDIR)/$(PROJ)

# How to build the project binary
$(BLDDIR)/$(PROJ): $(OBJECTS)
	$(LD) $(LDFLAGS) -o $@ $(OBJECTS)

# How to build object files
$(BLDDIR)/%.o: %.c *.h | $(BLDDIR)
	$(CC) $(CFLAGS) -o $@ -c $<

# Make sure there's an output directory.
$(BLDDIR):
	mkdir -p $(BLDDIR)

# How to clean the output files
clean:
	rm -rf $(BLDDIR)

