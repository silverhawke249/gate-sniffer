import dateutil.tz
from datetime import datetime, timedelta
from time import sleep

tz = dateutil.tz.gettz('America/Chicago')
now = datetime.now(tz=tz)
offset = timedelta(hours=1) - now.dst()
if offset:
    print(f'pausing script for {offset.total_seconds()} seconds...')
    sleep(offset.total_seconds())
