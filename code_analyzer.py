# write your code here
output = "Line {line}: {code} {message}"

class PEPError:
    def __init__(self, code, message):
        self.code = code
        self.message = message

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

fname = input()
lines = []
with open(fname, 'r') as f:
    lines = f.readlines()

res = [[] for x in range(len(lines))]
errors = [LineLenError, IndentError, SemicolonError, SpaceCommentsError, TODOError]
for i, line in enumerate(lines):
    for err in errors:
        if err.check(line):
            res[i].append(err)

another_res = BlankLinesError.check(lines)
for i,r in enumerate(res):
    if i in another_res:
        res[i].append(BlankLinesError)

for i, r in enumerate(res):
    for err in r:
        print(output.format(line=i+1, code=err.code, message=err.message))
