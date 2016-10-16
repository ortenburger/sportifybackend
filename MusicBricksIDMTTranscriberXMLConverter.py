__author__ = 'Jakob Abesser'
__email__ = 'jakob.abesser@idmt.fraunhofer.de'
__copyright__ = 'Fraunhofer IDMT, 2015'

import os
import xml.etree.ElementTree as et


class MusicBricksIDMTTranscriberXMLConverter:
    """ Class to
          - parse the MusicBricksIDMTTranscriber results in XML files and
          - to convert the results to CSV files that can be imported to Sonic Visualizer layers
    """

    def readXML(self, fnXML):
        """ Load data from MusicBricksIDMTTranscriber XML result file
        Args:
            fnXML: (string) Absolute filename of XML file
        Returns:
            data: (dict) Extracted parameters, keys:
                'key': (string) Key string (e.g. 'Cm')
                'bpm': (float) Tempo in bpm
                'melody' / 'bass': (list of dict) Melody / bass line notes, keys:
                    'onset': (float) Note onset in seconds
                    'duration': (float) Note duration in seconds
                    'pitch': (int) Closest MIDI pitch
                    'freq': (float) Fundamental frequency in Hz
                'beats': (list of dict) Beat grid notes
                    'onset': (float) Beat time in seconds
                    'index': (int) Beat index in bar (WARNING: one-based indexing is used here, first beat == 1)
                    'numerator': (int) Time signature numerator
                    'denominator': (int) Time signature denominator
        """
        data = dict()

        # parse XML
        tree = et.parse(fnXML)
        root = tree.getroot()

        # get key string
        if 'key' in root.attrib and 'mode' in root.attrib:
            data['key'] = MusicBricksIDMTTranscriberXMLConverter.convertToKeyString(int(root.attrib['key']),
                                                                                    int(root.attrib['mode']))
        for child in root:
            # get transcribed melody / bass line
            if child.tag == 'Transcribed_Tracks':
                for track in child:
                    tag = track.tag
                    if tag in ('Melody', 'Bass'):
                        data[tag.lower()] = [{'duration': float(_.attrib['duration']),
                                              'onset': float(_.attrib['start']),
                                              'freq': float(_.attrib['freq']),
                                              'pitch': int(_.attrib['midi'])} for _ in track]

            # get tempo & beat grid
            elif child.tag == 'BeatGrid':
                if 'bpm' in child.attrib:
                    data['bpm'] = float(child.attrib['bpm'])

                data['beats'] = [{'onset': float(_.attrib['onset']),
                                  'numerator': int(_.attrib['numerator']),
                                  'denominator': int(_.attrib['denominator']),
                                  'index': int(_.attrib['index'])} for _ in child]

        return data

    def createCSVFileForSonicVisualizerLayerImport(self, data, label='', targetDir=''):
        """ Converts data loaded from MusicBricksIDMTTranscriber XML result file to separate CSV files,
            which can be imported into Sonic Visualizer for visualization purpose
        Args:
            data: (dict) Data loaded with MusicBricksIDMTTranscriberXMLConverter.readXML()
                         (see function docstrings for details)
            label: (string) Label to be used for CSV file names
            targetDir: (string) Target directory, where CSV files are to be stored (default: current directory)
        """
        # convert melody & bass line to note layer CSV files
        for track in ['melody', 'bass']:
            if track in data.keys():
                MusicBricksIDMTTranscriberXMLConverter.exportNoteLayer(data[track],
                                                                       os.path.join(targetDir, '_'.join((label,
                                                                                                         track,
                                                                                                         'noteLayer.csv'))))
        # convert beat grid to time instant layer CSV file
        if 'beats' in data.keys():
            MusicBricksIDMTTranscriberXMLConverter.exportTimeInstantLayer(data['beats'],
                                                                          os.path.join(targetDir, '_'.join((label,
                                                                                                            'beats',
                                                                                                            'timeInstantsLayer.csv'))))

    @staticmethod
    def exportNoteLayer(noteSequence, fnCSV):
        """ Export note sequence as CSV file to be imported as note layer in Sonic Visualizer
        Args:
            noteSequence: (list of dict), with keys 'onset', 'pitch', and 'duration'
            fnCSV: (string) CSV file name
        """
        loudness = .8  # used as default loudness here
        with open(fnCSV, 'w') as f:
            for _ in range(len(noteSequence)):
                f.write("{},{},{},{}\n".format(noteSequence[_]['onset'],
                                               noteSequence[_]['pitch'],
                                               noteSequence[_]['duration'],
                                               loudness))

    @staticmethod
    def exportTimeInstantLayer(beats, fnCSV):
        """ Export note sequence as CSV file to be imported as note layer in Sonic Visualizer
        Args:
            beats: (list of dict), with keys 'onset', and 'index'
            fnCSV: (string) CSV file name
        """
        with open(fnCSV, 'w') as f:
            for _ in range(len(beats)):
                f.write("{},{}\n".format(beats[_]['onset'],
                                         beats[_]['index']))

    @staticmethod
    def convertToKeyString(chroma, mode):
        """ Generate key label from chroma index and major-minor mode
        Args:
            chroma: key chroma [0, 11] (0 = C, ...)
            mode: major / minor mode (0 = major, 1 = minor)
        """
        noteSpelling = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
        keyString = noteSpelling[chroma]
        if mode == 2:
            keyString += 'm'
        return keyString

if __name__ == '__main__':
    converter = MusicBricksIDMTTranscriberXMLConverter()

    # load data from XML
    data = converter.readXML(os.path.join('data', 'test.xml'))
    print('MusicBricksIDMTTranscriber results successfully loaded from test.xml')

    # export data to separate CSV files that can be imported to Sonic Visualizer annotation layers for visualization
    converter.createCSVFileForSonicVisualizerLayerImport(data,
                                                         'test',
                                                         os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                                      'data'))
    print('MusicBricksIDMTTranscriber results successfully converted to CSV files for Sonic Visualizer import')

