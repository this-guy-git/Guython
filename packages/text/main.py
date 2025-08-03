def reverse(s):
    """Reverse a string"""
    return s[::-1]

def toupper(s):
    """Convert string to uppercase"""
    return s.upper()

def tolower(s):
    """Convert string to lowercase"""
    return s.lower()

def capitalize(s):
    """Capitalize the first character"""
    return s.capitalize()

def titlecase(s):
    """Convert string to title case"""
    return s.title()

def countsubstring(s, sub):
    """Count occurrences of a substring"""
    return s.count(sub)

def startswith(s, prefix):
    """Check if string starts with prefix"""
    return s.startswith(prefix)

def endswith(s, suffix):
    """Check if string ends with suffix"""
    return s.endswith(suffix)

def removewhitespace(s):
    """Remove all whitespace"""
    return "".join(s.split())

def isnumeric(s):
    """Check if string is numeric"""
    return s.isnumeric()

def strip(s):
    """Strip whitespace from both ends"""
    return s.strip()

def lstrip(s):
    """Strip whitespace from the left"""
    return s.lstrip()

def rstrip(s):
    """Strip whitespace from the right"""
    return s.rstrip()

def stripchars(s, chars):
    """Strip specified characters from both ends"""
    return s.strip(chars)

def lstripchars(s, chars):
    """Strip specified characters from the left"""
    return s.lstrip(chars)

def rstripchars(s, chars):
    """Strip specified characters from the right"""
    return s.rstrip(chars)

def replace(s, old, new, count=-1):
    """
    Replace occurrences of 'old' with 'new' in string 's'.
    If count is specified, replaces up to 'count' times.
    """
    return s.replace(old, new, count)