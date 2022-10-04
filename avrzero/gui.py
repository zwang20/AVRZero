import math
import os
import tkinter.filedialog
import tkinter as tk

from avrzero import BYTE_SIZE, WORD_SIZE
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
        lab_err = tk.Label(text=err_str, justify=tk.LEFT)
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
        self._register.trace_add("write", self.refresh)
        self._blink = None
        self.lab_name = tk.Label(self, text=self._register.name)
        self.lab_name.pack(fill=tk.X, side=tk.LEFT)
        self.ent_val = tk.Entry(self,
                                validate="focusout",
                                validatecommand=self.validate)
        self.ent_val.bind("<Return>", lambda event: self.validate())
        self.ent_val.pack(side=tk.LEFT)
        self.ent_val.config(font="TkFixedFont")

    def get_format(self):
        return Formatter.by_name(self.master.frm_format_picker.formatter.get())

    def validate(self):
        try:
            converter = self.get_format().converter
            self._register.val = converter(self.ent_val.get())
            self.winfo_toplevel().show_message(f"{self._register.name} saved")
        except (TypeError, ValueError) as err:
            self.winfo_toplevel().show_message(str(err))
        self.refresh()

    def blink_entry(self):
        self.ent_val.configure(background="grey")
        if self._blink is not None:
            self.ent_val.after_cancel(self._blink)
        self._blink = self.ent_val.after(500, lambda: self.ent_val.configure(
            background="systemTextBackgroundColor"))

    def refresh(self, *args):
        self.ent_val.delete(0, tk.END)
        self.ent_val.insert(0, self.get_format().format(
            self._register.val, n_bits=self._register.N_BITS))
        if args:
            self.blink_entry()


