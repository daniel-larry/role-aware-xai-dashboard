"""Generate LMS import files from OULAD so every course, student and enrolment exists in the LMS.

Each OULAD module presentation becomes one course (shortname e.g. FFF-2014J); each OULAD student
becomes one LMS user (username s<id_student>, anonymised display name); each studentInfo row
(32,593 student-module-presentation observations) becomes one student enrolment. Staff demo
accounts are added: one instructor per module plus an all-course instructor, an advisor and an
administrator.

Outputs
  out/moodle/courses.csv      admin/tool/uploadcourse/cli/uploadcourse.php
  out/moodle/users.csv        admin/tool/uploaduser/cli/uploaduser.php (with enrolments)
  out/moodle/staff.csv        staff accounts and teacher enrolments
  out/canvas/*.csv            Canvas SIS import (terms, courses, users, enrollments)
"""
import csv
import os
import sys

import pandas as pd

MODULE_NAMES = {  # OULAD publishes only codes and domains (Kuzilek et al., 2017)
    'AAA': 'Social Sciences module AAA', 'BBB': 'Social Sciences module BBB', 'CCC': 'STEM module CCC',
    'DDD': 'STEM module DDD', 'EEE': 'STEM module EEE', 'FFF': 'STEM module FFF', 'GGG': 'Social Sciences module GGG',
}


def shortname(m, p):
    return f'{m}-{p}'


def main(raw_dir, out_dir, staff_password):
    info = pd.read_csv(os.path.join(raw_dir, 'studentInfo.csv'), na_values=['?'])
    courses = pd.read_csv(os.path.join(raw_dir, 'courses.csv'))
    m_out, c_out = os.path.join(out_dir, 'moodle'), os.path.join(out_dir, 'canvas')
    os.makedirs(m_out, exist_ok=True); os.makedirs(c_out, exist_ok=True)

    # ---------------- Moodle ----------------
    with open(os.path.join(m_out, 'courses.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['shortname', 'fullname', 'category_path', 'summary', 'format'])
        for _, r in courses.sort_values(['code_module', 'code_presentation']).iterrows():
            w.writerow([shortname(r.code_module, r.code_presentation),
                        f'{MODULE_NAMES[r.code_module]} ({r.code_presentation})',
                        f'OULAD / {r.code_module}',
                        f'OULAD module {r.code_module}, presentation {r.code_presentation}, '
                        f'{r.module_presentation_length} days.', 'topics'])

    enrol = info.groupby('id_student').apply(
        lambda g: [shortname(m, p) for m, p in zip(g.code_module, g.code_presentation)], include_groups=False)
    max_c = int(enrol.map(len).max())
    with open(os.path.join(m_out, 'users.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        header = ['username', 'firstname', 'lastname', 'email', 'auth', 'idnumber']
        for i in range(1, max_c + 1):
            header += [f'course{i}', f'role{i}']
        w.writerow(header)
        for sid, cs in enrol.items():
            row = [f's{sid}', 'Student', str(sid), f's{sid}@students.oulad.invalid', 'nologin', str(sid)]
            for c in cs:
                row += [c, 'student']
            row += [''] * (len(header) - len(row))
            w.writerow(row)

    course_list = [shortname(r.code_module, r.code_presentation) for _, r in courses.iterrows()]
    with open(os.path.join(m_out, 'staff.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        header = ['username', 'firstname', 'lastname', 'email', 'auth', 'password']
        n = len(course_list)
        for i in range(1, n + 1):
            header += [f'course{i}', f'role{i}']
        w.writerow(header)

        def row(user, first, last, cs, role):
            r = [user, first, last, f'{user}@staff.oulad.invalid', 'manual', staff_password]
            for c in cs:
                r += [c, role]
            return r + [''] * (len(header) - len(r))

        w.writerow(row('instructor', 'Demo', 'Instructor', course_list, 'editingteacher'))
        for m in sorted(MODULE_NAMES):
            w.writerow(row(f'instructor_{m.lower()}', 'Instructor', m, [c for c in course_list if c.startswith(m)], 'editingteacher'))
        w.writerow(row('advisor', 'Demo', 'Advisor', [], ''))
        w.writerow(row('manager', 'Demo', 'Administrator', [], ''))

    # ---------------- Canvas SIS import ----------------
    pres = sorted(courses.code_presentation.unique())
    pd.DataFrame({'term_id': pres, 'name': pres, 'status': 'active'}).to_csv(os.path.join(c_out, 'terms.csv'), index=False)
    pd.DataFrame([{'course_id': shortname(r.code_module, r.code_presentation), 'short_name': shortname(r.code_module, r.code_presentation),
                   'long_name': f'{MODULE_NAMES[r.code_module]} ({r.code_presentation})', 'term_id': r.code_presentation,
                   'status': 'active'} for _, r in courses.iterrows()]).to_csv(os.path.join(c_out, 'courses.csv'), index=False)
    users = pd.DataFrame({'user_id': [f's{s}' for s in enrol.index], 'login_id': [f's{s}' for s in enrol.index],
                          'first_name': 'Student', 'last_name': [str(s) for s in enrol.index],
                          'email': [f's{s}@students.oulad.invalid' for s in enrol.index], 'status': 'active'})
    staff = pd.DataFrame([{'user_id': u, 'login_id': u, 'first_name': fn, 'last_name': ln,
                           'email': f'{u}@staff.oulad.invalid', 'status': 'active', 'password': staff_password}
                          for u, fn, ln in [('instructor', 'Demo', 'Instructor'), ('advisor', 'Demo', 'Advisor')]])
    pd.concat([users, staff]).to_csv(os.path.join(c_out, 'users.csv'), index=False)
    enr = pd.DataFrame({'course_id': [shortname(m, p) for m, p in zip(info.code_module, info.code_presentation)],
                        'user_id': [f's{s}' for s in info.id_student], 'role': 'student', 'status': 'active'})
    teach = pd.DataFrame({'course_id': course_list, 'user_id': 'instructor', 'role': 'teacher', 'status': 'active'})
    pd.concat([enr, teach]).to_csv(os.path.join(c_out, 'enrollments.csv'), index=False)

    print(f'courses={len(course_list)} students={len(enrol)} enrolments={len(info)} max courses per student={max_c}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], os.environ.get('STAFF_PASSWORD', 'ChangeMe-2026!'))
