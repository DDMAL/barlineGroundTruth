'''
For creation of mei file containing information provided by users of the Ground
Truth system for the barline finder.

Based on meicreate.py by Gregory Burlet.

by Nicholas Esterer, March 2013.
'''

from __future__ import division
import argparse
from pyparsing import nestedExpr
import os
import re
import sys
import datetime

from pymei import MeiDocument, MeiElement, XmlExport

class GroundTruthBarlineDataConverter:
    '''
    Convert the stored measures of the Ground Truth System to MEI.
    TODO: Only considers barpanels, not staffpanels
    '''

    def __init__(self, staffbb, barbb, verbose=False):
        '''
        Constructor of converter.
        '''

        # Print errors / messages
        self.verbose = verbose

        # The coordinates of the staves stored in the format:
        # [index, top-corner x, top-corner y, bottom-corner x, bottom-corner y]
        # (note this is a python list)
        # To get an idea of what the staves are, image a piano score where each
        # system consists (usually) of a treble staff and bass staff. This
        # system is divided into measures and you can divide the measure into
        # two parts: the box encompassing the top staff within the measure and
        # the box encompassing the bottom staff within the measure. These two
        # boxes are what is meant by staff bounding boxes.
        self.staffbb = staffbb
        if self.verbose:
            sys.stderr.write("Staff bounding boxes" + repr(self.staffbb))

        # The coordinates of the bars stored in the format:
        # (index, top-corner x, top-corner y, bottom-corner x, bottom-corner y)
        # (note this is a python tuple)
        # The differentiation is for compatibility with meicreate.py
        # Bars are the measures of the system. That means for an orchestral
        # score the bars can be very tall and thin.
        self.barbb = barbb
        if self.verbose:
            sys.stderr.write("Bar bounding boxes" + repr(self.barbb))

        self.meidoc = None;

    def bardata_to_mei(self, imagepath, imagewidth, imageheight, imagedpi=72):
        '''
        Perform the data conversion to MEI
        '''

        self.meidoc = MeiDocument()
        mei = MeiElement('mei')
        self.meidoc.setRootElement(mei)

        ###########################
        #         MetaData        #
        ###########################
        mei_head = self._create_header()
        mei.addChild(mei_head)

        ###########################
        #           Body          #
        ###########################
        music = MeiElement('music')
        body = MeiElement('body')
        mdiv = MeiElement('mdiv')
        score = MeiElement('score')
        score_def = MeiElement('scoreDef')
        section = MeiElement('section')

        # physical location data
        facsimile = MeiElement('facsimile')
        surface = MeiElement('surface')

        graphic = self._create_graphic(imagepath, imagewidth, imageheight,\
                imagedpi)
        surface.addChild(graphic)

        mei.addChild(music)
        music.addChild(facsimile)
        facsimile.addChild(surface)
        
        music.addChild(body)
        body.addChild(mdiv)
        mdiv.addChild(score)
        score.addChild(score_def)
        score.addChild(section)

        # It only considers bar panels for now
        for bar in self.barbb:
            # Zone is the coordinates where the measure is found in the image
            zone = self._create_zone(bar[1],bar[2],bar[3],bar[4]);
            # Zone is a child element of the surface
            surface.addChild(zone)
            # The measure is found in the zone
            # TODO: The ordering of the bars has not yet been taken into
            # consideration
            measure = self._create_measure(bar[0],zone);
            section.addChild(measure);
            

    def _create_header(self, rodan_version='0.1'):
        '''
        Create a meiHead element
        '''

        mei_head = MeiElement('meiHead')
        today = datetime.date.today().isoformat()

        app_name = 'gtruth_write_mei'

        # file description
        file_desc = MeiElement('fileDesc')

        title_stmt = MeiElement('titleStmt')
        title = MeiElement('title')
        resp_stmt = MeiElement('respStmt')
        corp_name = MeiElement('corpName')
        corp_name.setValue('Distributed Digital Music Archives and Libraries Lab (DDMAL)')
        title_stmt.addChild(title)
        title_stmt.addChild(resp_stmt)
        resp_stmt.addChild(corp_name)
        
        pub_stmt = MeiElement('pubStmt')
        resp_stmt = MeiElement('respStmt')
        corp_name = MeiElement('corpName')
        corp_name.setValue('Distributed Digital Music Archives and Libraries Lab (DDMAL)')
        pub_stmt.addChild(resp_stmt)
        resp_stmt.addChild(corp_name)

        mei_head.addChild(file_desc)
        file_desc.addChild(title_stmt)
        file_desc.addChild(pub_stmt)

        # encoding description
        encoding_desc = MeiElement('encodingDesc')
        app_info = MeiElement('appInfo')
        application = MeiElement('application')
        application.addAttribute('version', rodan_version)
        name = MeiElement('name')
        name.setValue(app_name)
        ptr = MeiElement('ptr')
        ptr.addAttribute('target', 'https://github.com/DDMAL/barlineFinder')

        mei_head.addChild(encoding_desc)
        encoding_desc.addChild(app_info)
        app_info.addChild(application)
        application.addChild(name)
        application.addChild(ptr)

        # revision description
        revision_desc = MeiElement('revisionDesc')
        change = MeiElement('change')
        change.addAttribute('n', '1')
        resp_stmt = MeiElement('respStmt')
        corp_name = MeiElement('corpName')
        corp_name.setValue('Distributed Digital Music Archives and Libraries Lab (DDMAL)')
        change_desc = MeiElement('changeDesc')
        ref = MeiElement('ref')
        ref.addAttribute('target', '#'+application.getId())
        ref.setValue(app_name)
        ref.setTail('.')
        p = MeiElement('p')
        p.addChild(ref)
        p.setValue('Encoded using ')
        date = MeiElement('date')
        date.setValue(today)
        
        mei_head.addChild(revision_desc)
        revision_desc.addChild(change)
        change.addChild(resp_stmt)
        resp_stmt.addChild(corp_name)
        change.addChild(change_desc)
        change_desc.addChild(p)
        change.addChild(date)

        return mei_head

    def _create_graphic(self, image_path, image_width, image_height, image_dpi):
        '''
        Create a graphic element.
        '''

        graphic = MeiElement('graphic')
        graphic.addAttribute('height', str(image_height))
        graphic.addAttribute('width', str(image_width))
        graphic.addAttribute('target', image_path)
        graphic.addAttribute('resolution', str(image_dpi))
        graphic.addAttribute('unit', 'px')

        return graphic

    def _create_measure(self, n, zone = None):
        '''
        Create a measure element and attach a zone reference to it.
        The zone element is optional, since the zone of the measure is
        calculated once all of the staves within a measure have been added
        to the MEI.
        '''

        measure = MeiElement('measure')
        measure.addAttribute('n', str(n))

        if zone is not None:
            measure.addAttribute('facs', '#'+zone.getId())

        return measure

    def _create_zone(self, ulx, uly, lrx, lry):
        '''
        Create a zone element
        '''

        zone = MeiElement('zone')
        zone.addAttribute('ulx', str(ulx))
        zone.addAttribute('uly', str(uly))
        zone.addAttribute('lrx', str(lrx))
        zone.addAttribute('lry', str(lry))

        return zone

    def output_mei(self, output_path):
        '''
        Write the generated mei to disk
        '''

        # output mei file
        if self.meidoc == None:
            raise Warning('The MEI document has not yet been created');
            return

        XmlExport.meiDocumentToFile(self.meidoc, output_path)

