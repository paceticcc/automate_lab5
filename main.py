import csv
import sys

def export_moore_automaton_to_csv(moore_automaton, filename, start_state):
    all_input_symbols = set()

    for key in moore_automaton:
        state = moore_automaton[key]
        for transition in state['transitions']:
            all_input_symbols.add(transition['inputSym'])

    all_input_symbols = sorted(all_input_symbols)

    state_keys = [start_state] + [key for key in moore_automaton if key != start_state]
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')

        output_row = [''] + [moore_automaton[key]['output'] for key in state_keys]
        writer.writerow(output_row)

        headers = [''] + state_keys
        writer.writerow(headers)

        for symbol in all_input_symbols:
            row = [symbol]
            for key in state_keys:
                state = moore_automaton[key]
                next_states = [
                    transition['nextPos']
                    for transition in state['transitions']
                    if transition['inputSym'] == symbol
                ]

                if not next_states:
                    row.append('')
                else:
                    output_str = ','.join(next_states)
                    row.append(output_str)

            writer.writerow(row)

    print(f"Moore automaton exported to {filename}")


def parse_regex(pattern):
    def parse_or(expr):
        parts = []
        current = []
        depth = 0
        for char in expr:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "|" and depth == 0:
                parts.append("".join(current))
                current = []
                continue
            current.append(char)

        parts.append("".join(current))
        if len(parts) > 1:
            return {"type": "Or", "left": parse_concat(parts[0]), "right": parse_or("|".join(parts[1:]))}
        return parse_concat(expr)

    def parse_concat(expr):
        parts = []
        i = 0
        while i < len(expr):
            if expr[i] == "(":
                end = find_closing_parenthesis(expr, i)
                sub_expr = expr[i + 1:end]
                if sub_expr == "":
                    parts.append({"type": "Literal", "value": "ε"})
                else:
                    parts.append(parse_or(sub_expr))
                i = end + 1
            elif expr[i] in "*+":
                if not parts:
                    raise ValueError(f"Unexpected operator '{expr[i]}' at position {i}")
                op = "Repeat" if expr[i] == "*" else "Plus"
                parts[-1] = {"type": op, "expr": parts[-1]}
                i += 1
            else:
                parts.append({"type": "Literal", "value": expr[i]})
                i += 1

        if len(parts) == 1:
            return parts[0]

        return build_concat_tree(parts)

    def build_concat_tree(parts):
        if len(parts) == 1:
            return parts[0]

        left = parts[0]
        right = build_concat_tree(parts[1:])
        return {"type": "Concat", "left": left, "right": right}

    def find_closing_parenthesis(expr, start):
        depth = 1
        for i in range(start + 1, len(expr)):
            if expr[i] == "(":
                depth += 1
            elif expr[i] == ")":
                depth -= 1
                if depth == 0:
                    return i
        raise ValueError("Unmatched parenthesis in expression")

    return parse_or(pattern)

state_counter = 1

def add_eps_trans(nfa, start_state, final_state):
    nfa[start_state]['transitions'].append({
                                    'inputSym': 'ε',
                                    'nextPos': final_state
                                })
    return nfa

def new_state():
    global state_counter
    state = {
            "state": f"q{state_counter}",
            "output": '',
            "transitions": []
        }
    state_counter += 1
    return state

def tree_to_nfa(regex, startState, finalState, nfa):
    if regex['type'] == 'Literal':
        global state_counter
        start_state = new_state()
        final_state = new_state()
        start_state["transitions"].append({
                                    'inputSym': regex['value'],
                                    'nextPos': final_state['state']
                                })

        nfa[start_state['state']] = start_state
        nfa[final_state['state']] = final_state

        return nfa, start_state['state'], final_state['state']

    elif regex['type'] == 'Concat':

        left_nfa, lstart, lfinal = tree_to_nfa(regex['left'], startState, finalState, nfa)
        right_nfa, rstart, rfinal = tree_to_nfa(regex['right'], startState, finalState, nfa)

        nfa = add_eps_trans(nfa, lfinal, rstart)

        return nfa, lstart, rfinal

    elif regex['type'] == 'Or':

        left_nfa, lstart, lfinal = tree_to_nfa(regex['left'], startState, finalState, nfa)
        right_nfa, rstart, rfinal = tree_to_nfa(regex['right'], startState, finalState, nfa)

        start_state = new_state()
        final_state = new_state()

        nfa[start_state['state']] = start_state
        nfa[final_state['state']] = final_state

        nfa = add_eps_trans(nfa, start_state['state'], lstart)
        nfa = add_eps_trans(nfa, lfinal, final_state['state'])

        nfa = add_eps_trans(nfa, start_state['state'], rstart)
        nfa = add_eps_trans(nfa, rfinal, final_state['state'])

        return nfa, start_state['state'], final_state['state']

    elif regex['type'] == 'Repeat':

        sub_nfa, sub_start, sub_final = tree_to_nfa(regex['expr'], startState, finalState, nfa)

        start_state = new_state()
        final_state = new_state()

        nfa[start_state['state']] = start_state
        nfa[final_state['state']] = final_state

        nfa = add_eps_trans(nfa, start_state['state'], sub_start)
        nfa = add_eps_trans(nfa, sub_final, sub_start)
        nfa = add_eps_trans(nfa, sub_final, final_state['state'])
        nfa = add_eps_trans(nfa, start_state['state'], final_state['state'])

        return nfa, start_state['state'], final_state['state']

    elif regex['type'] == 'Plus':

        sub_nfa, sub_start, sub_final = tree_to_nfa(regex['expr'], startState, finalState, nfa)

        start_state = new_state()
        final_state = new_state()

        nfa[start_state['state']] = start_state
        nfa[final_state['state']] = final_state

        nfa = add_eps_trans(nfa, start_state['state'], sub_start)
        nfa = add_eps_trans(nfa, sub_final, sub_start)
        nfa = add_eps_trans(nfa, sub_final, final_state['state'])

        return nfa, start_state['state'], final_state['state']

def main():

    if len(sys.argv) != 3:
        print('Usage: /regexToNFA <output.csv> "<regex>"')
        sys.exit(1)

    output_file = sys.argv[1]
    regex = sys.argv[2]

    parsed_tree = parse_regex(regex)
    print(parsed_tree)

    startState, finalState = "q0"
    nfa = {}
    nfa, start, final = tree_to_nfa(parsed_tree, startState, finalState, nfa)

    print(start)
    print(final)
    nfa[final]['output'] = "F"
    print(nfa)

    export_moore_automaton_to_csv(nfa, output_file, start)

if __name__ == "__main__":
    main()