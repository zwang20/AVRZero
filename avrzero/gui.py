import math
import tkinter.filedialog
import tkinter as tk

from avrzero.assembler import Assembler
from avrzero.formatter import Formatter
from avrzero.machine import Machine


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
        self.lab_name = tk.Label(self)
        self.lab_name.config(text=self._register.name)
        self.lab_name.pack()
        self.ent_val = tk.Entry(self,
                                validate="focusout",
                                validatecommand=self.validate)
        self.ent_val.bind("<Return>", lambda event: self.validate())
        self.ent_val.pack()
        self.ent_val.config(font="TkFixedFont")

    def get_format(self):
        return Formatter.by_name(self.master.frm_format_picker.formatter.get())

    def validate(self):
        try:
            self._register.val = int(self.ent_val.get(),
                                     base=self.get_format().base)
        except ValueError:
            pass
        self.refresh()

    def refresh(self):
        self.ent_val.delete(0, tk.END)
        self.ent_val.insert(
            0, self.get_format().format_spec.format(self._register.val))


class FormatPickerFrame(tk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatter = tk.StringVar()
        self._rad_ls = []

        for formatter in Formatter.all:
            rad = tk.Radiobutton(
                self,
                text=formatter.name,
                variable=self.formatter,
                value=formatter.name,
                command=self.master.refresh)
            rad.pack(side=tk.LEFT)
            self._rad_ls.append(rad)
        self._rad_ls[0].select()


class RegisterFileFrame(tk.Frame):

    def __init__(self, registers, n_rows, n_cols, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frm_format_picker = FormatPickerFrame(self)
        self.frm_format_picker.grid(row=0, columnspan=n_cols)
        widgets = []
        for i in range(n_rows):
            for j in range(n_cols):
                widget = RegisterFrame(registers[i + n_rows * j], self)
                widget.grid(row=i + 1, column=j)
                widgets.append(widget)
        self._widgets = widgets
        self.refresh()

    def refresh(self):
        for widget in self._widgets:
            widget.refresh()


class FlashFrame(tk.Frame):

    def __init__(self, PC, flash, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prev_select = 0
        self._PC = PC
        self._flash = flash

        self.frm_format_picker = FormatPickerFrame(self)
        self.frm_format_picker.pack(side=tk.TOP)

        self.listbox = tk.Listbox(self)
        self.listbox.config(font="TkFixedFont")
        self.listbox.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        format_spec = Formatter.by_name(
            self.frm_format_picker.formatter.get()).format_spec
        for i in range(len(self._flash)):
            self.listbox.insert(tk.END, f"{i:8d} : "
                + format_spec.format(self._flash[i]))

        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(fill=tk.BOTH, side=tk.LEFT)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.refresh()

    def refresh(self):
        format_spec = Formatter.by_name(
            self.frm_format_picker.formatter.get()).format_spec

        self.listbox.delete(0, 2**8 - 1)
        for i in range(2**8):
            self.listbox.insert(i, f"{i:8d} : "
                + format_spec.format(self._flash[i]))

        self.listbox.see(self._PC.val)
        self.listbox.itemconfigure(self._prev_select, background="")
        self.listbox.itemconfigure(self._PC.val, background="grey")
        self._prev_select = self._PC.val


class AVRSimTk(tk.Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.machine = Machine()

        self.title("AVR Zero")

        self.menu = tk.Menu(self)
        menu_file = tk.Menu(self.menu, tearoff=0)
        menu_file.add_command(label="Open", command=self.file_open)
        menu_file.add_command(label="Save As", command=self.file_save_as)
        self.menu.add_cascade(label="File", menu=menu_file)
        self.config(menu=self.menu)

        self.frm_toolbar = tk.Frame(self)
        self.frm_toolbar.pack(fill=tk.X, side=tk.TOP)

        self.btn_assemble = tk.Button(
            self.frm_toolbar, text="Assemble", command=self.assemble)
        self.btn_assemble.pack(side=tk.LEFT)
        self.btn_step = tk.Button(
            self.frm_toolbar, text="Step", command=self.step)
        self.btn_step.pack(side=tk.RIGHT)
        self.btn_reset = tk.Button(
            self.frm_toolbar, text="Reset", command=self.reset)
        self.btn_reset.pack(side=tk.RIGHT)

        self.txt_code = CodeText(self)
        self.txt_code.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.frm_machine = tk.Frame(self)
        self.frm_machine.pack(fill=tk.BOTH, side=tk.LEFT)

        self.frm_gpr = RegisterFileFrame(
            self.machine.R, 16, 2, self.frm_machine)
        self.frm_gpr.pack(side=tk.LEFT, anchor=tk.N)

        self.frm_spr = RegisterFileFrame(
            [self.machine.X, self.machine.Y, self.machine.Z,
             self.machine.SP, self.machine.SREG, self.machine.PC],
            3, 2, self.frm_machine)
        self.frm_spr.pack(side=tk.LEFT, anchor=tk.N)

        self.frm_stack = FlashFrame(self.machine.SP,
                                    self.machine.memory,
                                    self.frm_machine)
        self.frm_stack.pack(fill=tk.Y, side=tk.LEFT)

        self.frm_flash = FlashFrame(self.machine.PC,
                                    self.machine.flash,
                                    self.frm_machine)
        self.frm_flash.pack(fill=tk.Y, side=tk.LEFT)

    def file_open(self):
        file_name = tk.filedialog.askopenfilename(
            title="Select a file",
            filetypes=(("Assembly files", "*.asm"),))

        if not file_name:
            return

        try:
            with open(file_name) as file:
                self.txt_code.replace("0.0", "end", file.read())
        except OSError as err:
            tk.messagebox.showerror(
                title="Error opening file!",
                message=str(err))

    def file_save_as(self):
        file_name = tk.filedialog.asksaveasfilename(
            title="Save as...",
            filetypes=(("Assembly files", "*.asm"),))

        if not file_name:
            return

        try:
            with open(file_name, "w") as file:
                file.write(self.txt_code.get("0.0", "end"))
        except OSError as err:
            tk.messagebox.showerror(
                title="Error saving file!",
                message=str(err)
            )

    def assemble(self):
        assembler = Assembler(self.txt_code.get("0.0", tk.END))
        program = assembler.assemble()
        self.txt_code.tag_error_clear()
        if assembler.errors:
            for line_no, err in assembler.errors:
                self.txt_code.tag_error(line_no, str(err))
        else:
            self.machine.load_program(program)
            self.frm_flash.refresh()

    def reset(self):
        self.machine.reset()
        self.frm_gpr.refresh()
        self.frm_spr.refresh()
        self.frm_stack.refresh()
        self.frm_flash.refresh()

    def step(self):
        self.machine.step()
        self.frm_gpr.refresh()
        self.frm_spr.refresh()
        self.frm_stack.refresh()
        self.frm_flash.refresh()


if __name__ == "__main__":
    AVRSimTk().mainloop()
