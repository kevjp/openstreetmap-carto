from config_geo import Configuration
import datetime

class Generate_location_probs(Configuration):

    """
    Class which generates probabilitiy distributions for a specific location for a specific subpopulation.
    Methods defined generate:
        1 - A visiting location probability distribution
        2 - Distribution of daily visiting times
        3 - Distribution of duration times spent at location
        4 - Distribution of times before next visit to location

    """

    def __init__(self, location, subpop_id):
        # Inherit everything from Configuration class
        super().__init__()
        key_arg = location + '_' + str(subpop_id)
        # Populate probability distribution dictionaries
        # Dictionary of daily prob distributions of visiting a location
        self.prob_of_visiting_dict[key_arg] = self.init_prob_of_visiting_dist()
        # Dictionary of time distributions across a day period
        self.time_of_visit_dict[key_arg] = self.init_visiting_times_dist

    def init_prob_of_visiting_dist(self, max_pos_skew = -5, max_neg_skew = 5):
            """
            Generates a matrix of probability distributions. Each row represents number of days passed due date to visit location
            Each row contains Gaussian distribution of probability values form 0-1 where as the number of days passed due date increases so the probability distribution becomes more negatively skewed to higher probability values indicating increasing urgency of visiting a location
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
                self._probabilities[:,idx] = self._sm_probabilities[:,idx] - np.min(self._sm_probabilities[:,idx])

                # standardise all values between 0 and 1
                self._probabilities[:,idx] = self._sm_probabilities[:,idx] / np.max(self._sm_probabilities[:,idx])
            return self._probabilities


    def init_visiting_times_dist(self, start = 0, stop = 840, skewness = 0, mean = 420, size = 1000):

        self._minutes = np.zeroes((size,))
        minutes = skewnorm.rvs(a = skewness,loc=mean, size=size)
        # shift values so that lowest value is 0
        minutes = minutes - np.min(minutes)
        # standardise all values between 0 and 840
        minutes = (minutes / np.max(minutes)) * stop
        # Translate minutes into times  default set to times between 8am to 10pm
        for i, m in enumerate(minutes):
            # generate a datetime.time object for each element in the time distribution
            self._minutes[i] = (datetime.datetime.combine(datetime.date(1,1,1),datetime.time(8, 0)) + datetime.timedelta(0, 0,0,0,m)).time()

        return self._minutes




