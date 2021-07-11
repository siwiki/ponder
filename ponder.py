# Ponder
#!/usr/bin/env python
from argparse import ArgumentParser
from csv import DictWriter
import os

parser = ArgumentParser(prog='Ponder', description='Generates CSV file with student grade rankings according to the law of Bachelor Studies for the SI major at the School of EE, University of Belgrade')
parser.add_argument('year',type=int, help='Select study year',choices=[1,2,3,4])
parser.add_argument('-ects_file',type=str,help='CSV file containing ECTS points per course',default='ECTS.csv')
parser.add_argument('-names_file',type=str,help='CSV file containing the names of the students, along with their student IDs',default='names.csv')
parser.add_argument('-grades_directory',type=str,help='Directory containing CSV files with grade info per student',default='./data/')
parser.add_argument('-prior_years_directory',type=str,help='Directory containing CSV files with weighted sums from prior years',default='/old/')
parser.add_argument('-min_passed',type=int,help='Do not include students with less than the given amount of passed subjects',default=1)
parser.add_argument('-output',type=str, help='Output filename',default='results.csv')
parser.add_argument('--gpa',help='Output is sorted by GPA rather than weighted sum.',action='store_true')
parser.add_argument('--strict',help='Make no assumptions about given data',action='store_true')
parser.add_argument('--verbose',help='Verbose output',action='store_true')
args = parser.parse_args()

# ECTS values of each course
ECTS = {}
with open(args.ects_file, encoding='utf-8-sig') as f:
    for line in f:
        stripped = line.strip()
        if stripped == '':
            continue
        course, points, year = stripped.split(';')
        try:
            if int(year) != args.year: continue
        except ValueError:
            print(f'Course {course} has invalid year.')
            exit()

        try:
            ECTS[course] = int(points)
        except ValueError:
            if not args.strict:
                print(f'Course {course} has invalid ECTS number. Assuming 6.')
                ECTS[course] = 6
            else: 
                print(f'Course {course} has invalid ECTS number.')
                exit()

if (args.verbose):
    print(f'{args.ects_file}: Loaded {len(ECTS)} courses.')

# Students
students = {}
with open(args.names_file, encoding='utf-8-sig') as f:
    for line in f:
        stripped = line.strip()
        if stripped == '':
            continue
        id, name= stripped.split(';')
        students[id] = {}
        students[id]['name'] = name
        students[id]['sum'] = 0
        students[id]['priorsum'] = 0
        students[id]['gpa'] = 0
        students[id]['courses'] = {}
        students[id]['budget'] = False

if (args.verbose):
    print(f'{args.names_file}: Loaded {len(students)} students.')

# Prior years
for i in range(1, args.year):
    with open(f'.{args.prior_years_directory}year-{i}.csv', 'r', encoding='utf-8-sig') as file:
        count = 0
        for line in file:
            line = line.strip()
            if line == "": continue
            id, wsum, budget = line.split(';')
            if students.get(id, None) == None:
                if args.verbose: 
                    print(f'year-{i}.csv: Student {id} not present. Skipping...')
                continue
            try:
                wsum = float(wsum)
            except ValueError:
                print(f'year-{i}.csv: Invalid sum {wsum}')
                exit()
            students[id]['priorsum'] += wsum
            students[id]['budget'] = True if budget else False
            count += 1
        if args.verbose:
            print(f'year-{i}.csv: Processed {count} students.')
            
    

# Exams
csv_filenames = sorted([file for file in os.listdir(args.grades_directory) if file[-4:] == '.csv'])
for filename in csv_filenames:
    course, term = filename[:-4].split('-')
    if ECTS.get(course, None) == None:
        print(f'Course {course} not present. Skipping...')
        continue
    try:
        term = int(term)
    except:
        print('{filename}: Invalid term number')
        exit()
    with open(f'{args.grades_directory}/{filename}', 'r', encoding='utf-8-sig') as file:
        for line in file:
            line = line.strip()
            if line == '': continue
            id, grade = line.split(';')
            try:
                if grade == '': grade = 0
                grade = int(grade)
                if grade > 10 or grade < 0: raise ValueError
                if grade < 6: continue
            except ValueError:
                print(f'{filename}:Invalid grade {grade} for {id}.')
                exit()
            if students.get(id, None) == None:
                if args.verbose : print(f'{filename}: Student {id} not present. Skipping...')
                continue
            if students[id]['courses'].get(course, None) == None:
                students[id]['courses'][course] = ()
            elif args.verbose and grade > students[id]["courses"][course][0]:
                print(f'{filename}: Student {id} fixed {students[id]["courses"][course][0]} with {grade}')
            students[id]['courses'][course] = (grade, term, int(grade * ECTS[course] * 1.1 if term < 3 else 1))

# Table
table = []
columns = ['ID', 'Name'] + list(ECTS) + ['Sum', 'GPA']
for id in students:
    if args.min_passed > len(students[id]['courses']):
        if args.verbose:
            print(f'{id} has only {len(students[id]["courses"])} passed subjects, needs {args.min_passed}.')
        continue
    student_row = {
        'ID': id, 
        'Name': students[id]['name']
    }
    for course, grade in students[id]['courses'].items():
        student_row[course] = grade[0] if grade[1] > 2 else f'{grade[0]}*'
        students[id]['gpa'] += grade[0]
        students[id]['sum'] += grade[2]
    students[id]['gpa'] /= len(students[id]['courses'])
    students[id]['sum'] /= (sum(list(map(lambda x : ECTS[x], students[id]['courses']))))
    students[id]['sum'] += students[id]['priorsum']
    students[id]['sum'] /= args.year
    student_row['GPA'] = f'={students[id]["gpa"]:.2f}'
    student_row['Sum'] = f'={students[id]["sum"]:.2f}'
    
    table.append(student_row)

table.sort(key = lambda x : students[x['ID']]['sum'], reverse = True)

# Write table to file.
with open(args.output, 'w', encoding='utf-8-sig', newline='') as results:
    writer = DictWriter(results, fieldnames=columns, delimiter=';', extrasaction='ignore')
    writer.writeheader()
    for data in table:
        writer.writerow(data)
if args.verbose:
    print(f'SUCCESS: Written to {args.output}')

