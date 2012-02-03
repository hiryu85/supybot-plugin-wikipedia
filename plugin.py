###
# Copyright (c) 2009, Mirko 'hiryu' Chialastri
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


from supybot.utils.web import urlquote
from lxml.html import etree, parse
from cStringIO import StringIO
from random import choice

from WikiQuote import QuoteElement, filterQuotes, ExcludeDialogues

def getStringOptions(optionsDictionary):
    """ Return search options in string format """
    return ','.join([ '%s=%s' % (key, optionsDictionary[key]) 
                                       for key in optionsDictionary ])


class SearchWithNoResult():
    def __init__(self, keyword, url, optDict, tips=None):
        self.keyword = keyword
        self.url = url
        self.tips = tips 
        self.options = optDict

    def getStringOptions(self):
        """ Return search options in string format from the exception """
        return getStringOptions(self.options)

    def __str__(self):
        meanTips = self.tips if bool(self.tips) else ''
        return "<WikipediaSearch No result for `%s` %s with options:%s>" %\
                                (self.keyword, '(tips: %s)' % meanTips,
                                               self.getStringOptions())
    

class Wikipedia(callbacks.Plugin):
    """Add the help for "@plugin help Wikipedia" here
    This should describe *how* to use this plugin."""
    threaded = True
    public = True


    def __init__(self, irc):
        self.__parent = super(Wikipedia, self)
        self.__parent.__init__(irc)

    def _makeOptsDict(self, optlist, replyTo=None):
        """ Create a options dictionary from wrap callbacks optlist"""
        optDict = dict([ (opt[0], opt[1]) for opt in optlist ])
        #print replyTo
        if 'lang' not in optDict: 
            if replyTo:  # channel lang option
                optDict['lang'] = self.registryValue('defaultLanguage',
                                                              replyTo)
            else: # default lang option
                optDict['lang'] = self.registryValue('defaultLanguage')
        return optDict


    url_search = 'http://%s.%s/w/index.php?search=%s&go=Vai'
    def _searchKeyword(self, keyword, optDict, domain='wikipedia.org'):
        """ Search keyword from wikipedia.org

            Return a file descriptor with a result.
            Raise an SearchWithNoResult Exception when the key isn't in 
            Wikipedia. 
        """
        headers = utils.web.defaultHeaders
        headers['Referer'] = 'http://www.%s' % domain
        message = 'Search from supybot.plugins.Wikipedia.search at %s' % domain
        self.log.debug(message)
        fd = utils.web.getUrlFd(self.url_search % (optDict['lang'], domain,  
                                          urlquote(keyword)), headers)
        # Search page 
        if 'search=' in fd.geturl(): 
            url = fd.geturl()
            p = parse(StringIO(fd.read())) 
            tips = ''
            try:
                els = p.xpath('//div[@class="searchdidyoumean"]/a')[0]
                tips = els.text_content()
                url = 'http://%s.%s%s' % (optDict['lang'], domain, 
                 [tag[1] for tag in els.items() if tag[0] == 'href'][0])
                #res = 'Did you mean: %s - %s' % (tips, url)
                raise SearchWithNoResult(keyword, url, optDict, tips)
            except IndexError, e:
                #res = '%s not found - %s' % (keyword, url)     
                raise SearchWithNoResult(keyword, url, optDict)           
            except Exception, e:
                args = getStringOptions(optDict)
                errmsg = 'Unhandled exception in wikipedia search method\n'
                errmsg += 'from supybot.plugins.Wikipedia\n'
                errmsg += '%s.'
                self.log.warning(errmsg % e)
        return fd



    # ######################### #
    #        Callbacks
    #
    # ######################### #
    def wikipedia(self, irc, msg, args, optlist, keyword):
        """{--lang|par} <value>} <keyword>

            Search <keyword> in <lang>.Wikipedia.org
        """
        replyTo = msg.args[0]
        options = self._makeOptsDict(optlist, replyTo)
        par = int(options['p']) if 'p' in options else 1

        try:
            searchFd = self._searchKeyword(keyword, options)
        except SearchWithNoResult, e:
            if not e.tips:
                res = '\x02%s\x02 not found - \x1f%s\x1f' % (e.keyword, e.url)
            else:
                res = 'Did you mean: \x02%s\x02? \x1f%s\x1f' % (e.tips, e.url)
            irc.reply(res)
            return

        except Exception, e:
            errmsg = 'Unhandled exception from supybot.plugins.Wikipedia.wiki.\n'
            errmsg += 'Parsing error while i trying to parse the result of:'
            errmsg += 'keyword:%s   with   options:%s'
            errmsg += '\n'
            errmsg += 'The Exception is %s - %s'
            self.log.warning(errmsg % (keyword, getStringOptions(options),
                             type(e), e))
            return 

        # The keyword has been founded at wikipedia
        b = StringIO(searchFd.read())
        p = parse(b)

        # is disambiguid term?
        try:
            XpathExpression = "//a[@class='image'][contains(@href, 'Disamb')][contains(@href, '.svg')]"
            el = p.xpath(XpathExpression)[0]
            res = 'disambiguation in term \x02%s\x02 - \x1f%s\x1f' % \
                                          (keyword, searchFd.geturl())
            self.log.debug("Wikipedia.wiki plugins: Search with a disambiguid term (%s)" % keyword)
            irc.reply(res)
        except IndexError, e:
            # The keyword has been fonded and is a valid term
            while True:       # This loop because with some terms the
                              # first paragraph is empty
                XpathExpression = "id('bodyContent')/p[%s]" % par
                res = p.xpath(XpathExpression)[0].text_content().encode('utf-8')
                self.log.debug("Wikipedia.wiki looping in %d th paragraphs:: %s" % (par, res.strip()))
                if res.strip() != '':
                   # Stop iteration and send result to channel
                    irc.reply('\x1f%s\x1f - %s' % (searchFd.geturl(), res))
                    break
                par += 1
        except Exception, e:
            self.log.error("Error in parse method of Wikimedia.wiki: %s [%s] \
                          for keyword %s %s" % (type(e), e, keyword,
                                           getStringOptions(options)))
    wiki = wrap(wikipedia, 
                [
                  optional(
                   getopts({'lang' : 'something', 'p' : 'int'}),
                  ),
                  'text',
                 ])

    def wikiquote(self, irc, msg, args, optlist, keyword):
        """{--lang <value>}  <keyword>

        Search <keyword> quotes from <lang>.wikiquote.org
        """
        replyTo = msg.args[0]
        options = self._makeOptsDict(optlist, replyTo)
        #par = int(options['p']) if 'p' in options else 1

        try:
            searchFd = self._searchKeyword(keyword, options,
                                                 domain='wikiquote.org')
        except SearchWithNoResult, e:
            if not e.tips:
                res = '\x02%s\x02 not found - \x1f%s\x1f' % (e.keyword, e.url)
            else:
                res = 'Did you mean: \x02%s\x02? \x1f%s\x1f' % (e.tips, e.url)
            irc.reply(res)
            return

        except Exception, e:
            errmsg = 'Unhandled exception from supybot.plugins.Wikipedia.quote.\n'
            errmsg += 'Parsing error while i trying to parse the result of:'
            errmsg += 'keyword:%s   with   options:%s'
            errmsg += '\n'
            errmsg += 'The Exception is %s - %s'
            self.log.warning(errmsg % (keyword, getStringOptions(options),
                             type(e), e))
            return 

        # The keyword has been founded at wikipedia
        b = StringIO(searchFd.read())
        p = parse(b)
        quotes = []
        try:
            XpathExpression = "//div[@id='bodyContent']/h2/span[@class='mw-headline' and @id]"
            elements = p.xpath(XpathExpression)
            for title in elements:
                headline = title.getparent()
                if headline.tag == 'h2':
                   #print 'Quote section: %s' % headline.text_content()
                   iterSiblings = headline.itersiblings('ul')
                   quoteLists = [] if not iterSiblings else iterSiblings

                   for quoteULContainer in quoteLists:
                       for li in quoteULContainer.getchildren(): 
                           if li.tag == 'li':
                              quote = QuoteElement(li)
                              quotes.append(quote)
                        
            # Filtering QuoteList with WikiQuote.filterQuotes
            #print 'Filtering:\n'
            #print quotes

            # You can see the filter action in WikiQuote.py file
            WQuoteFilters = ['NoDialogues', 'NoExternalLinks', 
                                                       'NoCastsOfFilm']
            quotes = filterQuotes(quotes, WQuoteFilters)

            #print [ qel for qel in quotes ]
            #print 'After filtering, quote list is:'
            #print quotes 

            if len(quotes) > 1:
                quote = choice(quotes)
                irc.reply(quote)
            else:
                irc.reply('No quotes found for \x02%s\x02 - %s' % \
                                         (keyword, searchFd.geturl()))
        except IndexError, e:
                print e
        

    quote = wrap(wikiquote, [ optional(
                    getopts({'lang' : 'something'}
             )), 'text'])

Class = Wikipedia


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
