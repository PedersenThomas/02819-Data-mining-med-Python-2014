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
           "F#": (184,69,252),
           "Emacs Lisp": (192,101,219),
           "Standard ML": (220,86,109),
           "CSS": (86,61,124),
           "Ruby": (112,21,22),
           "PHP": (79,93,149),
           "VimL": (25,156,75),
           "Rust": (222,165,132),
           "Shell": (137, 224,81),
           "CoffeeScript": (36,71,118),
           "ActionScript": (227,73,26),
           "HaXe": (255,109,81),
           "OCaml": (59,225,51),
           "Logos": (204,204,204),
           "PowerShell": (204,204,204),
          }

def get_color(language):
    if language in _colors:
        R, G, B = _colors[language]
        return (R/255., G/255., B/255.)
    else:
        print language
        return (0,0,0)