#!/usr/bin/python

import pygame
from pygame.locals import *
from boxes import SheepBox
import time
import os
import sys
import numpy as np
import itertools
import math

from functools import partial

import collections

class GameMain():

	def __init__( self, color_bg=(0,0,0) ):
		pygame.init()
		pygame.font.init()

		pygame.display.set_caption( "Group Dynamics Simulator" )        
		self.color_bg = color_bg

		self.clock = pygame.time.Clock()
		self.limit_fps = True
		self.limit_fps_max = 60

		# actual size
		self.width = 1000
		self.height = 700

		self.screen = pygame.display.set_mode(( self.width, self.height ))

		self.sheep = []

		self.options_init()
		self.action_panel_init()
		self.control_panel_init()
		self.game_init()

		#self.refresh_distance_matrix()

	def game_init(self, color_list=None, init_speed=7):

		self.sheep = []
		self.add_sheep( self.options.get('n_boxes').value )

	def update_n_boxes(self):
		n_boxes = self.options.get('n_boxes').value
		if n_boxes < len( self.sheep ) :
			self.sheep = self.sheep[:n_boxes]
		elif n_boxes > len( self.sheep ) :
			self.add_sheep( n_boxes - len( self.sheep ) )

	def add_sheep(self, n=1, loc_list=None, init_speed=7, color_list=None, name=None, retreat=False):
		if loc_list != None and len( loc_list ) != n:
			raise Exception( "The sheep are confused about where they're supposed to be..." )

		if loc_list == None:
			loc_list = []

		if color_list == None:
			color_list = []

		for s in range( n ):
			if len( color_list ) > 0:
				color = color_list[n % len( color_list )]
			else:
				color = self.randColor()

			if len( loc_list ) > 0:
				loc = loc_list[ s ]
			else:
				loc = self.randLoc()

			self.sheep.append( SheepBox(self,
				loc,
				self.randVelocity(init_speed),
				color=color,
				name=name,
				retreat=retreat,
				)
			)

	def control_panel_init(self):
		self.control_panel_rect = Rect( 700, 0, 300, 700 )
		self.control_panel = self.screen.subsurface( self.control_panel_rect )

		# Create surfaces with our images on them
		self.checkbox_unselected = pygame.image.load(os.path.join("graphics","checkbox.png")).convert()
		self.checkbox_selected   = pygame.image.load(os.path.join("graphics","selected.png")).convert()
		self.scroll_bar_left   = pygame.image.load(os.path.join("graphics","scroll_bar_left.png")).convert()
		self.scroll_bar_right   = pygame.image.load(os.path.join("graphics","scroll_bar_right.png")).convert()


		# Callbacks for different option types event handling
		# Generic boolean button
		def boolean_event_handler( opt_name, x, y, click_pos=None ):
			if ( self.options.toggle(opt_name) ):
				self.screen.blit(self.checkbox_selected, (x,y))
			else:
				self.screen.blit(self.checkbox_unselected, (x,y))

		# Generic int/float slider
		def slider_event_handler( opt_name, slider, click_pos=None ):
			value = slider.click( click_pos )
			self.options.set(opt_name, value)

		def n_boxes_event_handler( slider, click_pos=None ):
			value = slider.click( click_pos )
			self.options.set('n_boxes', value)
			self.update_n_boxes()

		# Define sliders
		# TODO: we might be able to get rid of this list now that we're using
		# the functools.partil to close the callbacks
		sliders = {}

		self.control_buttons = {}

		y_offset = 10
		for opt in self.options.values():
			rect = Rect( 710, y_offset, 100 + 2 * self.scroll_bar_left.get_width(), 20 )
			if opt.key == 'n_boxes':
				sliders[ 'n_boxes' ] = Slider( self, 710, y_offset, opt )
				self.control_buttons[ 'n_boxes' ] = ( rect, partial(n_boxes_event_handler, sliders[ 'n_boxes' ] ) )
			elif opt.val_type == bool :
				self.control_buttons[ opt.key ] = ( rect, partial(boolean_event_handler, opt.key, 710, y_offset ) )
			elif opt.val_type == float or opt.val_type == int:
				sliders[ opt.key ] = Slider( self, 710, y_offset, opt )
				self.control_buttons[ opt.key ] = ( rect, partial(slider_event_handler, opt.key, sliders[ opt.key ] ) )

			y_offset = y_offset + 20

			for name, button in self.control_buttons.items():
				opt = self.options.get(name)
				rect = button[0]
				onclick = button[1]
				
				if opt.val_type == bool :
					# Draw the checkbox
					if self.options.get( name ).value :
						self.screen.blit(self.checkbox_selected, (rect.x,rect.y))
					else:
						self.screen.blit(self.checkbox_unselected, (rect.x,rect.y))

					# Draw the label TODO: draw this on control_panel and never update
					fontobject = pygame.font.Font( None, 18 )
					self.screen.blit( fontobject.render(name, 1, (255,255,255)), (rect.x+20,rect.y) )
				elif opt.val_type == float or opt.val_type == int:
					onclick()
					fontobject = pygame.font.Font( None, 18 )
					self.screen.blit( fontobject.render(name, 1, (255,255,255)), (rect.x+140,rect.y) )


	def action_panel_init(self):
		self.action_panel_rect = Rect(0, 0, 700, 700)
		self.action_panel = self.screen.subsurface( self.action_panel_rect )

		pygame.draw.rect( self.screen, Color('yellow') , self.action_panel_rect, 3 )


	def options_init(self):
		options = (
				#TODO: shold reconsider some of the defaults/min/max
				('n_boxes',          3,      K_n, int,   1,    101 ),

				('gravity',          False,  K_g, bool,  None, None ),
				('A0',               0.0015, K_a, float, 0,    0.01  ),
				('ROI',              200,    K_r, int,   0,    400  ),
				#('critical_mass',    40,     K_k, int,   40,   500  ),
				('max_speed',        5,      K_m, float, 1,    20   ),
				('bounce_off_walls', False,  K_b, bool,  None, None ),
				('withdraw',         False,  K_w, bool,  None, None), 

				('draw_tail_len',    30,     K_l, int,   1,    200, ),
				('draw_ROI',         False,  K_d, bool,  None, None ),
				)
		self.options = OptionsHandler( options )

		# Bind out shortcut keys to the keyboard bindings dict
		self.keyboard_bindings = {}
		for opt in self.options.values():
			if opt.shortcut_key != None:
				self.keyboard_bindings[ opt.shortcut_key ] = opt.key

	def editOption( self, key ):
		if( not key in self.options.keys() ):
			raise UnsupportedOptionException(key)

		opt = self.options.get( key )

		val = self.drawOption( 10, self.height - 30, key, opt.value, editable=True )
		self.options.set(key, val)

	def loop(self):
		while True:
			self.handle_events()
			self.update()
			self.draw()

			if self.limit_fps: self.clock.tick( self.limit_fps_max )
			else: self.clock.tick()

	def update(self):        
		# Compute the distances between each pair of boxes
		n_boxes = self.options.get( 'n_boxes' ).value
		self.distance_matrix = np.zeros( [n_boxes,n_boxes] )
		for pair in itertools.combinations( range( len( self.sheep ) ), 2 ):
			s1 = self.sheep[ pair[0] ]
			s2 = self.sheep[ pair[1] ]

			d = math.hypot( s1.loc[0] - s2.loc[0], s1.loc[1] - s2.loc[1] )

			self.distance_matrix[ pair[0],pair[1] ] = d
			self.distance_matrix[ pair[1],pair[0] ] = d

		for n in range( len( self.sheep ) ):
			s = self.sheep[ n ]
			status = s.update(self.action_panel_rect, n)
			if ( status == 1 ):
				self.sheep.remove( s )
			elif ( status == 2 ):
				self.game_init()
	
	def handle_events(self):
		# kmods = pygame.key.get_mods() # key modifiers

		paused = False
		while( True ):

			events = pygame.event.get()
			for event in events:
				if(event.type == KEYDOWN):
					if ( event.key == K_RETURN ):
						self.game_init()
					elif (event.key == K_SPACE): paused = not paused
					elif (event.key == K_ESCAPE): self.quit()
					elif (event.key in self.keyboard_bindings.keys() ):
						opt_key = self.keyboard_bindings[ event.key ]

						opt = self.options.get( opt_key )

						# If not toggling a bool type, get user input
						if opt.val_type != bool :
							self.editOption( opt_key )

						# fire a positionless click on the associated gui element
						option_gui = self.control_buttons[ opt_key ]
						if ( option_gui != None ):
							option_gui[1]()

						# Hack around the option design to change the number of boxes
						if opt_key == 'n_boxes' :
							self.update_n_boxes()

				elif(event.type == MOUSEBUTTONDOWN):

					# If clicked control panel
					if self.control_panel_rect.collidepoint( event.pos ):
						for opt_name, button in self.control_buttons.items():
							button_rect = button[0]
							button_hit  = button[1]

							if button_rect.collidepoint( event.pos ):
								button_hit(click_pos=event.pos)
					elif self.action_panel_rect.collidepoint( event.pos ):
						self.options.get( 'n_boxes' ).value += 1
						self.add_sheep( loc_list=[event.pos] )
			if ( paused ):
				pygame.time.wait( 50 )
			else:
				return

	def draw(self):
		# clear screen
		self.screen.fill( self.color_bg, self.action_panel_rect )

		for s in self.sheep:
			first = True
			w,h = s.width, s.height
			for tail in s.tail:
				x,y = tail
				r = Rect(x, y, w, h)
				self.action_panel.fill(s.color, r)
				if first and self.options.get('draw_ROI').value:
					pygame.draw.circle( self.action_panel, s.color, (int(x), int(y)), int(self.options.get('ROI').value), 1 )
					first = False

		pygame.display.flip()
	
	def quit(self):
		sys.exit(0)


	def display_box(self, x, y, string):
		"Print a message box at x,y"
		fontobject = pygame.font.Font(None,18)
		pygame.draw.rect(self.screen, self.color_bg, (x, y, 200, 20), 0)
		if( len( string ) > 0 ):
			self.screen.blit( fontobject.render(string, 1, (255,255,255)), (x, y) )
		pygame.display.flip()

	def drawOption(self, x, y, key, val, editable=False):
		val = str( val )
		self.display_box(x, y, "%s: %s" % (key, val) )
		if ( editable ):
			while 1:
				inkey = self.get_key()
				if inkey == K_BACKSPACE:
					val = val[0:-1]
				elif inkey == K_RETURN:
					break
				elif inkey == K_MINUS:
					val += "_"
				elif inkey <= 127:
					val += chr(inkey)
				self.display_box(x, y, "%s: %s" % (key, val) )
			return val

	def get_key(self):
		while 1:
			event = pygame.event.poll()
			if event.type == KEYDOWN:
				return event.key
			else:
				pass

	
	def randLoc(self):
		size = (self.action_panel_rect.width, self.action_panel_rect.height)
		return [ np.random.randint(0, size[0] - 0 ) + self.action_panel_rect.x,
				np.random.randint(0, size[1] - 0 ) + self.action_panel_rect.y ]

	def randVelocity(self, init_speed):
		rad = np.radians( np.random.randint(0,360) )
		return [np.cos(rad) * init_speed, np.sin(rad) * init_speed]

	def randColor(self):
		return ( np.random.randint( 50, 255 ), np.random.randint( 50, 255 ), np.random.randint( 50, 255 ) )
	
