# compiler.py
import re

class JabaiScriptCompiler:
    """Class na mamamahala sa pag-run ng JabaiScript code."""

    def run(self, code: str) -> str:
        if not code.strip():
            return "Error: Empty code block."

        output_lines = []
        variables = {}

        lines = code.strip().split("\n")

        # --- Switch state ---
        in_switch = False
        switch_val = None
        execute_block = False
        matched_any_case = False

        # --- If-else state ---
        # Each entry: {"type": "if"|"elif"|"else", "condition": str|None, "active": bool}
        if_chain = []          # stack of if-chain blocks
        in_if_block = False
        if_block_active = False  # whether the current { } block should execute
        if_chain_matched = False  # whether any branch in the current chain already matched
        brace_depth = 0

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1

            if not line or line.startswith("//"):
                continue

            # -------------------------------------------------------
            # IF-ELSE HANDLING
            # -------------------------------------------------------

            # kung (condition) {
            kung_if = re.match(r'^kung\s*\((.+)\)\s*\{$', line)
            # kaha kung (condition) {
            kaha_kung = re.match(r'^kaha\s+kung\s*\((.+)\)\s*\{$', line)
            # kung dili {
            kung_dili = re.match(r'^kung\s+dili\s*\{$', line)

            if kung_if:
                condition_str = kung_if.group(1).strip()
                result = self._eval_condition(condition_str, variables)
                if_chain = [{"type": "if", "matched": result}]
                if_chain_matched = result
                if_block_active = result
                in_if_block = True
                brace_depth = 1
                continue

            elif kaha_kung:
                if in_if_block:
                    # Close previous block (already handled by })
                    pass
                condition_str = kaha_kung.group(1).strip()
                result = (not if_chain_matched) and self._eval_condition(condition_str, variables)
                if result:
                    if_chain_matched = True
                if_block_active = result
                in_if_block = True
                brace_depth = 1
                continue

            elif kung_dili:
                if_block_active = not if_chain_matched
                if_chain_matched = True  # else always "consumes" the chain
                in_if_block = True
                brace_depth = 1
                continue

            elif in_if_block:
                if line == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        in_if_block = False
                        if_block_active = False
                    continue
                elif "{" in line:
                    brace_depth += 1

                # Execute lines only when the active branch matched
                if if_block_active:
                    # Handle print inside if-block
                    if line.startswith("printa(") and line.endswith(");"):
                        content = line[7:-2].strip().strip('"\'')
                        if content in variables:
                            output_lines.append(variables[content])
                        else:
                            output_lines.append(content)
                    # Handle variable assignment inside if-block
                    elif line.startswith("nambai") and "=" in line and line.endswith(";"):
                        parts = line.replace("nambai", "").replace(";", "").split("=")
                        var_name = parts[0].strip()
                        var_val = parts[1].strip().strip('"\'')
                        variables[var_name] = var_val
                continue

            # -------------------------------------------------------
            # VARIABLE DECLARATION: nambai age = 18;
            # -------------------------------------------------------
            if line.startswith("nambai") and "=" in line and line.endswith(";"):
                parts = line.replace("nambai", "").replace(";", "").split("=")
                var_name = parts[0].strip()
                var_val = parts[1].strip().strip('"\'')
                variables[var_name] = var_val
                continue

            # -------------------------------------------------------
            # SWITCH STATEMENT
            # -------------------------------------------------------
            if line.startswith("pili") and "(" in line:
                in_switch = True
                matched_any_case = False
                start_idx = line.find("(") + 1
                end_idx = line.find(")")
                expr = line[start_idx:end_idx].strip()
                switch_val = variables.get(expr, expr)
                execute_block = False
                continue

            if line.startswith("kaso") and ":" in line:
                if in_switch:
                    case_val = line.replace("kaso", "").split(":")[0].strip().strip('"\'')
                    if case_val == str(switch_val):
                        execute_block = True
                        matched_any_case = True
                    else:
                        execute_block = False
                continue

            if line.startswith("default:") or line.startswith("lain:"):
                if in_switch:
                    execute_block = not matched_any_case
                continue

            if line == "undang;":
                if in_switch:
                    execute_block = False
                continue

            if line == "}":
                execute_block = False
                in_switch = False
                continue

            # -------------------------------------------------------
            # PRINT STATEMENT: printa(value);
            # -------------------------------------------------------
            if line.startswith("printa(") and line.endswith(");"):
                if not in_switch or execute_block:
                    content = line[7:-2].strip().strip('"\'')
                    if content in variables:
                        output_lines.append(variables[content])
                    else:
                        output_lines.append(content)

        if output_lines:
            return "\n".join(output_lines)
        return "Code executed successfully (No output)."

    # -------------------------------------------------------
    # HELPER: Evaluate a simple condition string
    # Supports: ==, !=, >, <, >=, <=
    # Variables are resolved from the variables dict.
    # -------------------------------------------------------
    def _eval_condition(self, condition: str, variables: dict) -> bool:
        ops = [">=", "<=", "!=", "==", ">", "<"]
        for op in ops:
            if op in condition:
                left, right = condition.split(op, 1)
                left = left.strip().strip('"\'')
                right = right.strip().strip('"\'')

                # Resolve variables
                lval = variables.get(left, left)
                rval = variables.get(right, right)

                # Try numeric comparison
                try:
                    lval = float(lval)
                    rval = float(rval)
                except ValueError:
                    pass  # keep as string

                if op == "==":
                    return lval == rval
                elif op == "!=":
                    return lval != rval
                elif op == ">":
                    return lval > rval
                elif op == "<":
                    return lval < rval
                elif op == ">=":
                    return lval >= rval
                elif op == "<=":
                    return lval <= rval
        return False