class FormatPickerFrame(tk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatter = tk.StringVar(self)
        self._rad_ls = []

        for formatter in Formatter.all:
            rad = tk.Radiobutton(
                self,
                text=formatter.name,
                variable=self.formatter,
                value=formatter.name)
            rad.pack(side=tk.LEFT)
            self._rad_ls.append(rad)
        self._rad_ls[0].select()


class RegisterFileFrame(tk.Frame):

    def __init__(self, registers, n_rows, n_cols, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frm_format_picker = FormatPickerFrame(self)
        self.frm_format_picker.grid(row=0, columnspan=n_cols)
        self.frm_format_picker.formatter.trace_add("write", self.refresh)
        widgets = []
        for i in range(n_rows):
            for j in range(n_cols):
                widget = RegisterFrame(registers[i + n_rows * j], self)
                widget.grid(row=i + 1, column=j, sticky=tk.E)
                widgets.append(widget)
        self._widgets = widgets
        self.refresh()

    def refresh(self, *args):
        for widget in self._widgets:
            widget.refresh()


class FlashFrame(tk.Frame):

    def __init__(self, counter, flash, n_bits, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._n_bits = n_bits
        self._idx_len = math.ceil(math.log(len(flash), 10))

        self._flash = flash
        for i, register in enumerate(flash):
            register.trace_add("write",
                               lambda *args, i=i: self.update_line(idx=i))

        self._prev_select = 0
        self._counter = counter
        self._counter.trace_add("write", self.update_highlight)

        self.frm_format_picker = FormatPickerFrame(self)
        self.frm_format_picker.pack(side=tk.TOP)
        self.frm_format_picker.formatter.trace_add("write", self.refresh)

        self.listbox = tk.Listbox(self)
        self.listbox.config(font="TkFixedFont")
        self.listbox.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(fill=tk.BOTH, side=tk.LEFT)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.refresh()

    def update_line(self, idx):
        val = self._flash[idx].get()
        formatter = Formatter.by_name(self.frm_format_picker.formatter.get())
        line = "{:<{}d} | {}".format(idx,
                                     self._idx_len,
                                     formatter.format(val, self._n_bits))

        if line != self.listbox.get(idx):
            self.listbox.delete(idx)
            self.listbox.insert(idx, line)
            self.update_highlight()

    def refresh(self, *args):
        formatter = Formatter.by_name(self.frm_format_picker.formatter.get())
        self.listbox.delete(0, tk.END)
        for i, cell in enumerate(self._flash):
            self.listbox.insert(tk.END, "{:<{}d} | {}".format(
                i, self._idx_len, formatter.format(cell.get(), self._n_bits)))
        self.update_highlight()

    def update_highlight(self, *args):
        self.listbox.itemconfigure(self._prev_select, background="")
        self.listbox.itemconfigure(self._counter.val, background="grey")
        self._prev_select = self._counter.val
        self.listbox.see(self._counter.val)


class AVRSimTk(tk.Tk):

    EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), "example")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.machine = Machine(win=self)

        self.title("AVR Zero")

        self.menu = tk.Menu(self)
        menu_file = tk.Menu(self.menu, tearoff=0)
        menu_file.add_command(label="Open", command=self.ask_file_open)
        menu_file.add_command(label="Save As", command=self.file_save_as)

        menu_example = tk.Menu(menu_file, tearoff=0)
        for file_name in os.listdir(self.EXAMPLE_DIR):
            name = os.path.splitext(file_name)[0].replace("_", " ").title()
            path = os.path.join(self.EXAMPLE_DIR, file_name)
            menu_example.add_command(
                label=name, command=lambda path=path: self.file_open(path))
        menu_file.add_cascade(label="Example", menu=menu_example)

        self.menu.add_cascade(label="File", menu=menu_file)
        self.config(menu=self.menu)

        self.frm_toolbar = tk.Frame(self)
        self.frm_toolbar.pack(fill=tk.X)

        self.btn_assemble = tk.Button(
            self.frm_toolbar, text="Assemble", command=self.assemble)
        self.btn_assemble.pack(side=tk.LEFT)
        self.btn_step = tk.Button(
            self.frm_toolbar, text="Step", command=self.step)
        self.btn_step.pack(side=tk.RIGHT)
        self.btn_reset = tk.Button(
            self.frm_toolbar, text="Reset", command=self.reset)
        self.btn_reset.pack(side=tk.RIGHT)

        self.frm_main = tk.Frame(self)
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        self.txt_code = CodeText(self.frm_main)
        self.txt_code.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.frm_machine = tk.Frame(self.frm_main)
        self.frm_machine.pack(fill=tk.Y, side=tk.LEFT, expand=True)
        self.frm_machine.rowconfigure(0, weight=1)
        self.frm_machine.rowconfigure(1, weight=1)

        self.frm_gpr = RegisterFileFrame(
            self.machine.R, 16, 2, self.frm_machine)
        self.frm_gpr.grid(row=0, column=0, sticky=tk.N + tk.S)

        self.frm_spr = RegisterFileFrame(
            [self.machine.X, self.machine.Y, self.machine.Z,
             self.machine.SP, self.machine.SREG, self.machine.PC],
            3, 2, self.frm_machine)
        self.frm_spr.grid(row=1, column=0, sticky=tk.N + tk.S)

        self.frm_stack = FlashFrame(self.machine.SP,
                                    self.machine.memory,
                                    BYTE_SIZE,
                                    self.frm_machine)
        self.frm_stack.grid(row=0, column=1, sticky=tk.N + tk.S)

        self.frm_flash = FlashFrame(self.machine.PC,
                                    self.machine.flash,
                                    WORD_SIZE,
                                    self.frm_machine)
        self.frm_flash.grid(row=1, column=1, sticky=tk.N + tk.S)

        self.lab_msg = tk.Label(self,
                                text="No message.",
                                background="grey")
        self.lab_msg.pack(fill=tk.X)

    def show_message(self, text):
        self.lab_msg.config(text=text)

    def ask_file_open(self):
        file_name = tk.filedialog.askopenfilename(
            title="Select a file",
            filetypes=(("Assembly files", "*.asm"),))

        if not file_name:
            return

        self.file_open(file_name)

    def file_open(self, file_name):
        try:
            with open(file_name) as file:
                self.txt_code.replace("0.0", "end", file.read())
        except OSError as err:
            self.show_message(str(err))

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
            self.frm_flash.listbox.configure(state=tk.DISABLED)
            self.machine.load_program(program)
            self.frm_flash.listbox.configure(state=tk.NORMAL)
            self.frm_flash.refresh()

    def reset(self):
        self.machine.reset()

    def step(self):
        self.machine.step()


if __name__ == "__main__":
    AVRSimTk().mainloop()
