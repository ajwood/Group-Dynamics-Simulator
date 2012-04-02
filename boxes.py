import pygame
from pygame.locals import *
import time
import random
import math
#import Image   -- won't need this unless I want to load sprite images

import collections

import numpy as np

DEVELOPMENT = True

class SheepBox():

	def __init__(self, game, initial_loc, init_velocity, color=None, name=None, retreat=False ):

		self.game = game

		self.name = name

		self.loc = initial_loc
		self.width, self.height = 3, 3

		if color == None:
			self.color = [255,100,0]
		else:
			self.color = color

		self.retreat = retreat

		self.tail = collections.deque( [], self.game.options.get( 'draw_tail_len' ).value )

		self.velocity = np.array( init_velocity )


	def update(self, panel, self_i):
		bottom = panel.top + panel.height
		right = panel.top + panel.width

		# Accelerate toward com of visable group with magnitude proportional to
		# the distance from the com
		# TODO: This needs to be implemented with a dynamic progamming algorithm
		# Also, there may be a better vectorized approach to avoid the iteration?
		if self.game.options.get( 'gravity' ).value:

			others = []
			for n in range( len( self.game.sheep ) ):
				s = self.game.sheep[ n ]
				if ( s != self ):
					#to_s = np.array( [s.loc[0] - self.loc[0], s.loc[1] - self.loc[1]] )
					#d = math.hypot( s.loc[0] - self.loc[0], s.loc[1] - self.loc[1] )
					d = self.game.distance_matrix[ self_i, n ]
					if ( d < self.game.options.get( 'ROI' ).value ):
						others.append( np.array( s.loc ) )

			# If we found some others
			if ( len( others ) > 0 ):
				others_com = np.mean( others, axis=0 )

				to_com = others_com - self.loc
				to_com_mag = math.hypot( to_com[0], to_com[1] )

				acceleration = scaleVector( to_com, to_com_mag * self.game.options.get( 'A0' ).value ) 
				#print acceleration

				#if ( len( others ) + 1 >= self.game.options.get( 'critical_mass' ).value ):
				#	acceleration = np.copy( acceleration ) * -100

				if self.game.options.get('withdraw').value:
					acceleration *= -1

				self.velocity += acceleration

		# Don't fall off the screen
		if ( self.game.options.get(  'bounce_off_walls'  ).value ):
			if self.loc[0] + self.width > right - 1:
				self.velocity[0] = abs( self.velocity[0] ) * -1
			elif self.loc[0] < 0:
				self.velocity[0] = abs( self.velocity[0] )
			if self.loc[1] + self.height > bottom - 1:
				self.velocity[1] = abs( self.velocity[1] ) * -1
			elif self.loc[1] < 0:
				self.velocity[1] = abs( self.velocity[1] )
		else:
			if self.loc[0] + self.width > right - 1:
				self.loc[0] = 0
			elif self.loc[0] < 0:
				self.loc[0] = right - self.width - 1
			if self.loc[1] + self.height > bottom - 1:
				self.loc[1] = 0
			elif self.loc[1] < 0:
				self.loc[1] = bottom - self.height - 1


		# Reduce to max speed
		self.velocity[ self.velocity > self.game.options.get( 'max_speed' ).value ] = self.game.options.get( 'max_speed' ).value
		self.velocity[ self.velocity < self.game.options.get( 'max_speed' ).value * -1 ] = self.game.options.get('max_speed' ).value * -1

		self.loc += self.velocity
		self.push_prev_loc( np.copy( self.loc ) )
		return 0

	def push_prev_loc( self, loc ):
		if ( self.tail.maxlen != self.game.options.get( 'draw_tail_len' ).value ):
			self.tail = collections.deque( self.tail, self.game.options.get( 'draw_tail_len' ).value )

		self.tail.appendleft( loc )


def scaleVector( vec, new_length ):
	old_length = math.hypot( vec[0], vec[1] )
	if ( old_length != 0 ):
		return vec * ( new_length / old_length )
	else:
		return vec

def rotateVector( vec, dir ):
	return scaleVector( np.copy(dir), math.hypot( vec[1], vec[0] ) )
	
