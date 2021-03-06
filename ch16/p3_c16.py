#!/usr/bin/env python3

# Chapter 16 -- Coping with the Command Line
# ------------------------------------------------------------------------

# ..  sectnum::
#
# ..  contents::
#

# Preliminary Definitions
# ========================

# Import the simulation model we've been using.
# Plus a handy validation function that assures the output is sensible.
# And logging, since we'll use it for some examples.
# ::

from simulation_model import *
from p2_c13 import check

import logging
from pprint import pprint
import os

# Command-line parsing
# =======================

# Global version
# ::

import argparse
__version__= "3.3.2"

# Step 1: Parser.
# ::

parser = argparse.ArgumentParser( description="Simulate Blackjack", add_help=False,
formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Step 2: Arguments.

# Simple on-off options
# ::

parser.add_argument( '-v', '--verbose', action='store_true', default=False )
parser.add_argument( '--debug', action='store_const', const=logging.DEBUG, default=logging.INFO, dest="logging_level" )

# Options with arguments
# ::

parser.add_argument( "--dealerhit", action="store", default="Hit17", choices=['Hit17', 'Stand17'], dest='dealer_rule')
parser.add_argument( "--resplit", action="store", default="ReSplit", choices=['ReSplit', 'NoReSplit', 'NoReSplitAces'], dest='split_rule')

parser.add_argument( "--decks", action="store", default=6, type=int, help="Decks to deal" )
parser.add_argument( "--limit", action="store", default=50, type=int )
parser.add_argument( "--payout", action="store", default="(3,2)" )

parser.add_argument( "-p", "--playerstrategy", action="store", default="SomeStrategy", choices=["SomeStrategy", "AnotherStrategy"], dest='player_rule')
parser.add_argument( "-b", "--bet", action="store", default="Flat", choices=["Flat", "Martingale", "OneThreeTwoSix"], dest='betting_rule')
parser.add_argument( "-r", "--rounds", action="store", default=100, type=int )
parser.add_argument( "-s", "--stake", action="store", default=50, type=int )

parser.add_argument( "--samples", action="store",
    default=int(os.environ.get("SIM_SAMPLES",100)),
    type=int, help="Samples to generate" )

# Arguments
# ::

parser.add_argument( "outputfile", action="store", metavar="output" ) # required

# Version and help
# ::

parser.add_argument( "-V", "--version", action="version", version=__version__ )
parser.add_argument( "-?", "--help", action="help" )

# Step 3: Parse

config1= parser.parse_args( ['p3_c16_simulation1.dat'] ) # Defaults
pprint( config1 )
config2= parser.parse_args( ["-v", "--samples", "2", 'p3_c16_simulation2.dat'] )
pprint( config2 )
config3= parser.parse_args( ["-b", "Martingale", "--samples", "3", 'p3_c16_simulation3.dat'] )
pprint( config3 )

#error= parser.parse_args( ["-b", "Doesn't Work", "--samples", "x", 'p3_c16_simulation3.dat'] )

# Supplying Defaults
# =====================

# Simple
# ::

config4= argparse.Namespace()
config4.dealer_rule= "Hit17"
config4.split_rule= "NoReSplitAces"
config4.limit= 50
config4.decks= 6
config4.payout= "(3,2)"
config4.player_rule= "SomeStrategy"
config4.betting_rule= "Flat"
config4.rounds=100
config4.stake=50
config4.outputfile= "p3_c16_simulation4.dat"
config4.samples= int(os.environ.get("SIM_SAMPLES",200))
config4a= parser.parse_args( ["-b", "OneThreeTwoSix", 'p3_c16_simulation4.dat'], namespace=config4 )
pprint( config4a )

# Via ChainMap built from configuration files and environment variables
# ::

os.environ['SIM_STAKE']= "100" # Mock the environment

from collections import ChainMap

def nint( x ):
    if x is None: return x
    return int(x)

env_values= [
    ('samples', nint(os.environ.get("SIM_SAMPLES", None)) ),
    ('stake', nint(os.environ.get( "SIM_STAKE", None )) ),
    ('rounds', nint(os.environ.get( "SIM_ROUNDS", None )) ),
]

defaults = ChainMap(
    dict( (k,v) for k,v in env_values if v is not None ),
    { "dealer_rule": "Hit17", "split_rule": "NoReSplitAces" }, # user config
    { "samples": 100, "stake": 50, "rounds": 100 }, # System config
)

config5= parser.parse_args( ["-b", "OneThreeTwoSix", 'p3_c16_simulation5.dat'],
    namespace=argparse.Namespace( **defaults ) )
pprint( config5 )


# Top-level Function
# ===================

# Here's the main feature of a program as a top-level function.

# ::

import ast
import csv
def simulate_blackjack( config ):
    dealer_rule= {'Hit17': Hit17, 'Stand17': Stand17}[config.dealer_rule]()
    split_rule= {'ReSplit': ReSplit, 'NoReSplit': NoReSplit, 'NoReSplitAces':NoReSplitAces}[config.split_rule]()
    try:
       payout= ast.literal_eval( config.payout )
       assert len(payout) == 2
    except Exception as e:
       raise Exception( "Invalid payout {0}".format(config.payout) ) from e
    table= Table( decks=config.decks, limit=config.limit, dealer=dealer_rule,
        split=split_rule, payout=payout )
    player_rule= {'SomeStrategy': SomeStrategy, 'AnotherStrategy': AnotherStrategy}[config.player_rule]()
    betting_rule= {"Flat":Flat, "Martingale":Martingale, "OneThreeTwoSix":OneThreeTwoSix}[config.betting_rule]()
    player= Player( play=player_rule, betting=betting_rule,
        rounds=config.rounds, stake=config.stake )
    simulate= Simulate( table, player, config.samples )
    with open(config.outputfile, "w", newline="") as target:
        wtr= csv.writer( target )
        wtr.writerows( simulate )

# Demo 5 -- using the top-level function
# ::

if __name__ == "__main__":
    simulate_blackjack( config5 )
    check( 'p3_c16_simulation5.dat' )

# Here's how we can build the configuration as a context manager.
# This is of questionable value. It's consistent with using 
# a context manager for logging setup.
# ::

class Build_Config:
    def __enter__( self ):
        return parser.parse_args( ["-b", "OneThreeTwoSix", 'p3_c16_simulation5.dat'],
            namespace=argparse.Namespace( **defaults ) )
    def __exit__( self, *exc ):
        return False

# Demo 5a -- using the top-level function with a context manager that collects
# the configuration.
# ::

if __name__ == "__main__":
    with Build_Config() as config5a:
        simulate_blackjack( config5a )
        check( 'p3_c16_simulation5.dat' )

# Logging and config as context
# ===============================

# ::

import logging.config
import sys

# Here's logging setup as a context manager.
# ::

class Setup_Logging:
    def __init__( self ):
        log_config= dict(
            version= 1,
            handlers= {
                'console': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stderr',
                    'formatter': 'basic',
                },
            },
            formatters = {
                'basic': {
                    'format': "{levelname}:{name}:{message}",
                    'style': "{",
                }
            },
    
            root= { 'handlers': ['console'], 'level': logging.INFO, },
        )
        self.config= log_config
    def __enter__( self ):
        #logging.basicConfig( stream=sys.stderr, level=logging.INFO )
        #logging.config.dictConfig( self.config ) # Doesn't fix existing loggers!
        self.config['disable_existing_loggers']= False
        logging.config.dictConfig( self.config )
        return self
    def __exit__( self, *exc ):
        logging.shutdown()
        return False

