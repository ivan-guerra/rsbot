"""Define a virtual machine that executes RSbot script."""

from instructions import Delay, MouseClick, MouseMove, MouseMoveClickBox


class VirtualMachine:  # pylint: disable=too-few-public-methods
    """Represents a virtual machine that executes RSbot scripts."""

    def _execute_instructions(self, instructions: list[str]) -> None:
        """Execute the list of instructions until the end is reached or an error occurs."""
        def execute(inst_type, raw_inst: str):
            obj = inst_type()
            obj.parse(raw_inst)
            obj.execute()

        pc = 0
        while pc in range(0, len(instructions)):
            raw_inst = instructions[pc]
            itype = raw_inst.split(" ")[0]
            if itype == "delay":
                execute(Delay, raw_inst)
            elif itype == "msclk":
                execute(MouseClick, raw_inst)
            elif itype == "msmv":
                execute(MouseMove, raw_inst)
            elif itype == "msmvcb":
                execute(MouseMoveClickBox, raw_inst)
            else:
                raise ValueError(f"unknown instruction '{itype}'")

            pc += 1

    def execute(self, script: str) -> None:
        """Execute an RSbot script.

        Args:
            script (str): The path to the script file to be executed.
        """
        instructions = []
        with open(script, "r", encoding="ascii") as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line.startswith("#") or stripped_line == "":
                    # Skip comments and blank lines.
                    continue
                instructions.append(stripped_line)

        self._execute_instructions(instructions)


vm = VirtualMachine()
vm.execute("scripts/test.rsbot")
