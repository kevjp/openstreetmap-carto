import datetime
import numpy as np

"""
Updates clock time for agent based simulation. Class is updated at each tstep

"""
class Clock():


    def __init__(self):
        self._clock = {
            "tstep" : 0,
            "time" : np.datetime64('1-01-01 00:00'),
            # create time in minutes
            "time_mins" : self.convert_numpy_datetime64_to_mins(),
            "day" : datetime.datetime.today()
        }

    @property
    def tstep_count(self):
        return self._clock["tstep"]

    @property
    def current_time(self):
        return self._clock['time_mins']

    @property
    def day(self):
        return self._clock['day']

    def update_tstep(self):
        self._clock["tstep"] += 1
        # update time on clock
        self._update_time()
        if self._clock["tstep"] % 1440 == 0:
            self._update_day()

    def convert_numpy_datetime64_to_mins(self, np_datetime64 = np.datetime64('1-01-01 00:00')):
        """
        Convert numpy datetime64 to a minute representation of the time component
        """
        day_obj= np_datetime64.astype('datetime64[D]')
        # Converts time element to value representing the number of mins
        time_mins = (np_datetime64 - day_obj).astype('int')
        return time_mins

    def _update_time(self):

        # add 1 minute to the clock
        self._clock["time"] = self._clock["time"] + np.timedelta64('1', 'm')
        self._clock["time_mins"] = self.convert_numpy_datetime64_to_mins(np_datetime64 = self._clock["time"])

    def day_of_week_num(self, numpy_datetime_obj):
        """
        return day of the week as integer 0= Mon, 6=Sun
        """
        return (numpy_datetime_obj.astype('datetime64[D]').view('int64') - 4) % 7



    def _update_day(self):
        # create 1 day time delta
        day = np.timedelta64('1', 'D')
        # add 1 day to the clock
        day_of_the_week = self.day_of_week_num((self._clock["time"] + day))
        # update dictionary _clock
        self._clock["day"] = day_of_the_week



