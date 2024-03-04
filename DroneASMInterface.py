# File: DroneASMInterface.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 03 Mar 2024
# Purpose:
#   An interface for using DroneASM written with tkinter
# Notes:
import os.path
import tkinter as tk
from tkinter import Tk, scrolledtext
from tkinter import ttk, filedialog, messagebox

from drone_asm.asm_compiler import compile, TokenizerErrorException, ValidationErrorException
from drone_asm.drone_virtual_machine import DroneVM, RuntimeSoftwareErrorException, RuntimeHardwareErrorException


class DroneASMInterface:
    def __init__(self):
        self.root = Tk()
        self.root.wm_title("DroneASM")
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.grid()
        self.nav_bar = ttk.Frame(self.frame, padding=2)
        self.nav_bar.grid(column=0, row=0)
        self.text_field = ttk.Frame(self.frame, padding=2)
        self.text_field.grid(column=0, row=1)
        self.prog_btns = ttk.Frame(self.frame, padding=10)
        self.prog_btns.grid(column=1, row=1)
        # Bar Buttons/Switches
        self.new_btn = ttk.Button(self.nav_bar, text="New File", command=self.new_file)
        self.new_btn.grid(column=1, row=0)
        self.load_btn = ttk.Button(self.nav_bar, text="Load File", command=self.load)
        self.load_btn.grid(column=2, row=0)
        self.save_btn = ttk.Button(self.nav_bar, text="Save File", command=self.save)
        self.save_btn.grid(column=3, row=0)
        self.simulation_switch = tk.Button(self.nav_bar, text="Simulation", bg="#53e079", width=10,
                                           command=self.sim_switch)
        self.simulation_switch.grid(column=0, row=0)
        self.quit_btn = ttk.Button(self.nav_bar, text="Quit", command=self.destroy)
        self.quit_btn.grid(column=4, row=0)
        # Compilation Buttons
        self.comp_btn = ttk.Button(self.prog_btns, text="Compile", command=self.compile)
        self.comp_btn.grid(column=0, row=0)
        self.run_btn = ttk.Button(self.prog_btns, text="Run", command=self.run_program)
        self.run_btn.grid(column=0, row=1)
        self.run_btn.config(state=tk.DISABLED)
        # Text box
        self.program_name = tk.Text(self.text_field, height=1, width=30)
        self.program_name.insert(tk.INSERT, "untitled.dasm")
        self.program_name.grid(column=0, row=0, sticky='w')
        self.program_txt = scrolledtext.ScrolledText(self.text_field)
        self.program_txt.grid(column=0, row=1)
        
        # Internal program management
        self.program = None
        self.vm = DroneVM()
        self.simulation = True
    
    def start(self):
        self.root.mainloop()
    
    def compile(self):
        prog_txt = self.program_txt.get('1.0', tk.END).strip().split("\n")
        self.program = None
        try:
            self.program = compile(prog_txt)
        except TokenizerErrorException as exp:
            messagebox.showerror("Compilation Parsing Error", exp.message)
        except ValidationErrorException as exp:
            messagebox.showerror("Invalid Line Error", exp.message)
        if self.program is not None:
            self.run_btn.config(state=tk.ACTIVE)
        else:
            self.run_btn.config(state=tk.DISABLED)
    
    def run_program(self):
        self.vm.reset()
        try:
            self.vm.run_program(self.program, self.simulation)
        except RuntimeSoftwareErrorException as exp:
            messagebox.showerror("Runtime Software Error", exp.message)
        except RuntimeHardwareErrorException as exp:
            messagebox.showerror("Runtime Hardware Error", exp.message)
    
    def new_file(self):
        self.run_btn.config(state=tk.DISABLED)
        self.program_name.delete('1.0', tk.END)
        self.program_txt.delete('1.0', tk.END)
        self.program_name.insert(tk.INSERT, "untitled.dasm")
    
    def save(self):
        with open(self.program_name.get('1.0', tk.END).strip(), "w") as fout:
            print(self.program_txt.get('1.0', tk.END).strip(), file=fout)
    
    def load(self):
        self.run_btn.config(state=tk.DISABLED)
        filename = tk.filedialog.askopenfilename(initialdir=os.path.curdir, title="Select File to Load",
                                                 filetypes=[("Drone ASM Files", "*.dasm"), ("All Files", "*.*")])
        if filename:
            self.program_txt.delete('1.0', tk.END)
            self.program_name.delete('1.0', tk.END)
            self.program_name.insert('1.0', os.path.relpath(filename))
            with open(filename, "r") as fin:
                self.program_txt.insert('1.0', fin.read())
                
    def sim_switch(self):
        self.simulation = not self.simulation
        if self.simulation:
            self.simulation_switch.config(text="Simulation", bg="#53e079")
        else:
            self.simulation_switch.config(text="LIVE", bg="#ed5858")
    
    def destroy(self):
        self.root.destroy()


def main():
    interface = DroneASMInterface()
    interface.start()


if __name__ == '__main__':
    main()
