import sys, os

output = "{file}: Line {line}: {code} {message}"


class PEPError:
    code = "0"
    message = "Basic error"

    def check(self):
        pass


class LineLenError(PEPError):
    code = "S001"
    message = "Too long"

    @staticmethod
    def check(line):
        return len(line) > 79


class IndentError(PEPError):
    code = "S002"
    message = "Indentation is not a multiple of four"

    @staticmethod
    def check(line):
        num_spaces = 1
        while num_spaces < len(line):
            if line.startswith(' ' * num_spaces):
                num_spaces += 1
            else:
                num_spaces -= 1
                return num_spaces % 4


class SemicolonError(PEPError):
    code = "S003"
    message = "Unnecessary semicolon after a statement"

    @staticmethod
    def check(line):
        comment_pos = line.find('#')
        comment_pos = comment_pos if comment_pos != -1 else len(line)
        l = line[:comment_pos]
        l = l.replace(" ", "")
        l = l.replace('\n', '')
        last_symb = l[-1] if len(l) > 0 else ''
        return last_symb == ';'


class SpaceCommentsError(PEPError):
    code = "S004"
    message = "Less than two spaces before inline comments"

    @staticmethod
    def check(line):
        line_strip = line.strip()
        comment_pos = line_strip.find('#')
        if comment_pos < 1:  # -1, 0
            return False
        right_comment_pos = line.find('  #', 0, comment_pos + 1)
        return right_comment_pos == -1


class TODOError(PEPError):
    code = "S005"
    message = "TODO found"

    @staticmethod
    def check(line):
        line = line.lower()
        todo_pos = line.find('todo')
        return -1 < line.find('#') < todo_pos


class BlankLinesError(PEPError):
    code = "S006"
    message = "More than two blank lines preceding a code line."

    @staticmethod
    def check(text_lines):
        res = []
        num_blank = 0
        for i in range(0, len(text_lines)):
            line = text_lines[i].replace('\n', '')
            if len(line) == 0:
                num_blank += 1
            else:
                if num_blank > 2:
                    res.append(i)
                    num_blank = 0
        return res


class PEPChecker:
    single_line_errors = [LineLenError, IndentError, SemicolonError, SpaceCommentsError, TODOError]
    multi_line_errors = [BlankLinesError]
    errors = single_line_errors + multi_line_errors

    def __init__(self, fname):
        self.filename = fname
        self.lines = []
        self.error_dict = {}
        with open(fname, 'r') as f:
            self.lines = f.readlines()
        self._check()

    def __getitem__(self, line_num) -> list:
        """Return all errors in given line number """
        result = []
        for error, pages in self.error_dict.items():
            if line_num in pages:
                result.append(error)
        return result

    def __iter__(self):
        self.current_index = 0
        return self

    def __next__(self):
        if self.current_index < len(self.lines):
            line_errors = self.__getitem__(self.current_index)
            self.current_index += 1
            return line_errors
        raise StopIteration

    def _check(self):
        for i, line in enumerate(self.lines):
            for error in self.errors:
                self.error_dict[error] = self.check_error(error)

    def check_error(self, error: PEPError) -> list:
        if isinstance(error(), tuple(PEPChecker.multi_line_errors)):
            return error.check(self.lines)

        error_line_nums = []
        for i, line in enumerate(self.lines):
            if error.check(line):
                error_line_nums.append(i)
        return error_line_nums

    @staticmethod
    def check_line(line, error):
        if not isinstance(error(), tuple(PEPChecker.single_line_errors)):
            raise TypeError(message=f"Error {type(error)} doesn't exist or more than one line requires.")
        return error.check(line)


arg = sys.argv[1]
files = []
if os.path.isfile(arg):
    files.append(arg)
else:
    files = [os.path.join(arg, file) for file in os.listdir(arg) if os.path.basename(file).endswith('.py') and "tests.py" not in file]

for file in files:
    checker = PEPChecker(file)
    for line_num, errors in enumerate(checker):
        for err in errors:
            print(output.format(file=file, line=line_num+1, code=err.code, message=err.message))