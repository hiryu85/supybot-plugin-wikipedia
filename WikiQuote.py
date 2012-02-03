# -*- coding: utf-8 -*-

from lxml.html import HtmlElement as lxmlHtmlElement
from re import match

class QuoteElement:
    """ """
    def __init__(self, quote):
        if isinstance(quote, str):
           self._text = quote 
           self.element = None
        elif isinstance(quote, lxmlHtmlElement):
           self.element = quote
        else:
          raise ValueError('%s not is str or a lxml.html.HtmlElement instance' % \
                                                          type(quote))

    def get_text(self):
        """ Get quote text """
        if self.element == None:
           value = self._text 
        else:
            value = self.element.text_content()
        return value.encode('utf-8')

    text = property(get_text)    


class WikiQuoteFilterAssertion:
    pass


def filterQuotes(quoteElements, WQuoteFilters=[]):
    """ Iter each element of quoteElements list and filtering bad quotes.
        It returns a list of valid quotes.

     @param:  list   quoteElements    List of QuoteElements instances
     @param:  list   WQuoteFilters    List of WikiQuoteFilters instances
     @return  list   filteredQuotes   List of valid quotes
    """
    check = True
    filteredQuotes = []
    for quoteElement in quoteElements:
        quoteString = quoteElement.text
        check = True            # Reset check value at True for new 
        for WQuoteFilterInstance in WQuoteFilters:
            if not check: continue  # Go to next Iteration

            try:
                validation = WikiQuoteFilter.use(WQuoteFilterInstance,
                                                          quoteElement)
                #print '\nPreparing filter: %s\n' % WQuoteFilterInstance
                #print 'For check validity of: %s' % quoteString.upper()
                #print 'the quote passed validation?  %s' % validation

                if not validation:
                    # Search in filteredQuotes list if the string is
                    # already into list (and remove it).
                    try:
                        filteredQuotes.remove(quoteString)
                    except ValueError:
                           pass

                    # Here, skip the validation of next's filter beacause
                    # this non valid quote. 
                    check = False

                else:   # Append quote to valid quotes list
                   if quoteString not in filteredQuotes:
                      filteredQuotes.append(quoteString)

            except Exception, e:
                errmsg = 'Exception after validation of quote "%s":\n'
                errmsg += '%s (%s)\n\nvalidation filter: %s'
                print errmsg % (quoteString, type(e), e,
                                                 WQuoteFilterInstance)
                print '='*10
                import sys, traceback
                traceback.print_exc(file=sys.stdout)
                print '='*10
            #print '\n'
    return filteredQuotes


class WikiQuoteFilter:
    """ Class for inizialize and use a filter """
    @staticmethod
    def use(WikiQuoteFilterInstance, QuoteElement):
        """ Test if quoteString is a valid quote throught
            WikiQuoteFilterInstance.
            
            Return True if the quote is valid for this filter,
            otherwise False.

            @param:  inst   WikiQuoteFilterInstance    Instance of WikiQuoteFilterAbstract
            @param:  inst   QuoteElement               QuoteElement instance
            @return  boolean
        """
        if isinstance(WikiQuoteFilterInstance, WikiQuoteFilterAbstract):
            raise TypeError('Give me a valid WikiQuoteFilters')
        # WikiQuoteFilterInstance in string format?
        elif isinstance(WikiQuoteFilterInstance, str):
           if WikiQuoteFilterInstance in WikiQuoteFilters:
              WikiQuoteClass = WikiQuoteFilterInstance
              WikiQuoteFilterInstance = WikiQuoteFilters[WikiQuoteClass]
           else:
                errmsg = 'Filter %s not is registered;' % \
                                               WikiQuoteFilterInstance
                errmsg += '\nPlease add this key with filterInstance'
                errmsg += 'to the WikiQuoteFilter dictionary.'
                raise TypeError(errmsg)

        # TODO: E se non e` un'istanza di Filtro?
        Filter = WikiQuoteFilterInstance(QuoteElement)
        return Filter.validate()
      