# TODO:
#	- make self.options accessible w/o .get(key) becuase this is really just a specialized dict
#	- initialize options with a dict with required/optional keys (bools shouldn't need to supply min/max)
#   - callbacks for value changes should be installed here
class OptionsHandler():

	def __init__(self, option_list):
		self.options = {}

		for opt_spec in option_list:
			key, value, shortcut_key, value_type, min, max = opt_spec
			if key in self.options.keys():
				raise Exception( 
						"OptionsHandler initilized with duplicate key {0}={1} and {0}={2}".format( 
							key, 
							self.options[name].value, 
							value ) 
						)
			self.options[ key ] = Option( key, value, shortcut_key, value_type, min, max )
	
	def get(self, key):
		if( not key in self.options.keys() ):
				raise UnsupportedOptionException( key )
		return self.options[ key ]


	def keys(self):
		return self.options.keys()

	def values(self):
		return self.options.values()

	def items(self):
		ret = []
		for key, opt in self.options.items():
			ret.append( [key, opt.value] )
		return ret

	def toggle(self, key):
		option = self.get( key )
		if ( not option.val_type == bool ):
			raise ValueError( "Can't toggle non-boolean type: {0} (type={1})".format(key, option.val_type ) )
		option.value = not option.value
		return option.value

	def set(self, key, value):
		opt = self.get( key )

		# force option to its type
		# TODO: catch value exceptions and let the user keep trying
		opt.value = opt.val_type( value )


