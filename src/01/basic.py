"""TOKENS"""

DIGITS = "0123456789"
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_MOD = "MOD"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"


class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self) -> str:
        if self.value:
            return f"{self.type}:{self.value}"
        return f"{self.type}"


"""ERROR"""


class ERROR:
    def __init__(self, position_start, position_end, error_name, details) -> None:
        self.error_name = error_name
        self.details = details
        self.position_start = position_start
        self.position_end = position_end

    def as_string(self):
        result = f"{self.error_name}: {self.details}"
        result += f"\nFile {self.position_start.filename}, line {self.position_start.line + 1}"

        return result


class ILLEGAL_CHAR_ERROR(ERROR):
    def __init__(self, details, position_start, position_end) -> None:
        super().__init__(
            error_name="ILLEGAL CHARACTER",
            details=details,
            position_start=position_start,
            position_end=position_end,
        )


"""POSITION"""


class Position:
    def __init__(self, index, line, column, filename, filetxt) -> None:
        self.index = index
        self.line = line
        self.column = column
        self.filename = filename
        self.filetext = filetxt

    def advance(self, current_char):
        self.index += 1
        self.column += 1

        if current_char == "\n":
            self.line += 1
            self.column = 0

        return self

    def copy(self):
        return Position(
            self.index, self.line, self.column, self.filename, self.filetext
        )


"""LEXER"""


class Lexer:
    def __init__(self, text, filename):
        self.text = text
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        self.advance()
        self.filename = filename

    def advance(self):
        self.pos.advance(self.current_char)
        if self.pos.index < len(self.text):
            self.current_char = self.text[self.pos.index]
        else:
            self.current_char = None

    def makeTokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in " \t":
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == "/":
                if self.peek() == "/":
                    tokens.append(Token(TT_MOD))
                    self.advance()
                else:
                    tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == "//":
                tokens.append(Token(TT_MOD))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN))
                self.advance()
            else:
                char = self.current_char
                position_start = self.pos.copy()
                self.advance()
                return [], ILLEGAL_CHAR_ERROR(
                    f"'{char}'", position_start=position_start, position_end=self.pos
                )

        return tokens, None

    def peek(self):
        if self.pos.index < len(self.text) - 1:
            return self.text[self.pos.index + 1]
        else:
            return None

    def make_number(self):
        num_str = ""
        dot_count = 0

        while self.current_char != None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))


def run(filename, text):
    lexer = Lexer(text, filename)
    tokens, error = lexer.makeTokens()

    return tokens, error
