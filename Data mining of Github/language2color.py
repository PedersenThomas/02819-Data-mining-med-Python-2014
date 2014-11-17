_colors = {"TypeScript": (49,133,156),
           "JavaScript": (241,224,90),
           "C": (85,85,85),
           "Python": (53,129,186),
           "Java": (176,114,25),
           "VHDL": (84,57,120),
           "Scala": (125,211,176),
           "Ada": (2,248,140),
           "Lua": (250,31,161),
           "C#": (90,37,162),
           "Dart": (204,204,204),
           "C++": (243,75,125),
           "Visual Basic": (148,93,183),
          }

def get_color(language):
    if language in _colors:
        R, G, B = _colors[language]
        return (R/255., G/255., B/255.)
    else:
        return (0,0,0)