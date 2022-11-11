import sys, os
import re

output = "{file}: Line {line}: {code} {message}"


class PEPError:
    code = "0"
    message = "Basic error"

    def check(self):
        pass

    @staticmethod
    def find_construction(line, construction):
        pos_start = line.find(construction)
        pos_end = pos_start + len(construction)
        return None, None if pos_start == -1 else pos_start, pos_end


class LineLenError(PEPError):
    code = "S001"
    message = "Too long"

    @staticmethod
    def check(line):
        return LineLenError() if len(line) > 79 else None


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
                return IndentError() if num_spaces % 4 else None


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
        return SemicolonError() if last_symb == ';' else None


class SpaceCommentsError(PEPError):
    code = "S004"
    message = "Less than two spaces before inline comments"

    @staticmethod
    def check(line):
        line_strip = line.strip()
        comment_pos = line_strip.find('#')
        if comment_pos < 1:  # -1, 0
            return None
        right_comment_pos = line.find('  #', 0, comment_pos + 1)
        return SpaceCommentsError if right_comment_pos == -1 else None


class TODOError(PEPError):
    code = "S005"
    message = "TODO found"

    @staticmethod
    def check(line):
        line = line.lower()
        todo_pos = line.find('todo')
        return TODOError() if -1 < line.find('#') < todo_pos else None


class BlankLinesError(PEPError):
    code = "S006"
    message = "More than two blank lines preceding a code line."

    @staticmethod
    def check(text_lines):
        res = []
        num_blank = 0
        for i in range(0, len(text_lines)):
            line = text_lines[i]
            if line[0] == '\n':
                num_blank += 1
            else:
                if num_blank > 2:
                    res.append(i)
                num_blank = 0
        return res


class SpaceConstructionError(PEPError):
    code = "S006"
    message = "Too many spaces after construction_name \'{construction}\'."

    def __init__(self, construction):
        self.message = SpaceConstructionError.message.format(construction=construction)

    @staticmethod
    def check(line):
        class_re = 'class\s\s+'
        result = SpaceConstructionError('class') if re.match(class_re, line) else None

        def_re = 'def\s\s+'
        return SpaceConstructionError('def') if re.match(def_re, line) else result


class ClassNameError(PEPError):
    code = "S007"
    message = "Class name \'{class_name}\' should be written in CamelCase."

    def __init__(self, class_name):
        self.message = ClassNameError.format(class_name=class_name)

    @staticmethod
    def check(line):
        pos = line.find('class ')
        if pos > -1:
            pos += len('class ')
            pos_end = line.find('(')
            name = line[pos:pos_end]
            regexp = "[A-Z][^_]*"
            if not re.match(regexp, name):
                return ClassNameError(name)
        return None


class FunctionNameError(PEPError):
    code = "S008"
    message = "Function name \'{function_name}\' should be written in snake_case."

    def __init__(self, func_name):
        self.message = FunctionNameError.message.format(function_name=func_name)

    @staticmethod
    def check(line):
        pos = line.find('def ')
        if pos > -1:
            pos += len('def ')
            pos_end = line.find('(')
            name = line[pos:pos_end]
            regexp = "[_a-z0-9]+"
            if not re.match(regexp, name):
                return FunctionNameError(name)
        return None


class PEPChecker:
    single_line_errors = [LineLenError,
                          IndentError,
                          SemicolonError,
                          SpaceCommentsError,
                          TODOError,
                          ClassNameError,
                          SpaceConstructionError,
                          FunctionNameError]
    multi_line_errors = [BlankLinesError]
    errors = single_line_errors + multi_line_errors

    def __init__(self, fname):
        self.filename = fname
        self.lines = []
        self.error_dict = {}
        self.lines_errors = []
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
        self.lines_errors = [[] for x in range(len(self.lines))]
        # check single lines errors
        for i, line in enumerate(self.lines):
            for error in PEPChecker.single_line_errors:
                self.lines_errors[i] = error.check(line)

        # looking for multiline errors
        for error in PEPChecker.multi_line_errors:
            lines_with_err = error.check(self.lines)
            for line in lines_with_err:
                self.lines_errors[line].append(error())


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
    files = [os.path.join(arg, file) for file in os.listdir(arg) if
             os.path.basename(file).endswith('.py') and "tests.py" not in file]

for file in files:
    checker = PEPChecker(file)
    for line_num, errors in enumerate(checker):
        for err in errors:
            print(output.format(file=file, line=line_num + 1, code=err.code, message=err.message))
