from datetime import timedelta, time
import pandas as pd

def normalize_minutes(minutes: pd.Series) -> pd.Series:
    """
    Normalize a time string in the format 'HH:MM:SS' to the total number of seconds.
    
    Args:
        minutes (pd.Series): A series of time strings in the format 'HH:MM:SS'.
    
    Returns:
        pd.Series: The total number of seconds.
    """

    pad = '00'
    keys = ['hours', 'minutes', 'seconds']
    parts = minutes.split(':')
    parts = list(filter(lambda x: x != '', parts))

    if any(not _.isdigit() for _ in parts):
        parts = []
    
    parts = map(int, [pad] * (3 - len(parts)) + parts)
    return timedelta(**dict(zip(keys, parts))).seconds

def normalize_double_value(value: str | int | float, empty_value=None) -> float | None:
    output = empty_value

    if isinstance(value, str):
        value = value.strip().replace(',', '.')
        output = float(value) if value.isdigit() else empty_value
    
    elif isinstance(value, (int, float)):
        output = float(value)
    
    return output

def normalize_integer_value(value: str | int | float, empty_value=None) -> int | None:
    output = empty_value

    if isinstance(value, str):
        value = value.strip()
        output = int(value) if value.isdigit() else output
    
    elif isinstance(value, (int, float)):
        output = int(value)
    
    return output

def normalize_string_value(name: str, empty_value=None) -> str | None:
    name = str(name)
    name = name.strip()
    return name if name != '' else empty_value

normalizers = dict(
    gameId=normalize_string_value,
    teamId=normalize_string_value,
    teamCity=normalize_string_value,
    teamName=normalize_string_value,
    teamTricode=normalize_string_value,
    teamSlug=normalize_string_value,
    personId=normalize_string_value,
    firstName=normalize_string_value,
    familyName=normalize_string_value,
    nameI=normalize_string_value,
    playerSlug=normalize_string_value,
    position=normalize_string_value,
    comment=normalize_string_value,
    jerseyNum=normalize_integer_value,
    minutes=normalize_minutes,
    fieldGoalsMade=normalize_integer_value,
    fieldGoalsAttempted=normalize_integer_value,
    fieldGoalsPercentage=normalize_double_value,
    threePointersMade=normalize_integer_value,
    threePointersAttempted=normalize_integer_value,
    threePointersPercentage=normalize_double_value,
    freeThrowsMade=normalize_integer_value,
    freeThrowsPercentage=normalize_double_value,
    freeThrowsAttempted=normalize_integer_value,
    reboundsDefensive=normalize_integer_value,
    reboundsOffensive=normalize_integer_value,
    reboundsTotal=normalize_integer_value,
    assists=normalize_integer_value,
    steals=normalize_integer_value,
    blocks=normalize_integer_value,
    turnovers=normalize_integer_value,
    foulsPersonal=normalize_integer_value,
    points=normalize_integer_value,
    plusMinusPoints=normalize_integer_value,
)


