##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import os
import unittest

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferOSL
import GafferDelight

@unittest.skipIf( "TRAVIS" in os.environ, "No license available on Travis" )
class InteractiveDelightRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	# Temporarily disable this test (which is implemented in the
	# base class) because it fails. The issue is that we're automatically
	# instancing the geometry for the two lights, and that appears to
	# trigger a bug in 3delight where the sampling goes awry.
	@unittest.skip( "Awaiting feedback from 3delight developers" )
	def testAddLight( self ) :

		pass

	def _createInteractiveRender( self ) :

		return GafferDelight.InteractiveDelightRender()

	def _createConstantShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "Surface/Constant" )
		return shader, shader["parameters"]["Cs"]

	def _createTraceSetShader( self ) :

		return None, None

	def _cameraVisibilityAttribute( self ) :

		return "dl:visibility.camera"

	def _createMatteShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "matte" )
		return shader, shader["parameters"]["Cs"]

	def _createPointLight( self ) :

		light = GafferOSL.OSLLight()
		light["shape"].setValue( light.Shape.Sphere )
		light["radius"].setValue( 0.01 )
		light.loadShader( "maya/osl/pointLight" )
		light["attributes"].addMember( "dl:visibility.camera", False )

		return light, light["parameters"]["i_color"]

if __name__ == "__main__":
	unittest.main()