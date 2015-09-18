##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import IECore

import Gaffer
import GafferTest

class ValuePlugTest( GafferTest.TestCase ) :

	def testCacheMemoryLimit( self ) :

		n = GafferTest.CachingTestNode()

		n["in"].setValue( "d" )

		v1 = n["out"].getValue( _copy=False )
		v2 = n["out"].getValue( _copy=False )

		self.assertEqual( v1, v2 )
		self.assertEqual( v1, IECore.StringData( "d" ) )

		# the objects should be one and the same, as the second computation
		# should have shortcut and returned a cached result.
		self.failUnless( v1.isSame( v2 ) )

		Gaffer.ValuePlug.setCacheMemoryLimit( 0 )

		v3 = n["out"].getValue( _copy=False )
		self.assertEqual( v3, IECore.StringData( "d" ) )

		# the objects should be different, as we cleared the cache.
		self.failIf( v3.isSame( v2 ) )

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__originalCacheMemoryLimit )

		v1 = n["out"].getValue( _copy=False )
		v2 = n["out"].getValue( _copy=False )

		self.assertEqual( v1, v2 )
		self.assertEqual( v1, IECore.StringData( "d" ) )

		# the objects should be one and the same, as we reenabled the cache.
		self.failUnless( v1.isSame( v2 ) )

	def testSettable( self ) :

		p1 = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.In )
		self.failUnless( p1.settable() )

		p1.setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		self.failIf( p1.settable() )

		p1.setFlags( Gaffer.Plug.Flags.ReadOnly, False )
		self.failUnless( p1.settable() )

		p2 = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		self.failIf( p2.settable() )

		p1.setInput( p2 )
		self.failIf( p1.settable() )

	def testUncacheabilityPropagates( self ) :

		n = GafferTest.CachingTestNode()
		n["in"].setValue( "pig" )

		p1 = Gaffer.ObjectPlug( "p1", Gaffer.Plug.Direction.In, IECore.IntData( 10 ) )
		p2 = Gaffer.ObjectPlug( "p2", Gaffer.Plug.Direction.In, IECore.IntData( 20 ) )
		p3 = Gaffer.ObjectPlug( "p3", Gaffer.Plug.Direction.In, IECore.IntData( 30 ) )

		p1.setInput( n["out"] )
		p2.setInput( p1 )
		p3.setInput( p2 )

		o2 = p2.getValue( _copy = False )
		o3 = p3.getValue( _copy = False )

		self.assertEqual( o2, IECore.StringData( "pig" ) )
		self.assertEqual( o3, IECore.StringData( "pig" ) )
		self.failUnless( o2.isSame( o3 ) ) # they share cache entries

		n["out"].setFlags( Gaffer.Plug.Flags.Cacheable, False )

		o2 = p2.getValue( _copy = False )
		o3 = p3.getValue( _copy = False )

		self.assertEqual( o2, IECore.StringData( "pig" ) )
		self.assertEqual( o3, IECore.StringData( "pig" ) )
		self.failIf( o2.isSame( o3 ) ) # they shouldn't share cache entries

	def testReadOnlySerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug( defaultValue = 10, maxValue = 1000, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"].setValue( 100 )
		s["n"]["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["n"]["p"].defaultValue(), 10 )
		self.assertEqual( s2["n"]["p"].maxValue(), 1000 )
		self.assertEqual( s2["n"]["p"].getValue(), 100 )
		self.assertEqual( s2["n"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ), True )

	def testSetValueSignalsDirtiness( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.IntPlug()

		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["p"].setValue( 10 )

		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( n["p"] ) )

		n["p"].setValue( 10 )

		self.assertEqual( len( cs ), 1 )

	def testCopyPasteDoesntRetainComputedValues( self ) :

		s = Gaffer.ScriptNode()

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()

		s["add1"]["op1"].setValue( 2 )
		s["add1"]["op2"].setValue( 3 )
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		s["add2"]["op2"].setValue( 0 )

		self.assertEqual( s["add2"]["sum"].getValue(), 5 )

		ss = s.serialise( filter = Gaffer.StandardSet( [ s["add2"] ] ) )

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( s["add2"]["op1"].getInput() is None )
		self.assertEqual( s["add2"]["op1"].getValue(), 0 )
		self.assertEqual( s["add2"]["sum"].getValue(), 0 )

	def testSerialisationOmitsDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		self.assertEqual( s["n"]["op1"].getValue(), s["n"]["op1"].defaultValue() )
		self.assertEqual( s["n"]["op2"].getValue(), s["n"]["op2"].defaultValue() )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["op1"].setValue( 10 )

		self.assertTrue( "[\"op1\"].setValue" in s.serialise() )

	def testFloatPlugOmitsDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["f"].setValue( 10.1 )

		self.assertTrue( "[\"f\"].setValue" in s.serialise() )

	def testBoolPlugOmitsDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["f"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["f"].setValue( True )

		self.assertTrue( "[\"f\"].setValue" in s.serialise() )

	def testBoolPlugOmitsDefaultValuesWhenDefaultIsTrue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["f"] = Gaffer.BoolPlug( defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["f"].setValue( False )

		self.assertTrue( "[\"f\"].setValue" in s.serialise() )

	def testCreateCounterpart( self ) :

		p = Gaffer.ValuePlug()
		p["i"] = Gaffer.IntPlug()
		p["f"] = Gaffer.FloatPlug()

		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )
		self.assertEqual( p2.keys(), [ "i", "f" ] )
		self.assertTrue( isinstance( p2["i"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( p2["f"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( p2, Gaffer.ValuePlug ) )

	def testPrecomputedHashOptimisation( self ) :

		n = GafferTest.CachingTestNode()
		n["in"].setValue( "a" )

		a1 = n["out"].getValue( _copy = False )
		self.assertEqual( a1, IECore.StringData( "a" ) )
		self.assertEqual( n.numHashCalls, 1 )

		# We apply some leeway in our test for how many hash calls are
		# made - a good ValuePlug implementation will probably avoid
		# unecessary repeated calls in most cases, but it's not
		# what this unit test is about.
		a2 = n["out"].getValue( _copy = False )
		self.assertTrue( a2.isSame( a1 ) )
		self.assertTrue( n.numHashCalls == 1 or n.numHashCalls == 2 )

		h = n["out"].hash()
		self.assertTrue( n.numHashCalls >= 1 and n.numHashCalls <= 3 )
		numHashCalls = n.numHashCalls

		# What we care about is that calling getValue() with a precomputed hash
		# definitely doesn't recompute the hash again.
		a3 = n["out"].getValue( _copy = False, _precomputedHash = h )
		self.assertEqual( n.numHashCalls, numHashCalls )
		self.assertTrue( a3.isSame( a1 ) )

	def testSerialisationOfChildValues( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["v"] = Gaffer.ValuePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["v"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["v"]["i"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["v"]["i"].getValue(), 10 )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__originalCacheMemoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__originalCacheMemoryLimit )

if __name__ == "__main__":
	unittest.main()
