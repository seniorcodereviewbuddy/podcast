def seconds_to_string(seconds: float) -> str:
    days, remainder = divmod(seconds, 3600 * 24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    duration_string = ""
    if days > 0:
        duration_string += "%dd" % days
    if hours > 0:
        duration_string += "%dh" % hours
    if minutes > 0:
        duration_string += "%dm" % minutes
    if seconds > 0:
        duration_string += "%ds" % seconds

    if not duration_string:
        duration_string = "0s"

    return duration_string
