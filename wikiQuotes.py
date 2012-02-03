class WikiQuoteFilterAssertion:
    pass


def filterQuotes(quoteElements, WQuoteFilters=[]):
    """ Iter each element of quoteElements list and filtering bad quotes.
        It returns a list of valid quotes.

     @param:  list   quoteElements    List of string (quotes)
     @param:  list   WQuoteFilters    List of WikiQuoteFilters instance
     @return  list   filteredQuotes   List of valid quotes
    """
    check = True
    filteredQuotes = []
    for quoteString in quoteElements:
        check = True            # Reset check value at True for new 
        for WQuoteFilterInstance in WQuoteFilters:
            if not check: continue  # Go to next Iteration

            try:
                validation = WikiQuoteFilter.use(WQuoteFilterInstance,
                                                          quoteString)
                print '\nPreparing filter: %s\n' % WQuoteFilterInstance
                print 'For check validity of: %s' % quoteString.upper()
                print 'the validation result is:  %s' % validation

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
                errmsg += '%s (%s)\n\nvalidation fiter: %s'
                print errmsg % (quoteString, type(e), e,
                                                 WQuoteFilterInstance)
            print '\n'
    return filteredQuotes


class WikiQuoteFilter:
    """ Class for inizialize and use a filter """
    @staticmethod
    def use(WikiQuoteFilterInstance, quoteString):
        """ Test if quoteString is a valid quote throught
            WikiQuoteFilterInstance.
            
            Return True if the quote is valid for this filter,
            otherwise False.

            @param:  inst   WikiQuoteFilterInstance    Instance of WikiQuoteFilterAbstract
            @param:  str    quoteString                Quote
            @return  boolean
        """
        if isinstance(WikiQuoteFilterInstance, WikiQuoteFilterAbstract):
            raise ValueError('Give me a valid WikiQuoteFilters')
        Filter = WikiQuoteFilterInstance(quoteString)
        return Filter.validate()
      

class WikiQuoteFilterAbstract:
    """ Class for filtering quotes from wikiquote.org """
    def __init__(self, quoteString):
        self.quote = quoteString
        if not isinstance(self.quote, str):
           raise AttributeError('Require string, %s given.' %
                                                    type(quoteString))
        #self.validate()

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


class ExcludeDialogues(WikiQuoteFilterAbstract):
    """ Exclude long Dialogues from quote result """
    def check(self):
        """ foo """
        return len(self.quote) < 200


class ExcludePhoneNumber(WikiQuoteFilterAbstract):
    """ Exclude long Dialogues from quote result """

    def check(self):
        """ foo """
        from re import search
        # +23 123213232321
        # +23-123213232321
        res = search(r'\+?\d+(\s\-)?(\d{6,12})', self.quote)
        return res is  None
          

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
