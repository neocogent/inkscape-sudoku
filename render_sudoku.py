#!/usr/bin/env python

'''
render_sudoku.py
A sudoku generator plugin for Inkscape, but also can be used as a standalone
command line application.

Copyright (C) 2011 Chris Savery <chrissavery(a)gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

__version__ = "0.1"

import inkex, simplestyle, re, subprocess

class SVGSudoku (inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--tab",
            action="store", type="string",
            dest="tab")
        self.OptionParser.add_option("--difficulty",
            action="store", type="string",
            dest="difficulty", default="mixed",
            help='How difficult to make puzzles.')
        self.OptionParser.add_option("--rows",
            action="store", type="int",
            dest="rows", default=1,
            help='Number of puzzle rows.')
        self.OptionParser.add_option("--cols",
            action="store", type="int",
            dest="cols", default=1,
            help='Number of puzzle columns.')          
        self.OptionParser.add_option("--puzzle-size",
            action="store", type="int",
            dest="puzzle_size", default=6,
            help='The width & height of each puzzle.')
        self.OptionParser.add_option("--puzzle-gap",
            action="store", type="int",
            dest="puzzle_gap", default=1,
            help='The space between puzzles.')
        self.OptionParser.add_option("--color-text",
            action="store", type="int",
            dest="color_text", default=0,  #000000
            help='Color for given numbers.')           
        self.OptionParser.add_option("--color-bkgnd",
            action="store", type="int",
            dest="color_bkgnd", default=-1,  #FFFFFF
            help='Color for the puzzle background.')
        self.OptionParser.add_option("--color-puzzle",
            action="store", type="string",
            dest="color_puzzle", default=0,  #000000
            help='Border color for the puzzles.')
        self.OptionParser.add_option("--color-boxes",
            action="store", type="string",
            dest="color_boxes", default=0,  #000000
            help='Border color for puzzle boxes.')
        self.OptionParser.add_option("--color-cells",
            action="store", type="string",
            dest="color_cells", default=-1061109505, #C0C0C0
            help='Border color for the puzzle cells.')
        self.OptionParser.add_option("-u", "--units",
            action="store", type="string",
            dest="units", default="cm",
            help="The unit of the dimensions")

    def getUnittouu(self, param):
        " compatibility between inkscape 0.48 and 0.91 "
        try:
            return inkex.unittouu(param)
        except AttributeError:
            return self.unittouu(param)

    def unsignedLong(self, signedLongString):
        " interpret the signed long as unsigned "
        longColor = long(signedLongString)
        if longColor < 0:
            longColor = longColor & 0xFFFFFFFF
        return longColor

    #A*256^0 + B*256^1 + G*256^2 + R*256^3
    def getColorString(self, longColor):
        " convert the long into a #RRGGBB color value "
        longColor = self.unsignedLong(longColor)
        hexColor = hex(longColor)[2:-3]
        hexColor = hexColor.rjust(6, '0')
        return '#' + hexColor.upper()



    def draw_grid(self, g_puz, x, y):
        bkgnd_style = {'stroke':'none', 'stroke-width':'2', 'fill':self.options.color_bkgnd }      
        puzzle_style = {'stroke':self.options.color_puzzle, 'stroke-width':'2', 'fill':'none' }
        boxes_style = {'stroke':self.options.color_boxes, 'stroke-width':'2', 'fill':'none' }
        cells_style = {'stroke':self.options.color_cells, 'stroke-width':'1', 'fill':'none' }
        g = inkex.etree.SubElement(g_puz, 'g')
        self.draw_rect(g, bkgnd_style, self.left+x, self.top+y, self.size, self.size)
        self.draw_rect(g, cells_style, self.left+x+self.size/9, self.top+y, self.size/9, self.size)
        self.draw_rect(g, cells_style, self.left+x+self.size/3+self.size/9, self.top+y, self.size/9, self.size)
        self.draw_rect(g, cells_style, self.left+x+2*self.size/3+self.size/9, self.top+y, self.size/9, self.size)
        self.draw_rect(g, cells_style, self.left+x, self.top+y+self.size/9, self.size, self.size/9)
        self.draw_rect(g, cells_style, self.left+x, self.top+y+self.size/3+self.size/9, self.size, self.size/9)
        self.draw_rect(g, cells_style, self.left+x, self.top+y+2*self.size/3+self.size/9, self.size, self.size/9)      
        self.draw_rect(g, boxes_style, self.left+x+self.size/3, self.top+y, self.size/3, self.size)
        self.draw_rect(g, boxes_style, self.left+x, self.top+y+self.size/3, self.size, self.size/3)
        self.draw_rect(g, puzzle_style, self.left+x, self.top+y, self.size, self.size)
        
    def draw_rect(self, g, style, x, y, w, h):
        attribs = {'style':simplestyle.formatStyle(style), 'x':str(x), 'y':str(y), 'height':str(h), 'width':str(w) }
        inkex.etree.SubElement(g, inkex.addNS('rect','svg'), attribs)    
        
    def fill_puzzle(self, g_puz, x, y, data):
        cellsize = self.size / 9
        txtsize = self.size / 12
        offset = (cellsize + txtsize)/2.25
        g = inkex.etree.SubElement(g_puz, 'g')
        text_style = {'font-size':str(txtsize),
                      'fill':self.options.color_text,
                      'font-family':'arial',
                      'text-anchor':'middle', 'text-align':'center' }
        for n in range(len(data)):
            if data[n] in "123456789":
                attribs = {'style': simplestyle.formatStyle(text_style), 
                    'x': str(self.left + x + n%9 * cellsize + cellsize/2  ), 'y': str(self.top + y + n/9 * cellsize + offset ) }
                inkex.etree.SubElement(g, 'text', attribs).text = str(data[n])


    def effect(self):
        args = ["./qqwing", "--one-line", "--generate", str(self.options.rows * self.options.cols)]
        if self.options.difficulty != 'mixed':
            args.extend(["--difficulty", self.options.difficulty])
        data = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].splitlines()
        #
        # convert colors
        #inkex.debug("%s"%(self.options.color_cells))
        self.options.color_text = self.getColorString(self.options.color_text)
        self.options.color_bkgnd = self.getColorString(self.options.color_bkgnd)
        self.options.color_puzzle = self.getColorString(self.options.color_puzzle)
        self.options.color_boxes = self.getColorString(self.options.color_boxes)
        self.options.color_cells = self.getColorString(self.options.color_cells)
        #
        parent = self.document.getroot()
        self.doc_w = self.getUnittouu(parent.get('width'))
        self.doc_h = self.getUnittouu(parent.get('height'))
        self.size = self.getUnittouu(str(self.options.puzzle_size) + self.options.units)
        self.gap = self.getUnittouu(str(self.options.puzzle_gap) + self.options.units)
        self.shift = self.size + self.gap
        self.left = (self.doc_w - (self.options.cols * self.shift - self.gap))/2
        self.top = (self.doc_h - (self.options.rows * self.shift - self.gap))/2
        self.sudoku_g = inkex.etree.SubElement(parent, 'g', {'id':'sudoku'})
        for row in range(0, self.options.rows):
            for col in range(0, self.options.cols):
                g = inkex.etree.SubElement(self.sudoku_g, 'g', {'id':'puzzle_'+str(col)+str(row)})
                self.draw_grid(g, col*self.shift, row*self.shift)
                self.fill_puzzle(g, col*self.shift, row*self.shift, data[col+row*self.options.cols])

if __name__ == '__main__':   #pragma: no cover
    e = SVGSudoku()
    e.affect()
