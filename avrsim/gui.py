import tkinter as tk

from avrsim.assembler import Assembler
from avrsim.machine import Machine


class CodeText(tk.Text):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_configure(f"error", background="red")
        self.tag_lower(f"error")


class RegisterFrame(tk.Frame):

    def __init__(self, register, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._register = register
        self.lab_addr = tk.Label(self)
        self.lab_addr.pack()
        self.ent_val = tk.Entry(self)
        self.ent_val.pack()
        self.refresh()

    def refresh(self):
        self.lab_addr.config(text=self._register.addr_str)
        self.ent_val.delete(0, tk.END)
        self.ent_val.insert(0, str(self._register.val))


class MachineFrame(tk.Frame):

    def __init__(self, machine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widgets = []
        for i in range(16):
            for j in range(2):
                widget = RegisterFrame(machine.R[i + 16 * j], self)
                widget.grid(row=i, column=j)
                widgets.append(widget)
        self._widgets = widgets
        self.refresh()

    def refresh(self):
        for widget in self._widgets:
            widget.refresh()




def assemble(txt_code):
    assembler = Assembler(txt_code.get("0.0", tk.END))
    program = assembler.assemble()
    for tag_name in txt_code.tag_names():
        if tag_name.startswith("E"):
            txt_code.tag_remove(tag_name, "1.0", "end")
    if assembler.errors:
        for line_no, err in assembler.errors:
            lab_err = tk.Label(text=err)

            tag_name = f"E{line_no}"
            txt_code.tag_add(tag_name,
                             f"{line_no + 1}.0", f"{line_no + 1}.end")
            txt_code.tag_configure(tag_name, background="red")
            txt_code.tag_bind(tag_name, "<Enter>",
                              lambda event: lab_err.place(x=event.x, y=event.y))
            txt_code.tag_bind(tag_name, "<Leave>",
                              lambda event: lab_err.place_forget())


def main():
    machine = Machine()

    window = tk.Tk()
    window.title("AVR Simluator")

    frm_toolbar = tk.Frame(window)
    frm_toolbar.pack(fill=tk.X, side=tk.TOP)

    btn_assemble = tk.Button(frm_toolbar,
                             text="Assemble",
                             command=lambda: assemble(txt_code))
    btn_assemble.pack()

    txt_code = CodeText(window)
    txt_code.pack(fill=tk.BOTH, side=tk.LEFT)

    frm_machine = MachineFrame(machine, window)
    frm_machine.pack(fill=tk.BOTH, side=tk.LEFT)

    window.mainloop()


if __name__ == "__main__":
    main()