# The downside of using a dictConfig as a context manager is that
# logging objects created before logging is configured don't connect.
# properly to the root logger with usable handlers.

class ClassLogger: 
    log= logging.getLogger('ClassLogger')
    def work( self ):
        self.log.info( "Some Info" )
        self.log.warn( "A Warning" )
        
class InstanceLogger:
    def __init__( self, name ):
        self.log= logging.getLogger('InstanceLogger.{0}'.format(name))
    def work( self ):
        self.log.info( "Some Info" )
        self.log.warn( "A Warning" )        
    
# Here's a main function that uses two nested contexts.
# 

if __name__ == "__main__":
    il_bad= InstanceLogger("bad")
    with Setup_Logging( ):
        cl = ClassLogger()
        il = InstanceLogger("good")
        cl.work()
        il.work()
        il_bad.work()

# PITL via Function Composition
# =======================================

# Example of adding features through more
# top-level functions.
# ::

def simulate_blackjack_betting( config ):
    for bet_class in "Flat", "Martingale", "OneThreeTwoSix":
        config.betting_rule= bet_class
        #config.player= Player( play=config.player_rule,
        #    betting=config.betting_rule, rounds=100, stake=50 )
        config.outputfile= "p3_c16_simulation6_{0}.dat".format(bet_class)
        simulate_blackjack( config )

# This works reasonably well. We can do a bit more with object
# composition.

