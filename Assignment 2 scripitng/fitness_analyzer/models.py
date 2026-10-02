# This class stores the participants identity and their measurements.
class Participant:
    def __init__(self, participant_id, name, baseline_hr, baseline_skin, baseline_temp):
        self.participant_id = participant_id
        self.name = name
        self.baseline_hr = baseline_hr
        self.baseline_skin = baseline_skin
        self.baseline_temp = baseline_temp

# This class stores one single reading from a session.
class Observation:
    def __init__(self, timestamp, heart_rate, skin_response, temperature, activity_level, signal_quality):
        self.timestamp = timestamp
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level
        self.signal_quality = signal_quality

# This class groups many observations together for one participant and one session.
class Session:
    def __init__(self, session_id, participant):
        self.session_id = session_id
        self.participant = participant
        self._observations = []

    def add_observation(self, observation):
        self._observations.append(observation)

    @property
    def observations(self):
        #gives back the observations in time order.
        return sorted(self._observations, key=lambda item: item.timestamp)
