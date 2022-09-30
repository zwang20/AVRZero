import tkinter.filedialog
import tkinter as tk

from avrsim.assembler import Assembler
from avrsim.machine import Machine


class CodeText(tk.Text):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lab_err_ls = {}

    def tag_error_clear(self):
        for tag, lab in self.lab_err_ls.items():
            self.tag_remove(tag, "0.0", "end")
            lab.destroy()

    def tag_error(self, line_no, err_str):
        lab_err = tk.Label(text=err_str)
        tag_name = f"E{line_no}"
        self.tag_add(tag_name,
                     f"{line_no + 1}.0", f"{line_no + 1}.end")
        self.tag_configure(tag_name, background="red")
        self.tag_bind(tag_name, "<Enter>",
                      lambda event: lab_err.place(x=event.x, y=event.y))
        self.tag_bind(tag_name, "<Leave>",
                      lambda event: lab_err.place_forget())
        self.tag_lower(tag_name)
        self.lab_err_ls[tag_name] = lab_err


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


def file_open(txt_code):
    file_name = tk.filedialog.askopenfilename(
        title="Select a file",
        filetypes=(("Assembly files", "*.asm"),))

    if not file_name:
        return

    try:
        with open(file_name) as file:
            txt_code.replace("0.0", "end", file.read())
    except OSError as err:
        tk.messagebox.showerror(
            title="Error opening file!",
            message=str(err))


def file_save_as(txt_code):
    file_name = tk.filedialog.asksaveasfilename(
        title="Save as...",
        filetypes=(("Assembly files", "*.asm"),))

    if not file_name:
        return

    try:
        with open(file_name, "w") as file:
            file.write(txt_code.get("0.0", "end"))
    except OSError as err:
        tk.messagebox.showerror(
            title="Error saving file!",
            message=str(err)
        )


def assemble(txt_code):
    assembler = Assembler(txt_code.get("0.0", tk.END))
    program = assembler.assemble()
    txt_code.tag_error_clear()
    if assembler.errors:
        for line_no, err in assembler.errors:
            txt_code.tag_error(line_no, str(err))


def main():
    machine = Machine()

    window = tk.Tk()
    window.title("AVR Simluator")

    menu = tk.Menu(window)
    menu_file = tk.Menu(menu, tearoff=0)
    menu_file.add_command(label="Open",
                          command=lambda: file_open(txt_code))
    menu_file.add_command(label="Save As",
                          command=lambda: file_save_as(txt_code))
    menu.add_cascade(label="File", menu=menu_file)
    window.config(menu=menu)

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
