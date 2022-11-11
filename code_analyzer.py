import sys, os
import re, ast

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
        res = [None for i in range(len(text_lines))]
        num_blank = 0
        for i in range(0, len(text_lines)):
            line = text_lines[i]
            if line[0] == '\n':
                num_blank += 1
            else:
                if num_blank > 2:
                    res[i] = BlankLinesError()
                num_blank = 0
        return res


class SpaceConstructionError(PEPError):
    code = "S007"
    message = "Too many spaces after construction_name \'{construction}\'."

    def __init__(self, construction):
        self.message = SpaceConstructionError.message.format(construction=construction)

    @staticmethod
    def check(line):
        class_re = '\s*class \s+'
        result = SpaceConstructionError('class') if re.match(class_re, line) else None

        def_re = '\s*def \s+'
        result = SpaceConstructionError('def') if re.match(def_re, line) else result
        return result


class ClassNameError(PEPError):
    code = "S008"
    message = "Class name \'{class_name}\' should be written in CamelCase."

    def __init__(self, class_name):
        self.message = ClassNameError.message.format(class_name=class_name)

    @staticmethod
    def check(line):
        pos = line.find('class ')
        if pos > -1:
            pos += len('class ')
            name = re.match('\s*\S*?[:(]', line[pos:]).group()[:-1]
            name = name.strip()

            regexp = "[A-Z][^_]*"
            if not re.match(regexp, name):
                return ClassNameError(name)
        return None


class AstHelper:
    class Function:
        def __init__(self, name: str, lineno: int, args: list):
            self.name = name
            self.lineno = lineno
            self.args = args

    def __init__(self, text):
        self.text = text
        self.ast_tree = ast.parse(text)
        self.nodes = ast.walk(self.ast_tree)

    def all_functions(self):
        res = []
        for node in self.nodes:
            if isinstance(node, ast.FunctionDef):
                res.append(node)
        return res

    @staticmethod
    def get_function_args(ast_func: ast.FunctionDef) -> dict:
        res = {}

        args = ast_func.args.args
        default_args = ast_func.args.defaults
        for i, arg in enumerate(args):
            # find default if exists
            default_value = None
            def_i = len(default_args) - len(args) + i
            if def_i >= 0:
                default_value = default_args[def_i]
            res[arg] = default_value

        return res

    @staticmethod
    def get_function_vars(ast_func: ast.FunctionDef) -> list:
        res = []

        assignments = [x for x in ast_func.body if isinstance(x, ast.Assign)]

        for i, ass in enumerate(assignments):
            for var in ass.targets:
                res.append(var)
        return res


    @staticmethod
    def is_mutable(ast_obj):
        return isinstance(ast_obj, ast.List) or isinstance(ast_obj, ast.Dict) or isinstance(ast_obj, ast.Set)


class SnakeCaseFuncError(PEPError):
    code = "S009"
    message = "Function name \'{name}\' should be written in snake_case."

    def __init__(self, name):
        self.code = SnakeCaseFuncError.code
        self.message = SnakeCaseFuncError.message.format(name=name)

    @staticmethod
    def check(lines):
        regexp = "[_a-z0-9]+"
        ast_helper = AstHelper(''.join(lines))

        res = [None for i in range(len(lines))]
        for func in ast_helper.all_functions():
                func_name = func.name

                # function name
                if not re.match(regexp, func_name):
                    lineno = func.lineno - 1
                    res[lineno] = SnakeCaseFuncError(func_name)
        return res


class SnakeCaseArgError(PEPError):
    code = "S010"
    message = "Argument name \'{name}\' should be written in snake_case."

    def __init__(self, name):
        self.code = SnakeCaseArgError.code
        self.message = SnakeCaseArgError.message.format(name=name)

    @staticmethod
    def check(lines):
        regexp = "[_a-z0-9]+"
        ast_helper = AstHelper(''.join(lines))

        res = [None for i in range(len(lines))]
        for func in ast_helper.all_functions():
                args = ast_helper.get_function_args(func)

                # args
                for arg in args:
                    if not re.match(regexp, arg.arg):
                        lineno = arg.lineno - 1
                        res[lineno] = SnakeCaseArgError(arg.arg)

        return res


class SnakeCaseVarError(PEPError):
    code = "S011"
    message = "Variable \'{name}\' should be written in snake_case."

    def __init__(self, name):
        self.code = SnakeCaseVarError.code
        self.message = SnakeCaseVarError.message.format(name=name)

    @staticmethod
    def check(lines):
        regexp = "[_a-z0-9]+"
        ast_helper = AstHelper(''.join(lines))

        res = [None for i in range(len(lines))]
        for func in ast_helper.all_functions():
                vars = ast_helper.get_function_vars(func)

                # vars
                for var in vars:
                    if isinstance(var, ast.Name) and not re.match(regexp, var.id):
                        lineno = var.lineno - 1
                        res[lineno] = SnakeCaseVarError(var.id)
        return res


class MutableArgError(PEPError):
    code = "S012"
    message = "The default argument value is mutable."
    # mutable data types in Python: list, dictionary, set

    @staticmethod
    def check(lines):
        ast_helper = AstHelper(''.join(lines))

        res = [None for i in range(len(lines))]
        for func in ast_helper.all_functions():
            for arg, default in ast_helper.get_function_args(func).items():
                if ast_helper.is_mutable(default):
                    res[func.lineno - 1] = MutableArgError()
        return res


class PEPChecker:
    single_line_errors = [LineLenError,
                          IndentError,
                          SemicolonError,
                          SpaceCommentsError,
                          TODOError,
                          ClassNameError,
                          SpaceConstructionError]
    multi_line_errors = [BlankLinesError, SnakeCaseArgError, SnakeCaseFuncError, SnakeCaseVarError, MutableArgError]
    errors = single_line_errors + multi_line_errors

    def __init__(self, fname):
        self.filename = fname
        self.lines = []
        self.lines_errors = []
        with open(fname, 'r') as f:
            self.lines = f.readlines()
        self._check()

    def __getitem__(self, line_num) -> list:
        """Return all errors in given line number """
        return self.lines_errors[line_num]

    def __iter__(self):
        self.current_index = 0
        return self

    def __next__(self):
        if self.current_index < len(self.lines_errors):
            line_errors = self.__getitem__(self.current_index)
            self.current_index += 1
            return line_errors
        raise StopIteration

    def _check(self):
        self.lines_errors = [[] for x in range(len(self.lines))]
        # check single lines errors
        for i, line in enumerate(self.lines):
            for error in PEPChecker.single_line_errors:
                check = error.check(line)
                if check:
                    self.lines_errors[i].append(check)

        # looking for multiline errors
        for error in PEPChecker.multi_line_errors:
            list_with_err = error.check(self.lines)
            for i, element in enumerate(list_with_err):
                if element:
                    self.lines_errors[i].append(element)

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
