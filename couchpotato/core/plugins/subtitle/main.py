from couchpotato import get_session
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from couchpotato.core.settings.model import Library, FileType
from couchpotato.environment import Env
import subliminal

log = CPLog(__name__)


class Subtitle(Plugin):

    services = ['opensubtitles', 'thesubdb', 'subswiki']

    def __init__(self):
        addEvent('renamer.before', self.searchSingle)

    def searchLibrary(self):

        # Get all active and online movies
        db = get_session()

        library = db.query(Library).all()
        done_status = fireEvent('status.get', 'done', single = True)

        for movie in library.movies:

            for release in movie.releases:

                # get releases and their movie files
                if release.status_id is done_status.get('id'):

                    files = []
                    for file in release.files.filter(FileType.status.has(identifier = 'movie')).all():
                        files.append(file.path);

                    # get subtitles for those files
                    subliminal.list_subtitles(files, cache_dir = Env.get('cache_dir'), multi = True, languages = self.getLanguages(), services = self.services)

        #db.close()

    def searchSingle(self, group):

        if self.isDisabled(): return

        available_languages = sum(group['subtitle_language'].itervalues(), [])
        downloaded = []
        for lang in self.getLanguages():
            if lang not in available_languages:
                download = subliminal.download_subtitles(group['files']['movie'], multi = True, force = False, languages = [lang], services = self.services, cache_dir = Env.get('cache_dir'))
                downloaded.extend(download)

        for d_sub in downloaded:
            group['files']['subtitle'].add(d_sub.path)
            group['subtitle_language'][d_sub.path] = [d_sub.language]

    def getLanguages(self):
        return [x.strip() for x in self.conf('languages').split(',')]
