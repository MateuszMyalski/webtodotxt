from pytodotxt import Task, TodoTxt
from .file import DbFile
from datetime import datetime, date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class TaskWrapper:
    def __init__(self, task: Task):
        self._task = task

    def toggle_done(self) -> None | Task:
        if self._task.is_completed:
            self.set_undone()
            return None
        else:
            return self.set_done()

    def set_undone(self):
        if not self._task.is_completed:
            return

        self._task.is_completed = False
        self._task.completion_date = None
        if self._task.attributes.get("pri", None) is not None:
            self._task.priority = self._task.attributes.get("pri")[0]

    def set_done(self) -> None | Task:
        if self._task.is_completed:
            return None

        new_task = None
        if self._is_reccuring():
            new_task = self._create_reccuring_task()

        if self._task.priority:
            self._task.remove_attribute("pri")
            self._task.add_attribute("pri", self._task.priority)
        self._task.is_completed = True
        self._task.completion_date = date.today()

        return new_task

    def get_creation_date(self):
        return self._task.creation_date

    def get_completion_date(self):
        return self._task.completion_date

    def get_contexts(self):
        return self._task.contexts

    def get_projects(self):
        return self._task.projects

    def get_attributes(self):
        if self._task.attributes is None:
            return None

        attrs = self._task.attributes

        if "due" in attrs:
            del attrs["due"]
        return attrs

    def get_priority(self):
        if self._task.priority is not None:
            return self._task.priority[0]

        return (
            None
            if self._task.attributes.get("pri", None) is None
            else self._task.attributes.get("pri")[0]
        )

    def get_bare_description(self):
        return self._task.bare_description()

    def get_line_nr(self):
        return self._task.linenr

    def get_due_date(self):
        if not self._is_due():
            return None

        try:
            return Task.parse_date(self._task.attributes.get("due")[0])
        except ValueError:
            return None

    def parse(self, line):
        self._task.parse(line)

    @property
    def is_completed(self):
        return self._task.is_completed

    def _is_reccuring(self):
        return self._task.attributes.get("rec", None) != None

    def _is_due(self):
        return self._task.attributes.get("due", None) != None

    def _create_reccuring_task(self):
        rec_dt = self._task.attributes.get("rec")
        new_task = Task(self._task._raw)

        offset = date.today()

        if self._is_due():
            due = self._task.attributes.get("due")[0]
            new_task.remove_attribute("due")
            offset = Task.parse_date(due)

        new_due = self._apply_recurring(offset, rec_dt[0])

        while new_due < date.today():
            new_due = self._apply_recurring(new_due, rec_dt[0])

        new_task.add_attribute("due", new_due)
        new_task.creation_date = date.today()

        return new_task

    def _apply_recurring(self, dt: date, rec: str) -> date:
        num, unit = int(rec[:-1]), rec[-1]
        if unit == "d":
            dt += timedelta(days=num)
        elif unit == "w":
            dt += timedelta(weeks=num)
        elif unit == "m":
            dt += relativedelta(months=num)
        elif unit == "y":
            dt += relativedelta(years=num)
        else:
            raise ValueError("Unknown recurrence unit")

        return dt

    def edit_line(self, new_value):
        self._task.parse(new_value)


class Todos:
    def __init__(self, db_file: DbFile):
        self.db_file = db_file

        self.todotxt = TodoTxt(self.db_file.get_path())
        self.todotxt.parse()

    def get_task(self, line_number: int) -> TaskWrapper | None:
        try:
            return TaskWrapper(self.todotxt.tasks[line_number])
        except IndexError:
            return None

    def get_line(self, line_number):
        try:
            return self.todotxt.lines[line_number]
        except IndexError:
            return None

    def get_tasks(self):
        return [TaskWrapper(task) for task in self.todotxt.tasks]

    def save(self):
        self.todotxt.save()

    def append_task(self, new_task: Task):
        self.todotxt.add(new_task)

    def delete_task(self, line_number):
        with open(self.db_file.get_path(), "r") as f:
            lines = f.readlines()

        if line_number < 0 or line_number >= len(lines):
            return False

        del lines[line_number]

        self.db_file.backup()

        try:
            with open(self.db_file.get_path(), "w") as f:
                f.writelines(lines)
        except:
            self.db_file.restore()
            raise
        return True
