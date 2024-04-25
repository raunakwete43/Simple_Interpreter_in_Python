from string_with_arrows import string_with_arrows

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
TT_EOF = "EOF"


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end

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

    def as_string(self) -> str:
        result = f"{self.error_name}: {self.details}"
        result += (
            f"\nFile {self.position_start.filename}, line {self.position_start.ln + 1}"
        )
        result += "\n\n" + string_with_arrows(
            self.position_start.filetext, self.position_start, self.position_end
        )

        return result


class ILLEGAL_CHAR_ERROR(ERROR):
    def __init__(self, details, position_start, position_end) -> None:
        super().__init__(
            error_name="ILLEGAL CHARACTER",
            details=details,
            position_start=position_start,
            position_end=position_end,
        )


class INVALID_SYNTAX_ERROR(ERROR):
    def __init__(self, details, position_start, position_end) -> None:
        super().__init__(
            error_name="INVALID_SYNTAX",
            details=details,
            position_start=position_start,
            position_end=position_end,
        )


"""POSITION"""


class Position:
    def __init__(self, index, line, column, filename, filetxt) -> None:
        self.index = index
        self.ln = line
        self.column = column
        self.filename = filename
        self.filetext = filetxt

    def advance(self, current_char=None):
        self.index += 1
        self.column += 1

        if current_char == "\n":
            self.ln += 1
            self.column = 0

        return self

    def copy(self):
        return Position(self.index, self.ln, self.column, self.filename, self.filetext)


"""NODES"""


class Node:
    def __init__(self, tok) -> None:
        self.tok = tok

    def __repr__(self):
        return f"{self.tok}"


class NumberNode(Node):
    def __init__(self, tok):
        super().__init__(tok)


class BinOpNode(Node):
    def __init__(self, left_node, op_tok, right_node):
        super().__init__(op_tok)
        self.left_node = left_node
        self.right_node = right_node

    def __repr__(self):
        return f"({self.left_node}, {self.tok}, {self.right_node})"


class UnaryNode(Node):
    def __init__(self, op_tok, node):
        super().__init__(op_tok)
        self.node = node

    def __repr__(self):
        return f"({self.tok}, {self.node})"


"""PARSE RESULT"""


class ParseResult:
    def __init__(self) -> None:
        self.error = None
        self.node = None

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error:
                self.error = res.error
            return res.node

        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self


"""PARSER"""


class Parser:
    def __init__(self, tokens) -> None:
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(
                INVALID_SYNTAX_ERROR(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected '+', '-', '*', '/', or ')'",
                )
            )
        return res

    def factor(self):
        res = ParseResult()

        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryNode(tok, factor))

        elif tok.type in (TT_INT, TT_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(tok))
        elif tok.type == TT_LPAREN:
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                return res.failure(
                    INVALID_SYNTAX_ERROR(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ')'",
                    )
                )

        return res.failure(
            INVALID_SYNTAX_ERROR(
                "Expected int or float",
                position_start=tok.pos_start,
                position_end=tok.pos_end,
            )
        )

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def bin_op(self, func, ops):
        res = ParseResult()
        left = res.register(func())
        if res.error:
            return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register(self.advance())
            right = res.register(func())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


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
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == "%":
                tokens.append(Token(TT_MOD, pos_start=self.pos))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            else:
                char = self.current_char
                position_start = self.pos.copy()
                self.advance()
                return [], ILLEGAL_CHAR_ERROR(
                    f"'{char}'", position_start=position_start, position_end=self.pos
                )

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def peek(self):
        if self.pos.index < len(self.text) - 1:
            return self.text[self.pos.index + 1]
        else:
            return None

    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()

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
            return Token(TT_INT, int(num_str), pos_start=pos_start, pos_end=self.pos)
        else:
            return Token(
                TT_FLOAT, float(num_str), pos_start=pos_start, pos_end=self.pos
            )


"""INTERPRETER"""


class Interpreter:
    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node)

    def no_visit_method(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_NumberNode(self, node):
        print(f"Found Number Node {node.tok}")

    def visit_BinOpNode(self, node):
        print(f"Found Binary Node {node.tok}")
        self.visit(node.left_node)
        self.visit(node.right_node)

    def visit_UnaryNode(self, node):
        print(f"Found Unary Node {node.tok}")


"""RUN"""


def run(filename, text):
    # Generate TOKENS
    lexer = Lexer(text, filename)
    tokens, error = lexer.makeTokens()
    if error:
        return None, error

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()

    if ast.error:
        return None, ast.error
    interpreter = Interpreter()
    interpreter.visit(ast.node)

    return ast.node, None
