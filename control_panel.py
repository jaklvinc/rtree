import os
import shlex
import math
from typing import Optional, List, Tuple, Iterable


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

            if (cmd, selected_mode) in self.COMMANDS:
                if len(args) != self.COMMANDS[(cmd, selected_mode)][1]:
                    status = 'Usage: {} {}'.format(cmd, self.COMMANDS[cmd, selected_mode][2])
                else:
                    status = self.COMMANDS[(cmd, selected_mode)][0](self, args)
            else:
                status = 'Command \'{}\' not found'.format(cmd)

    def _load_trees(self):
        self._trees = []

        if not os.path.isdir(self._dir):
            os.mkdir(self._dir)

        for f in os.listdir(self._dir):
            if os.path.isfile(os.path.join(self._dir, f)) and f.lower().endswith('.rtree'):
                self._trees.append((f[:-len('.rtree')], None))

    def _clear(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def _parse_cmd(self, cmd: str) -> Tuple[str, List[str]]:
        args = shlex.split(cmd)
        return args[0].lower(), args[1:]

    def _print_list(self, status: Optional[str]):
        # TODO: change this?
        cols = ['ID', 'Name', 'Size']
        cols_w = self._calcColsWidths()

        for i, col in enumerate(cols):
            cols_w[i] = max(cols_w[i], len(col))

        title = 'List of r-trees in directory \'{}\''.format(self._dir)

        w = max(sum(cols_w) + len(cols_w) + 1, len(title) + 2, 0 if status is None else len(status) + 4)

        self._print_status(status, w)
        print(self._center(title, w))
        print()
        print()

        # TODO: add more fields
        self._print_table_row(cols, cols_w, w)
        self._print_table_row(('-' * c for c in cols_w), cols_w, w)

        for i, (name, tree) in enumerate(self._trees):
            self._print_table_row([
                self._right(str(i), cols_w[0]),
                self._left(name, cols_w[1]),
                self._right('0', cols_w[2])
            ], cols_w, w)
        print()
        print()
        print()

        self._print_commands(False)

    def _print_selected(self, status: Optional[str]):
        title = 'R-tree \'{}\''.format(self._selected[0])
        # TODO: remove name?
        # TODO: add more fields
        labels = ['Name', 'Size']
        label_w = max(len(r) for r in labels)

        fields = [(self._selected[0], self._left), ('0', self._right)]
        fields_w = max(len(s) for s, fn in fields)

        rows = []

        for i, (s, fn) in enumerate(fields):
            rows.append('{}: {}'.format(self._right(labels[i], label_w), fn(s, fields_w)))

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

        for (cmd, mode), val in self.COMMANDS.items():
            if mode != selected_mode:
                continue
            cmds.append(('    {} {}'.format(cmd, val[2]), val[3]))

        w = max(len(cmd) for cmd, _ in cmds) + 4

        for cmd, desc in cmds:
            print(self._left(cmd, w), desc, sep='')
        print()

    def _calcColsWidths(self) -> List[int]:
        # TODO: Add more fields
        return [len(str(len(self._trees) - 1)), max(len(name) for name, _ in self._trees), 0]

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

    def _cmd_reload(self, args: List[str]) -> Optional[str]:
        self._load_trees()
        return 'Directory reloaded'

    def _cmd_select(self, args: List[str]) -> Optional[str]:
        i = self._find_tree_index(args[0])
        if i is None:
            return 'Cannot find r-tree with id or name \'{}\''.format(args[0])

        self._selected = self._trees[i]

    def _cmd_create(self, args: List[str]) -> Optional[str]:
        for name, _ in self._trees:
            if name == args[0]:
                return 'R-tree named \'{}\' already exists'.format(args[0])

        # TODO: create new R-tree

        pass

    def _cmd_rename(self, args: List[str]) -> Optional[str]:
        i = self._find_tree_index(args[0])
        if i is None:
            return 'Cannot find r-tree with id or name \'{}\''.format(args[0])

        for name, _ in self._trees:
            if name == args[1]:
                return 'R-tree named \'{}\' already exists'.format(args[1])

        # TODO: change after RTree is implemented

        try:
            os.rename(
                os.path.join(self._dir, self._trees[i][0] + '.rtree'),
                os.path.join(self._dir, args[1] + '.rtree')
            )
            self._trees[i] = (args[1], self._trees[i][1])
            return 'R-tree renamed'
        except IOError:
            return 'Error with renaming r-tree file'

    def _cmd_delete(self, args: List[str]) -> Optional[str]:
        i = self._find_tree_index(args[0])
        if i is None:
            return 'Cannot find r-tree with id or name \'{}\''.format(args[0])

        # TODO: change after RTree is implemented

        try:
            os.remove(os.path.join(self._dir, self._trees[i][0] + '.rtree'))
            self._trees.pop(i)
            return 'R-tree deleted'
        except IOError:
            return 'Error with deleting r-tree file'

    def _cmd_exit(self, args: List[str]) -> Optional[str]:
        self._selected = None
        return None

    COMMANDS = {
        # CMD, SELECTED_MODE
        ('reload', False): (_cmd_reload, 0, '', 'Reloads the directory'),
        ('select', False): (_cmd_select, 1, 'R-TREE', ''),
        ('create', False): (_cmd_create, 1, 'NAME', 'Creates new r-tree with name NAME'),
        ('rename', False): (_cmd_rename, 2, 'R-TREE NAME', 'Renames existing r-tree'),
        ('delete', False): (_cmd_delete, 1, 'R-TREE', 'Deletes existing r-tree'),
        ('exit', False): (None, 0, '', 'Exits the program'),
        ('exit', True): (_cmd_exit, 0, '', 'Exits to list od r-trees'),
    }


if __name__ == "__main__":
    panel = ControlPanel('./data')
    panel.run()
