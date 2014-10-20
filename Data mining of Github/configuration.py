import ConfigParser

class Configuration(object):
    """description of class"""

    def __init__(self, filename):
        self.config = ConfigParser.ConfigParser({'port':'27017'})
        self.config.read(filename)

    @property
    def 