# Top script
# ::

if __name__ == "__main__":
    #with Setup_Logging():
    #with Build_Config() as config6:
    config6= config5
    simulate_blackjack_betting(config6)
    check("p3_c16_simulation6_Flat.dat")
    check("p3_c16_simulation6_Martingale.dat")
    check("p3_c16_simulation6_OneThreeTwoSix.dat")

# PITL via Object Composition
# =======================================

# Proper **Command** design pattern
# ::

from collections.abc import Callable
class Command( Callable ):
    """Typical use
    c = Command()
    c.config= config
    c.run()
    """
    def set_config( self, config ):
        self.__dict__.update( config.__dict__ )
    config= property( fset=set_config )
    def run( self ):
        pass
    def __call__( self ):
        self.run()

class Simulate_Command( Command ):
    dealer_rule_map = {"Hit17": Hit17, "Stand17": Stand17}
    split_rule_map = {'ReSplit': ReSplit,
        'NoReSplit': NoReSplit, 'NoReSplitAces': NoReSplitAces}
    player_rule_map = {'SomeStrategy': SomeStrategy,
        'AnotherStrategy': AnotherStrategy}
    betting_rule_map = {"Flat": Flat,
        "Martingale": Martingale, "OneThreeTwoSix": OneThreeTwoSix}

    def run( self ):
        dealer_rule= self.dealer_rule_map[self.dealer_rule]()
        split_rule= self.split_rule_map[self.split_rule]()
        try:
           payout= ast.literal_eval( self.payout )
           assert len(payout) == 2
        except Exception as e:
           raise Exception( "Invalid payout {0}".format(self.payout) ) from e
        table= Table( decks=self.decks, limit=self.limit, dealer=dealer_rule,
            split=split_rule, payout=payout )
        player_rule= self.player_rule_map[self.player_rule]()
        betting_rule= self.betting_rule_map[self.betting_rule]()
        player= Player( play=player_rule, betting=betting_rule,
            rounds=self.rounds, stake=self.stake )
        simulate= Simulate( table, player, self.samples )
        with open(self.outputfile, "w", newline="") as target:
            wtr= csv.writer( target )
            wtr.writerows( simulate )

if __name__ == "__main__":
    #with Setup_Logging():
    #with Build_Config() as config5:
    main = Simulate_Command()
    main.config= config5
    main.run()

# Composition
# ::

class Analyze_Command( Command ):
    def run( self ):
        with open(self.outputfile, "r", newline="") as target:
            rdr= csv.reader( target )
            outcomes= ( float(row[10]) for row in rdr )
            first= next(outcomes)
            sum_0, sum_1 = 1, first
            value_min = value_max = first
            for value in outcomes:
                sum_0 += 1 # value**0
                sum_1 += value # value**1
                value_min= min( value_min, value )
                value_max= max( value_max, value )
            mean= sum_1/sum_0
            print( "{4}\nMean = {0:.1f}\nHouse Edge = {1:.1%}\nRange = {2:.1f} {3:.1f}".format(mean, 1-mean/50, value_min, value_max, self.outputfile) )

class Command_Sequence( Command ):
    sequence = []
    def __init__( self ):
        self._sequence = [ class_() for class_ in self.sequence ]
    def set_config( self, config ):
        for step in self._sequence:
            step.config= config
    config= property( fset=set_config )
    def run( self ):
        for step in self._sequence:
            step.run()

class Simulate_and_Analyze( Command_Sequence ):
    sequence = [Simulate_Command, Analyze_Command]

if __name__ == "__main__":
    both = Simulate_and_Analyze()
    both.config= config5
    both.run()
    check("p3_c16_simulation7_Flat.dat")
    check("p3_c16_simulation7_Martingale.dat")
    check("p3_c16_simulation7_OneThreeTwoSix.dat")


# Wrapping another class in a For-All loop.
# ::

class ForAllBets_Simulate( Command ):
    def run( self ):
        for bet_class in "Flat", "Martingale", "OneThreeTwoSix":
            self.betting_rule= bet_class
            self.outputfile= "p3_c16_simulation7_{0}.dat".format(bet_class)
            sim= Simulate_Command()
            sim.config= self
            sim.run()

if __name__ == "__main__":
    msc= ForAllBets_Simulate()
    msc.config= config5
    msc.run()
    check("p3_c16_simulation7_Flat.dat")
    check("p3_c16_simulation7_Martingale.dat")
    check("p3_c16_simulation7_OneThreeTwoSix.dat")

