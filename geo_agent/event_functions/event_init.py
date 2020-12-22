import numpy as np
from scipy.stats import skewnorm
import scipy.stats as stats



class Eventinit():

    """
    Class to hold all event initialisation functions for all events specify names and corresponding event instances
    in event config json.
    """

    # class level variables
    # _probabilities = np.zeros((100, 10))

    def __init__(self):
        self._probabilities = np.zeros((100, 10))
        self._starttime = np.zeros((100,), dtype='datetime64[s]')
        self._minutes = np.zeros((100,))
        self._days = np.zeros((100,))



    def init_event_occuring(self,max_pos_skew = -5, max_neg_skew = 5):

        """
        Initialise probabilities of event occurring. Generates a matrix of
        probability distributions. Each row represents number of days passed due
        date to visit location. Each row contains Gaussian distribution of
        probability values form 0-1 where as the number of days passed due date
        increases so the probability distribution becomes more negatively skewed
         to higher probability values indicating increasing urgency of visiting
         a location
        """


        # Define list of distributions relating to the number of frames since last visited
        # so let's say we base it over 100 frames
        skewness_values  = np.linspace(max_neg_skew, max_pos_skew, 100)
        # generate 1000 random values for each skewness setting
        dist_sample_size = 1000

        # initialize the _sm_probabilities numpy array
        self._probabilities = np.zeros((dist_sample_size, len(skewness_values)))

        # Populate numpy array with probabilities changing the skewness of the prob distribution depending on how long it is since the agent last visited a specific destination
        for idx, skewness in enumerate(skewness_values):
            # generate _sm_probabilities distributions for each time frame
            self._probabilities[:,idx] = skewnorm.rvs(a = skewness,loc=100, size=dist_sample_size)

            # shift values so that lowest value is 0
            self._probabilities[:,idx] = self._probabilities[:,idx] - np.min(self._probabilities[:,idx])

            # standardise all values between 0 and 1
            self._probabilities[:,idx] = self._probabilities[:,idx] / np.max(self._probabilities[:,idx])
        return self._probabilities

    #def init_event_starttime(self, start = 0, stop = 840, skewness = 0, mean = 420, size = 1000):
    def init_event_starttime(self, start = 0, stop = 500, skewness = 0, mean = 250, size = 1000):

        """
        Generate a distribution of start times for going to an event

        """
        self._starttime = np.zeros((size,), dtype='datetime64[m]')
        starttime = skewnorm.rvs(a = skewness,loc=mean, size=size)
        # shift values so that lowest value is 0
        starttime = starttime - np.min(starttime)
        # standardise all values between 0 and 840 relating to 14 hours of available shopping time
        starttime = (starttime / np.max(starttime)) * stop
        # Translate minutes into times  default set to times between 8am to 10pm
        for i, m in enumerate(starttime):
            m = int(round(m)) # numpy timedelta only accepts whole int values
            # generate a datetime.time object for each element in the time distribution
            #self._starttime[i] = np.datetime64('1-01-01 08:00') + np.timedelta64(m, 'm')
            self._starttime[i] = np.datetime64('1-01-01 00:00') + np.timedelta64(m, 'm')
            # self._starttime[i] = (datetime.combine(date(1,1,1),time(8, 0)) + timedelta(0, 0,0,0,m)).time()

        return self._starttime


    def init_time_spent_at_event(self, start = 0, stop = 120, skewness = 0, mean = 45, sd = 20, size = 1000):

        """
        generate distribution of time periods spent at event location
        """
        min_list = []
        minutes = stats.truncnorm.rvs((start - mean)/sd, (stop - mean)/sd,loc=mean, size=size, scale=sd)
        # Convert values over to timedelta values
        for i, m in enumerate(minutes):
            m = int(round(m)) # numpy timedelta only accepts whole int values
            min_list.append(np.timedelta64(m, 'm'))
        self._minutes = np.array(min_list)

        return self._minutes


    #def init_time_before_event_occurs_again(self, start = 0, stop = 10, mean = 7, sd = 2, size = 1000):
    def init_time_before_event_occurs_again(self, start = 0, stop = 0.05, mean = 0.035, sd = 0.0175, size = 1000):

        """
        generate a distribution of time periods (in minutes) before the event will happen again
        """

        day_list = []
        days = stats.truncnorm.rvs((start - mean)/sd, (stop - mean)/sd,loc=mean, size=size, scale=sd)
        # Convert values over to timedelta values
        for i, d in enumerate(days):
            mins = d * 1440
            mins = int(round(mins))# numpy timedelta only accepts whole int values
            day_list.append(np.timedelta64(mins, 'm'))
        self._days = np.array(day_list)

        return self._days





