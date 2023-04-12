from .contextual import Contextual
from .recommender import Recommender
import random

from ..track import Track


class NewWay(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog, tracks_with_diverse_recs_redis):
        self.tracks_redis = tracks_redis
        self.fallback = Contextual(tracks_with_diverse_recs_redis, catalog)
        self.catalog = catalog
        self.tracks = set()
        self.artists = set()

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            res_idx = -1
            next_track = Track(-1, "", "", [-1])
            while next_track.track != -1 and next_track.track not in self.tracks and \
                    next_track.artist != "" and next_track.artist not in self.artists:
                res_idx = self.fallback.recommend_next(user, prev_track, prev_track_time)
                next_track = self.catalog.from_bytes(self.tracks_redis.get(res_idx))
            self.tracks.add(next_track.track)
            self.artists.add(next_track.artist)
            return res_idx

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if not recommendations:
            res_idx = -1
            next_track = Track(-1, "", "", [-1])
            while next_track.track != -1 and next_track.track not in self.tracks and \
                    next_track.artist != "" and next_track.artist not in self.artists:
                res_idx = self.fallback.recommend_next(user, prev_track, prev_track_time)
                next_track = self.catalog.from_bytes(self.tracks_redis.get(res_idx))
            self.tracks.add(next_track.track)
            self.artists.add(next_track.artist)
            return res_idx

        shuffled = list(recommendations)
        random.shuffle(shuffled)
        res_idx = shuffled[0]
        next_track_res = self.catalog.from_bytes(self.tracks_redis.get(res_idx))
        for next_track_id in shuffled:
            next_track = self.tracks_redis.get(next_track_id)
            next_track = self.catalog.from_bytes(next_track)
            if next_track.track != -1 and next_track.track not in self.tracks and \
                next_track.artist != "" and next_track.artist not in self.artists:
                next_track_res = next_track
                res_idx = next_track_id
                break
        self.tracks.add(next_track_res.track)
        self.artists.add(next_track_res.artist)
        return res_idx

