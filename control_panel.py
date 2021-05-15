import os
import shlex
import math
import random
from typing import Optional, List, Tuple, Iterable, Union
from rtree import RTree, RTreeSplitType
from visualization import Visualizer


class ControlPanel:
    def __init__(self, directory: str):
        self._dir = directory
        self._selected = None
        self._load_trees()

    def run(self):
        status = None
        while True:
            self._clear()
            selected_mode = self._selected is not None

            if selected_mode:
                self._print_selected(status)
            else:
                self._print_list(status)
            status = None

            cmd_input = input(self._selected[0] + '> ' if selected_mode else '> ')
            if not cmd_input:
                continue

            cmd, args = self._parse_cmd(cmd_input)

            if cmd == 'exit' and not selected_mode:
                # self._clear()
                break

            if (cmd, selected_mode) in self._COMMANDS:
                if len(args) != self._COMMANDS[(cmd, selected_mode)][1]:
                    status = 'Usage: {} {}'.format(cmd, self._COMMANDS[cmd, selected_mode][2])
                else:
                    status = self._COMMANDS[(cmd, selected_mode)][0](self, args)
            else:
                status = 'Command \'{}\' not found'.format(cmd)

    def _load_trees(self):
        self._trees = []

        if not os.path.isdir(self._dir):
            os.mkdir(self._dir)

        for f in os.listdir(self._dir):
            if os.path.isfile(os.path.join(self._dir, f)) and f.lower().endswith('.rtree'):
                try:
                    tree = RTree.from_file(os.path.join(self._dir, f))
                    self._trees.append((f[:-len('.rtree')], tree))
                except IOError:
                    pass

    def _clear(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def _parse_cmd(self, cmd: str) -> Tuple[str, List[str]]:
        args = shlex.split(cmd)
        return args[0].lower(), args[1:]

    def _print_list(self, status: Optional[str]):
        cols = ['ID', 'Name', 'Dim', 'Node size', 'Split type']
        cols_w = self._calcColsWidths() if self._trees else [0 for _ in cols]

        for i, col in enumerate(cols):
            cols_w[i] = max(cols_w[i], len(col))

        title = 'List of R-trees in directory \'{}\''.format(self._dir)

        w = max(sum(cols_w) + len(cols_w) + 1, len(title) + 2, 0 if status is None else len(status) + 4)

        self._print_status(status, w)
        print(self._center(title, w))
        print()
        print()

        self._print_table_row(cols, cols_w, w)
        self._print_table_row(('-' * c for c in cols_w), cols_w, w)

        for i, (name, tree) in enumerate(self._trees):
            self._print_table_row([
                self._right(str(i), cols_w[0]),
                self._left(name, cols_w[1]),
                self._right(str(tree.get_dimensions()), cols_w[2]),
                self._right('{} B'.format(str(tree._storage.get_node_size())), cols_w[3]),
                self._left(tree._storage.get_split_type().to_str(), cols_w[4])
            ], cols_w, w)
        print()
        print()
        print()

        self._print_commands(False)

    def _print_selected(self, status: Optional[str]):
        title = 'R-tree \'{}\''.format(self._selected[0])
        labels = ['Dimensions', 'Node size', 'Split type', 'Number of nodes']
        labels_w = max(len(l) for l in labels)

        fields = [
            str(self._selected[1].get_dimensions()),
            '{} B'.format(str(self._selected[1]._storage.get_node_size())),
            self._selected[1]._storage.get_split_type().to_str(),
            str(self._selected[1]._storage.count())
        ]
        fields_w = max(len(s) for s in fields)

        rows = []

        for l, s in zip(labels, fields):
            rows.append('{}: {}'.format(self._right(l, labels_w), self._left(s, fields_w)))

        w = max(len(title) + 2, max(len(r) for r in rows) + 2, 0 if status is None else len(status) + 4)

        self._print_status(status, w)
        print(self._center(title, w))
        print()

        for r in rows:
            print(self._center(r, w))
        print()
        print()
        print()

        self._print_commands(True)
        pass

    def _print_status(self, status: Optional[str], width: int):
        if status is None:
            return

        print('#' * width)
        print('#', self._center(status, width - 2), '#', sep='')
        print('#' * width)
        print()

    def _print_table_row(self, cells: Iterable[str], cols_w: List[int], width: int):
        print(self._center(' '.join(self._center(s, cols_w[i]) for i, s in enumerate(cells)), width))

    def _print_commands(self, selected_mode: bool):
        print('Commands:')

        cmds = []

        for (cmd, mode), val in self._COMMANDS.items():
            if mode != selected_mode:
                continue
            cmds.append(('    {} {}'.format(cmd, val[2]), val[3]))

        w = max(len(cmd) for cmd, _ in cmds) + 4

        for cmd, desc in cmds:
            print(self._left(cmd, w), desc, sep='')
        print()

    def _dialog_create(self, name: str):
        title = 'Creating R-tree \'{}\''.format(name)
        labels = [
            ('Dimensions', ': ', self._validate_int, (1, 30)),
            ('Node size', ' (in bytes): ', self._validate_int, (128, 8192)),
            ('Split type', ' (\'bruteforce\', \'quadratic\', \'linear\'): ', self._validate_choice, ['bruteforce', 'quadratic', 'linear'])
        ]
        labels_w = max(len(l) + len(h) for l, h, _, _ in labels)

        fields = []
        filled = 0
        status = None

        while filled < len(labels):
            self._clear()
            w = max(len(title) + 2, labels_w * 2, 0 if status is None else len(status) + 4)
            self._print_status(status, w)
            status = None
            print(self._center(title, w))
            print()

            for i, (l, h, fn, arg) in enumerate(labels):
                print(self._right(l + h, labels_w), end='')
                if i < filled:
                    print(fields[i])
                    continue

                value = input('')
                status = fn(l, value, arg)
                if status is not None:
                    break
                filled += 1
                fields.append(value)

        return int(fields[0]), int(fields[1]), RTreeSplitType.from_str(fields[2])

    def _dialog_search_results(self, result: List[Tuple[List[int], int]]):
        _, lines = os.get_terminal_size()

        pages = math.ceil(len(result) / (lines - 1))

        self._clear()

        for i, res in enumerate(result):
            print('({}) => {}'.format(', '.join([str(x) for x in res[0]]), res[1]))

            if (i + 1) % (lines - 1) == 0 and i != (len(result) - 1):
                print('[PAGE {}/{}]'.format(math.floor((i + 1) / (lines - 1)), pages), end='')
                input(' Press ENTER to go to the next page ')
                self._clear()

        lp = len(result) % (lines - 1)
        if lp != 0 or len(result) == 0:
            for _ in range(lines - lp - 1):
                print()

        if len(result) == 0:
            print('[EMPTY]', end='')
        else:
            print('[PAGE {}/{}]'.format(pages, pages), end='')
        input(' Press ENTER to quit ')

    def _calcColsWidths(self) -> List[int]:
        return [
            len(str(len(self._trees) - 1)),
            max(len(name) for name, _ in self._trees),
            max(len(str(t.get_dimensions())) for _, t in self._trees),
            max(len(str(t._storage.get_node_size())) + 2 for _, t in self._trees),
            max(len(t._storage.get_split_type().to_str()) for _, t in self._trees)
        ]

    def _center(self, msg: str, width: int) -> str:
        padding = (width - len(msg)) / 2
        return ' ' * math.floor(padding) + msg + ' ' * math.ceil(padding)

    def _left(self, msg: str, width: int) -> str:
        return msg + ' ' * (width - len(msg))

    def _right(self, msg: str, width: int) -> str:
        return ' ' * (width - len(msg)) + msg

    def _find_tree_index(self, arg: str) -> Optional[int]:
        try:
            i = int(arg)
            if 0 <= i < len(self._trees):
                return i
        except ValueError:
            pass
        for i, (name, _) in enumerate(self._trees):
            if name == arg:
                return i

    def _validate_int(self, name: str, value: str, bounds: Tuple[int, int]):
        try:
            val = int(value)
            if not bounds[0] <= val <= bounds[1]:
                return '{} must be between {} and {}'.format(name, bounds[0], bounds[1])
            return None
        except ValueError:
            return '\'{}\' is not a valid number'.format(value)

    def _validate_choice(self, name: str, value: str, choices: List[str]):
        if value in choices:
            return None
        return '{} must be one of these values: \'{}\''.format(name, '\', \''.join(choices))

    def _parse_point(self, arg: str, dim: int) -> Union[List[int], str]:
        p_str = arg.split(',')

        if len(p_str) != dim:
            return '\'{}\' does not define a point in {} dimensions'.format(arg, dim)

        p = []
        for x_str in p_str:
            try:
                x = int(x_str)
                p.append(x)
            except ValueError:
                return '\'{}\' is not a valid number'.format(x_str)
        return p

    def _box(self, p: List[int], q: List[int]) -> Tuple[List[int], List[int]]:
        a = []
        b = []

        for i in range(len(p)):
            a.append(min(p[i], q[i]))
            b.append(max(p[i], q[i]))

        return a, b

    def _cmd_reload(self, args: List[str]) -> Optional[str]:
        self._load_trees()
        return 'Directory reloaded'

    def _cmd_select(self, args: List[str]) -> Optional[str]:
        i = self._find_tree_index(args[0])
        if i is None:
            return 'Cannot find R-tree with id or name \'{}\''.format(args[0])

        self._selected = self._trees[i]

    def _cmd_create(self, args: List[str]) -> Optional[str]:
        for name, _ in self._trees:
            if name == args[0]:
                return 'R-tree named \'{}\' already exists'.format(args[0])

        dim, node_size, split_type = self._dialog_create(args[0])
        try:
            tree = RTree.create_in_file(os.path.join(self._dir, args[0] + '.rtree'), dim, node_size, split_type)
            self._trees.append((args[0], tree))
            return 'R-tree created'
        except ValueError:
            return 'Node size is too small for this number of dimensions'
        except IOError:
            return 'Error creating R-tree file'

    def _cmd_rename(self, args: List[str]) -> Optional[str]:
        i = self._find_tree_index(args[0])
        if i is None:
            return 'Cannot find R-tree with id or name \'{}\''.format(args[0])

        for name, _ in self._trees:
            if name == args[1]:
                return 'R-tree named \'{}\' already exists'.format(args[1])

        try:
            old_name, tree = self._trees.pop(i)
            del tree._storage

            old_path = os.path.join(self._dir, old_name + '.rtree')
            new_path = os.path.join(self._dir, args[1] + '.rtree')

            os.rename(old_path, new_path)

            self._trees.insert(i, (args[1], RTree.from_file(new_path)))
            return 'R-tree renamed'
        except IOError:
            return 'Error renaming R-tree file'

    def _cmd_delete(self, args: List[str]) -> Optional[str]:
        i = self._find_tree_index(args[0])
        if i is None:
            return 'Cannot find R-tree with id or name \'{}\''.format(args[0])

        try:
            name, tree = self._trees.pop(i)
            del tree._storage

            os.remove(os.path.join(self._dir, name + '.rtree'))
            return 'R-tree deleted'
        except IOError:
            return 'Error deleting R-tree file'

    def _cmd_show(self, args: List[str]) -> Optional[str]:
        if not 1 <= self._selected[1].get_dimensions() <= 3:
            return 'Visualization is only available for up to 3 dimensional trees'

        Visualizer.visualize(self._selected[1])
        return 'Opening visualization in browser'

    def _cmd_show_html(self, args: List[str]) -> Optional[str]:
        if not 1 <= self._selected[1].get_dimensions() <= 3:
            return 'Visualization is only available for up to 3 dimensional trees'

        Visualizer.visualize(self._selected[1], True)
        return 'Visualization generated to \'./vis.html\''

    def _cmd_insert(self, args: List[str]) -> Optional[str]:
        try:
            n = int(args[0])

            for i in range(n):
                self._selected[1].insert([random.randint(self._INSERT_RANGE[0], self._INSERT_RANGE[1]) for _ in range(self._selected[1].get_dimensions())], i)
            return 'Random data points inserted'
        except ValueError:
            return '\'{}\' is not a valid number'.format(args[0])

    def _cmd_search_knn(self, args: List[str]) -> Optional[str]:
        try:
            k = int(args[0])
            p = self._parse_point(args[1], self._selected[1].get_dimensions())

            if type(p) == str:
                return p

            result = self._selected[1].search_knn(p, k)
            self._dialog_search_results(result)
        except ValueError:
            return '\'{}\' is not a valid number'.format(args[0])

    def _cmd_search_range(self, args: List[str]) -> Optional[str]:
        dim = self._selected[1].get_dimensions()
        p = self._parse_point(args[0], dim)
        q = self._parse_point(args[1], dim)

        if type(p) == str:
            return p

        if type(q) == str:
            return q

        box = self._box(p, q)
        result = self._selected[1].search_range(box)
        self._dialog_search_results(result)

    def _cmd_exit(self, args: List[str]) -> Optional[str]:
        self._selected = None
        return None

    _COMMANDS = {
        # CMD, SELECTED_MODE
        ('reload', False): (_cmd_reload, 0, '', 'Reloads the directory'),
        ('select', False): (_cmd_select, 1, 'R-TREE', 'Selects R-tree to work with'),
        ('create', False): (_cmd_create, 1, 'NAME', 'Creates new R-tree with name NAME'),
        ('rename', False): (_cmd_rename, 2, 'R-TREE NAME', 'Renames existing R-tree'),
        ('delete', False): (_cmd_delete, 1, 'R-TREE', 'Deletes existing R-tree'),
        ('exit', False): (None, 0, '', 'Exits the program'),
        ('show', True): (_cmd_show, 0, '', 'Shows visualization of the R-tree (on some systems this may not work, in that case use \'show-html\' instead)'),
        ('show-html', True): (_cmd_show_html, 0, '', 'Generates visualization of the R-tree to html'),
        ('insert', True): (_cmd_insert, 1, 'N', 'Inserts N new random data points into the R-tree'),
        ('search-knn', True): (_cmd_search_knn, 2, 'K "X0, X1, ..., XN"', 'Searches the R-tree for K nearest neighbors to a given point X'),
        ('search-range', True): (_cmd_search_range, 2, '"X0, X1, ..., XN" "Y0, Y1, ..., YN"', 'Searches the R-tree for data points in a given bounding box. X, Y should be oposite corners'),
        ('exit', True): (_cmd_exit, 0, '', 'Exits to list od R-trees'),
    }
    _INSERT_RANGE = (-1000, 1000)


if __name__ == "__main__":
    panel = ControlPanel('./data')
    panel.run()
