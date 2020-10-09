import datetime

"""
Updates clock time for agent based simulation. Class is updated at each tstep

"""
class Clock():

    def __init__(self):
        self._clock = {
            "tstep" : 0,
            "time" : datetime.datetime.min,
            "day" : datetime.datetime.today()
        }

    @property
    def tstep_count(self):
        return self._clock["tstep"]

    @property
    def current_time(self):
        return self._clock['time']

    @property
    def day(self):
        return self._clock['day']

    def update_tstep(self):
        self._clock["tstep"] += 1
        # update time on clock
        self.update_time()
        if self._clock["tstep"] % 1440 == 0:
            self.update_day()

    def update_time(self):
        # create 1 minute time delta unit
        minute = datetime.timedelta(0, 0,0,0,1) # time delta in minutes
        # add 1 minute to the clock
        clock_time = (datetime.datetime.min + minute).time()
        # update dictionary _clock
        self._clock["time"] = clock_time


    def update_day(self):
        # create 1 day time delta
        day = datetime.timedelta(days=1)
        # add 1 day to the clock
        day_of_the_week = (datetime.datetime.min + day).weekday()
        # update dictionary _clock
        self._clock["day"] = day_of_the_week

