"""Define a virtual machine that executes RSbot script."""

from instructions import (Context, Delay, MouseClick,
                          MouseMove, MouseMoveClickBox, MouseMoveColor,
                          MouseMoveText, Subtract, Store,
                          JumpNotEqual)


class VirtualMachine:  # pylint: disable=too-few-public-methods
    """Represents a virtual machine that executes RSbot scripts."""

    def _execute_instructions(self, instructions: list[str]) -> None:
        """Execute the list of instructions until the end is reached or an error occurs."""
        def execute(inst_type, raw_inst: str, ctxt: Context):
            obj = inst_type(ctxt)
            obj.parse(raw_inst)
            obj.execute()

        ctxt = Context(pc=0, registers={"R0": 0}, labels={})
        while ctxt.pc in range(0, len(instructions)):
            raw_inst = instructions[ctxt.pc]
            itype = raw_inst.split(" ")[0]
            if itype == "delay":
                execute(Delay, raw_inst, ctxt)
            elif itype == "msclk":
                execute(MouseClick, raw_inst, ctxt)
            elif itype == "msmv":
                execute(MouseMove, raw_inst, ctxt)
            elif itype == "msmvcb":
                execute(MouseMoveClickBox, raw_inst, ctxt)
            elif itype == "msmvcolor":
                execute(MouseMoveColor, raw_inst, ctxt)
            elif itype == "msmvtext":
                execute(MouseMoveText, raw_inst, ctxt)
            elif itype == "sub":
                execute(Subtract, raw_inst, ctxt)
            elif itype == "store":
                execute(Store, raw_inst, ctxt)
            elif itype == "jne":
                execute(JumpNotEqual, raw_inst, ctxt)
            elif itype.endswith(":"):
                ctxt.pc += 1
                ctxt.labels[itype.removesuffix(":")] = ctxt.pc
            else:
                raise ValueError(f"unknown instruction '{itype}'")

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
