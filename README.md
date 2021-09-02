# ponder

Generates a CSV file with student grade rankings according to the law of Bachelor Studies for the SI major at the School of Electrical Engineering, University of Belgrade.

Original codebase by [@KockaAdmiralac](https://github.com/KockaAdmiralac)

# Input CSV formats
## Name file
Contents: `<id>;<name>`
## ECTS file
Contents: `<course_name>;<ECTS>`
## Grade files
Filename: `<course_name>-<term>.csv`

Contents: `<id>;<grade>`
## Prior years
Filename: `year-<year>.csv`

Contents: `<id>;<weighted_sum>;<budget>`
