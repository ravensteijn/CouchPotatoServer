from couchpotato.core.logger import CPLog
from string import ascii_letters, digits
from urllib import quote_plus
import re
import unicodedata

log = CPLog(__name__)


def toSafeString(original):
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    cleanedFilename = unicodedata.normalize('NFKD', toUnicode(original)).encode('ASCII', 'ignore')
    return ''.join(c for c in cleanedFilename if c in valid_chars)

def simplifyString(original):
    string = stripAccents(original.lower())
    string = toSafeString(' '.join(re.split('\W+', string)))
    split = re.split('\W+|_', string.lower())
    return toUnicode(' '.join(split))

def toUnicode(original, *args):
    try:
        if isinstance(original, unicode):
            return original
        else:
            try:
                return unicode(original, *args)
            except:
                try:
                    return ek(original, *args)
                except:
                    raise
    except UnicodeDecodeError:
        log.error('Unable to decode value: %s... ' % repr(original)[:20])
        ascii_text = str(original).encode('string_escape')
        return toUnicode(ascii_text)

def ek(original, *args):
    if isinstance(original, (str, unicode)):
        try:
            from couchpotato.environment import Env
            return original.decode(Env.get('encoding'))
        except UnicodeDecodeError:
            raise

    return original

def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def stripAccents(s):
    return ''.join((c for c in unicodedata.normalize('NFD', toUnicode(s)) if unicodedata.category(c) != 'Mn'))

def tryUrlencode(s):
    new = u''
    if isinstance(s, (dict)):
        for key, value in s.iteritems():
            new += u'&%s=%s' % (key, tryUrlencode(value))

        return new[1:]
    else:
        for letter in toUnicode(s):
            try:
                new += quote_plus(letter)
            except:
                new += letter

    return new

def replace_special_characters(s):
    s = s.replace(unichr(252), 'ue')
    s = s.replace(unichr(220), 'Ue')
    s = s.replace(unichr(228), 'ae')
    s = s.replace(unichr(196), 'Ae')
    s = s.replace(unichr(246), 'oe')
    s = s.replace(unichr(214), 'Oe')
    return s