class WikiQuoteFilterAbstract:
    """Class for filtering quotes from wikiquote.org .
       
       @param       instance   QuoteElement
       @exception   AttributeError  
    """
    def __init__(self, quote):
        if not isinstance(quote, QuoteElement):
           raise TypeError('Require QuoteElement object, %s given.' %
                                                   type(QuoteElement))
        self.element = quote


    def validate(self):
        """Try to test the string
            
            Return True if the string is valid, otherwise Fase
        """
        try:
            result = self.check()
            if not result or result == False: return False
            return True
        except WikiQuoteFilterAssertion, e:
            return False
            

    def check(self):
        """ Abstract method for checking string """
        raise NotImplementedError('Implement method check from %s' %
                                                                 self)


# ################################################## #
#                     Filters
#  
# You can create a new filters, in first time create
# a new class that extends WikiQuoteFilterAbstract 
# class.
# For register a filters add into WikiQuoteFilters dictionary
# the name of filter and the instance of new class.
#
# After that return to your class and override `check` method.
# You can validate the text through class attributes: text, quote.
#
# The "text" attr is the text of quote, while "element" attr is the 
# instance of lxml.html.HtmlElement.
# 
# ################################################## #
class ExcludeDialogues(WikiQuoteFilterAbstract):
    """Exclude long Dialogues (>200 chars) from quote result"""
    def check(self):
        """ foo """
        return len(self.element.text) < 200


class ExcludeWikipediaExternalLinks(WikiQuoteFilterAbstract):
    """ Exclude external links of wikipedia page from quotes """

    def check(self):
        """Check if the quote element childs has external link"""
        hasLink = 0
        for child in self.element.element.getiterator():
            x = child.tag == 'a'
            y = ''
               
            if x:
                hasLink += 1
        return hasLink == 0

class ExcludeCastsOfFilm(WikiQuoteFilterAbstract):
    """ Exclude text of Paragraphs `Cast` in a quotes from film """
    def check(self):
        """ Iter a childs of element and search cast string """
        pattern = r'^.+?\s—\s.+$'
    
        for child in self.element.element.getiterator():
            isActor = match(pattern, child.text.encode('utf-8'))
            #print 'Check actor:`%s` [%s] matching: %s' % (child.text,
            #                                type(child.text), isActor)
            if isActor:
               return  False

        return True

WikiQuoteFilters = {
    'NoDialogues' : ExcludeDialogues,
    'NoExternalLinks' :  ExcludeWikipediaExternalLinks,
    'NoCastsOfFilm' : ExcludeCastsOfFilm,
}


if __name__ == "__main__":
    filterValidators = [ExcludeDialogues, ExcludePhoneNumber]
    quotesToApplyFilters = [
        'Adoro l\'odore del Napalm al mattino',
        'Monta monta ciccia \
            molla! Svelto datti da fare Palla, sali su! Sali su!   \
            A vederti sembra di guardare un vecchio che cerca di   \
            scopare, te ne rendi conto Palla?! Avanti coraggio!    \
            Vai troppo piano, muoviti muoviti! Soldato Palla di    \
            lardo fai quello che vuoi ma non mi cascare di sotto,  \
            mi faresti morire di crepacuore! Su, forza, passa di la! \
            Passa di...',
        'Chiamami al numero 339-15643763'
    ]
    print '*' * 30, '\n'
    print filterQuotes(quotesToApplyFilters, filterValidators)
    print '=' * 30, '\n'
    print WikiQuoteFilter.use(ExcludeDialogues, 'io sono mirko')
    print WikiQuoteFilter.use(ExcludePhoneNumber, 'io sono mirko')
    print WikiQuoteFilter.use(ExcludePhoneNumber,
                                         'Il mio numero e` 06-9597543')
