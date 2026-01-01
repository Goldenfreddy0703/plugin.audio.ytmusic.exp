from dataclasses import dataclass
from typing import Literal, TypedDict

from typing import List, Dict, Any, Optional


@dataclass
class LyricLine:
    """Represents a line of lyrics with timestamps (in milliseconds).

    :param text (str): The Songtext.
    :param start_time (int): Begin of the lyric in milliseconds.
    :param end_time (int): End of the lyric in milliseconds.
    :param id (int): A Metadata-Id that probably uniquely identifies each lyric line.
    """

    text: str
    start_time: int
    end_time: int
    id: int

    @classmethod
    def from_raw(cls, raw_lyric: Dict[str, Any]) -> "LyricLine":
        """
        Converts lyrics in the format from the api to a more reasonable format

        :param raw_lyric: The raw lyric-data returned by the mobile api.
        :return LyricLine: A `LyricLine`
        """
        text = raw_lyric["lyricLine"]
        cue_range = raw_lyric["cueRange"]
        start_time = int(cue_range["startTimeMilliseconds"])
        end_time = int(cue_range["endTimeMilliseconds"])
        id = int(cue_range["metadata"]["id"])
        return cls(text, start_time, end_time, id)


class Lyrics(TypedDict):
    lyrics: str
    source: Optional[str]
    hasTimestamps: Literal[False]


class TimedLyrics(TypedDict):
    lyrics: List[LyricLine]
    source: Optional[str]
    hasTimestamps: Literal[True]
