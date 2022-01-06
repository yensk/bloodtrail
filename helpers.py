def get_printable_timestamp(timestamp):
    year = timestamp[:4]
    month = timestamp[4:6]
    day = timestamp[6:8]
    hour = timestamp[8:10]
    minute = timestamp[10:12]

    return f"{hour}:{minute} {day}.{month}.{year}"