class Option():
	def __init__(self, key, value, shortcut_key=None, val_type=None, min=None, max=None ):
		self.key          = key
		self.value        = value
		self.shortcut_key = shortcut_key
		self.min          = min
		self.max          = max

		# best guess for val for yet-to-be implemented user input casting
		if val_type == None:
			self.val_type = val_type( value )
		else:
			self.val_type = val_type

class UnsupportedOptionException(Exception):
	def __init__(self, key):
		self.key   = key
	def __str__(self):
		return 'Unsuppored option: %s' % self.key
	def __unicode__(self):
		return self.__str__()

# NOTE:
#	assumes left/right arrow graphic are same size, and square
#	assumes width=100 ticks
class Slider():
	def __init__(self, game, x, y, option):

		self.id = option.key
		self.option = option
		self.x = x                                                      # x position of slider object
		self.y = y                                                      # y position of slider object
		self.game = game                                                # reference to the main game object
		self.per_index = ( float(self.option.max) - float(self.option.min) ) / 100    # value represented by one click (pixel)

		self.arrow_width = game.scroll_bar_right.get_width()

		# Draw the left/right arrows
		game.screen.blit( game.scroll_bar_left, (x,y) )
		game.screen.blit( game.scroll_bar_right, (x + 100 + self.arrow_width, y) )

		# Rect over which the needle moves
		self.slide_area = Rect( x + self.arrow_width, y, 100, self.arrow_width )

		# Draw a border around the slide area
		slide_area_border = Rect( x + self.arrow_width - 1, y - 1, 102, self.arrow_width + 2 )
		pygame.draw.rect( game.screen, (100,100,90), slide_area_border, 1 ) 

		# Initialize needle
		self.needle = Rect( 0, y, 1, self.arrow_width )
		self.update_needle_position()
		self.draw_needle()

	def update_needle_position( self ):
		x_offset = 100 * (float(self.option.value) / self.option.max)
		self.needle.x = self.x + self.arrow_width + x_offset
		self.draw_needle()

	def draw_needle( self ):
		self.game.screen.fill( (0,0,0), self.slide_area )
		self.game.screen.fill( (50,50,50), self.needle )
		self.game.screen.fill( (50,50,50), self.needle )
	
	def inc(self):
		if self.option.value + self.per_index <= self.option.max :
			self.option.value += self.per_index
			self.needle.move_ip(1, 0)
			self.draw_needle()
		return self.option.value

	def dec(self):
		if self.option.value - self.per_index >= self.option.min :
			self.option.value -= self.per_index
			self.needle.move_ip(-1, 0)
			self.draw_needle()
		return self.option.value

	def click(self, pos):
		if pos == None:
			self.update_needle_position()
		elif pos[0] < self.x + self.game.scroll_bar_left.get_width() :
			self.dec()
		elif pos[0] > self.x + self.game.scroll_bar_left.get_width() + 100 :
			self.inc()
		return self.option.value




if __name__ == '__main__':
	g = GameMain()
	g.loop()
