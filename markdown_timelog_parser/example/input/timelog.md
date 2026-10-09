# Timelog

Sample time log for the parser. Each session is one list line: `- <date> <start>-<end> [description]`.
Dates: any format in `date_formats` (20250927, 20-Feb-2025, 2025-09-27, 27.09.2025). Times: HH.MM or HH:MM.

- 20261003      13.00-14.00
- 20261001      10.00-12.05 test

## September 2025
- 20250927      21.04-22.05 development: rendering test
- 20250927      23.30-00.15
- 20250926      01.10-01.35 reading
- 2025-09-25    14:00–15:30 planning; ISO date, en dash
- 24.09.2025    09.00-10.15 review; day.month.year date

## Older entries
- 20-Feb-2025   22.20-00.36
- 12-Jun-2025   11.55-12.50 development: assembly logic; textures;
- 09-Jul-2024   21.20-00.00

## Lines the parser reports as problems
- 12-Jun-2025   11.55-12.50 duplicate of the entry above
- 12-Jun-2025   12.30-13.00 overlaps the entry above
- 03-Mar-2025   01.30-21.03 longer than max_session_hours
- 20250930      10.00-10.00 start equals end
- 01-Jan-2099   10.00-11.00 a date in the future
- 20250930      9.5-10.00 not the session shape
- 20250930      24.10-01.00 invalid time
- 2025/09/30    10.00-11.00 unknown date format

## Lines the parser ignores
- a note without a date is just text and is ignored
