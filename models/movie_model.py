from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Actor:
    name: str
    movie_id: str
    actor_id: str

@dataclass
class Movie:
    movie_id: str
    title: str
    year: int
    rating: float
    duration: int
    actors: List[Actor]
    metascore: Optional[int] = None

    def to_dict(self):
        return {
            'title': self.title,
            'year': self.year,
            'rating': self.rating,
            'duration': self.duration,
            'metascore': self.metascore,
            'actors': [{"name":actor.name, "actor_id":actor.actor_id} for actor in self.actors] if self.actors else []
        }