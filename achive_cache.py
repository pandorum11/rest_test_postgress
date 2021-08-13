from datetime import datetime

# -----------------------------------------------------------------------------

# Cache operating classs

class AchiveCache:

    """
    Cache base on dictionary rule, takes 1 arg - buffer size (int)
    at constructor and uses next operations to process it :
    destroy_cache_by_size()
    add_to_cache()
    check_available()
    get_from_cache()
    del_chain_asin()
    asignment to cache throuh object
    """

    def __init__(self, buffer):

        self.cache_buffer = buffer
        self.global_cash = {}
        self.time_store = {}

    def destroy_cache_by_size(self):
        """
        This function deletes the last element in sorted self.time_store
        sorted by data. It finds the oldest global value which had to delete.
        While working add_to_cache, thet function refreshes values according to
        requests. Thets how it knows which requests are less in use and has to
        be removed.
        """

        # Get the row which was wrote the first
        sorted_time = sorted(self.time_store)
        first_row = self.time_store[sorted_time[0]]
        # Then take and process value of time_store
        del self.time_store[sorted_time[0]]
    
        asin = first_row[:10]
        page = first_row[10:]

        # and then delete it from global_cash also

        del self.global_cash[asin][int(page)]
    
        return


    def add_to_cache(self, asin, page, data):
        """
        Function provides adding items to cache
        """

        # in case of time_store owerflow initiating destroing procedure

        if len(self.time_store) > self.cache_buffer:

            self.destroy_cache_by_size()
            

        if asin in self.global_cash:

            if page not in self.global_cash[asin]:

                pass

            else:

                # refreshing

                # deleting the time_store mark
                del self.time_store[self.global_cash[asin][page]['date']]

                # replacing time_store mark by new value, for tracking 
                self.time_store[datetime.now()] = asin + str(page)

                return

        else:

            self.global_cash[asin] = {}


        # asighning data to cache
        self.global_cash[asin][page] = data

        # asighning data to timestore
        self.time_store[datetime.now()] = asin + str(page)

        return


    def check_available(self, asin, page):

        """
        Function chek availability of curent position in cash
        """

        if asin in self.global_cash:

            if page in self.global_cash[asin]:

                return True
            else:

                return False
        else:

            return False


    def get_from_cache(self, asin, page):

        return self.global_cash[asin][page]


    def del_chain_asin(self, asin):

        # this deletes all chain with product asin

        if asin in self.global_cash:

            # delete chain from time_store
            for el in self.global_cash[asin]:

                del self.time_store[self.global_cash[asin][el]['date']]

            # delete from cache
            del self.global_cash[asin]

        return