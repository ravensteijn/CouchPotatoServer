# -*- coding: utf-8 -*-
# Copyright 2011-2012 Antoine Bertin <diaoulael@gmail.com>
#
# This file is part of subliminal.
#
# subliminal is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# subliminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
from . import ServiceBase
from ..subtitles import get_subtitle_path, ResultSubtitle
from ..videos import Episode
from bs4 import BeautifulSoup
from guessit.language import lang_set
from subliminal.utils import get_keywords, split_keyword
import guessit
import logging
import re
import unicodedata
import urllib


logger = logging.getLogger(__name__)


class Subtitulos(ServiceBase):
    server_url = 'http://www.subtitulos.es'
    api_based = False
    languages = lang_set([u'English (US)', u'English (UK)', u'English', u'French', u'Brazilian',
                          u'Portuguese', u'Español (Latinoamérica)', u'Español (España)', u'Español',
                          u'Italian', u'Català'], strict=True)
    videos = [Episode]
    require_video = False
    required_features = ['permissive']
    # the '.+' in the pattern for Version allows us to match both '&oacute;'
    # and the 'ó' char directly. This is because now BS4 converts the html
    # code chars into their equivalent unicode char
    release_pattern = re.compile('Versi.+n (.+) ([0-9]+).([0-9])+ megabytes')

    def list_checked(self, video, languages):
        return self.query(video.path or video.release, languages, get_keywords(video.guess), video.series, video.season, video.episode)

    def query(self, filepath, languages, keywords, series, season, episode):
        request_series = series.lower().replace(' ', '_')
        if isinstance(request_series, unicode):
            request_series = unicodedata.normalize('NFKD', request_series).encode('ascii', 'ignore')
        logger.debug(u'Getting subtitles for %s season %d episode %d with languages %r' % (series, season, episode, languages))
        r = self.session.get('%s/%s/%sx%.2d' % (self.server_url, urllib.quote(request_series), season, episode))
        if r.status_code == 404:
            logger.debug(u'Could not find subtitles for %s season %d episode %d with languages %r' % (series, season, episode, languages))
            return []
        if r.status_code != 200:
            logger.error(u'Request %s returned status code %d' % (r.url, r.status_code))
            return []
        soup = BeautifulSoup(r.content, self.required_features)
        subtitles = []
        for sub in soup('div', {'id': 'version'}):
            sub_keywords = split_keyword(self.release_pattern.search(sub.find('p', {'class': 'title-sub'}).contents[1]).group(1).lower())
            if not keywords & sub_keywords:
                logger.debug(u'None of subtitle keywords %r in %r' % (sub_keywords, keywords))
                continue
            for html_language in sub.findAllNext('ul', {'class': 'sslist'}):
                language = guessit.Language(html_language.findNext('li', {'class': 'li-idioma'}).find('strong').contents[0].string.strip())
                if language not in languages:
                    logger.debug(u'Language %r not in wanted languages %r' % (language, languages))
                    continue
                html_status = html_language.findNext('li', {'class': 'li-estado green'})
                status = html_status.contents[0].string.strip()
                if status != 'Completado':
                    logger.debug(u'Wrong subtitle status %s' % status)
                    continue
                path = get_subtitle_path(filepath, language, self.config.multi)
                subtitle = ResultSubtitle(path, language, service=self.__class__.__name__.lower(), link=html_status.findNext('span', {'class': 'descargar green'}).find('a')['href'], keywords=sub_keywords)
                subtitles.append(subtitle)
        return subtitles


Service = Subtitulos
