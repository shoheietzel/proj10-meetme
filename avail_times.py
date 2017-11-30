import arrow
import logging


def get_free_times(all_events, daily_avail):
    """
    Takes our events and our free blocks (our daily availability) and compares them to return the resulting free times
    """
    free_times_list = []

    for event in all_events:
        assert event["start"] < event["end"]  # sanity check
        new_daily_avail = []
        for free_block in daily_avail:
            # Case A: cur event start and end times before cur free_block
            # simply append to new list
            if (event["start"] <= free_block["start"]) and (event["end"] <= free_block["start"]):
                new_daily_avail.append(free_block)
            # Case B: cur event start time before cur free_block and cur event end time during free_block
                # free_block start time now equals event end time
            elif (event["start"] <= free_block["start"]) and (event["end"] > free_block["start"]) and (event["end"] < free_block["end"]):
                free_block["start"] = event["end"]
                new_daily_avail.append(free_block)
            # Case C: cur event start time and end time during free_block
                # free_block end time equals cur event start time; make new free_block, w/start time == cur event end time and end time == original free_block end time
            elif (event["start"] > free_block["start"]) and (event["start"] < free_block["end"]) and (event["end"] > free_block["start"]) and (event["end"] < free_block["end"]):
                temp_free_block_time = free_block["end"]
                free_block["end"] = event["start"]
                new_daily_avail.append(free_block)
                new_daily_avail.append({
                    "start": event["end"],
                    "end": temp_free_block_time,
                })
            # Case D: cur event start time during free_block and end time after free_block
                # free_block end time = cur event start time
            elif (event["start"] > free_block["start"]) and (event["start"] < free_block["end"]) and (event["end"] >= free_block["end"]):
                free_block["end"] = event["start"]
                new_daily_avail.append(free_block)
            # Case E: cur event start and end times after cur free_block
                # simply append to new list
            elif (event["start"] >= free_block["end"]) and (event["end"] >= free_block["end"]):
                new_daily_avail.append(free_block)
            # Case F: cur event start before free_block and cur event end after free_block
            elif (event["start"] <= free_block["start"]) and (event["end"] >= free_block["end"]):
                # nothing is done in this case; free_block is no longer free
                continue
            else:
                raise Exception("invalid event format while checking", event["summary"], " with ",
                                free_block["start"], " ", free_block["end"])
        daily_avail = new_daily_avail
    daily_avail = sorted(daily_avail, key=lambda k: k['start'])
    return daily_avail
