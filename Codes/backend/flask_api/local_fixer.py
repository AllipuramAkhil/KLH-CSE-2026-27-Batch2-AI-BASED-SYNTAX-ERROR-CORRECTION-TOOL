import re


def _split_comments(line, inside_block_comment):
    code = list(line)
    index = 0
    quote = None
    escaped = False

    while index < len(line):
        if inside_block_comment:
            code[index] = " "
            if line.startswith("*/", index):
                inside_block_comment = False
                code[index + 1] = " "
                index += 2
            else:
                index += 1
            continue

        char = line[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            index += 1
        elif line.startswith("//", index):
            code[index:] = [" "] * (len(line) - index)
            break
        elif line.startswith("/*", index):
            inside_block_comment = True
            code[index] = " "
            code[index + 1] = " "
            index += 2
        else:
            index += 1

    return "".join(code), inside_block_comment


def _needs_semicolon(code):
    statement = code.strip()
    if not statement or statement.endswith((";", "{", "}")):
        return False

    if re.match(r"^(?:if|else|for|while|switch|do|class|struct)\b", statement):
        return False

    if re.match(r"^(?:int|void)\s+main\s*\(", statement):
        return False

    if re.search(r"\b(?:printf|scanf)\s*\(", statement):
        return statement.endswith(")")

    if re.match(r"^return\b", statement):
        return True

    declaration = re.match(
        r"^(?:(?:const|volatile|unsigned|signed|static)\s+)*"
        r"(?:int|float|double|char|long|short|bool|size_t)\s+.+$",
        statement,
    )
    return bool(declaration)


def local_fix(code):
    fixed_lines = []
    inside_block_comment = False

    for line in code.splitlines(keepends=True):
        newline = ""
        content = line
        if content.endswith("\r\n"):
            content, newline = content[:-2], "\r\n"
        elif content.endswith(("\n", "\r")):
            content, newline = content[:-1], content[-1]

        code_part, inside_block_comment = _split_comments(
            content,
            inside_block_comment,
        )
        if _needs_semicolon(code_part):
            insertion_index = len(code_part.rstrip())
            content = (
                f"{content[:insertion_index]};"
                f"{content[insertion_index:]}"
            )

        fixed_lines.append(f"{content}{newline}")

    return "".join(fixed_lines)
