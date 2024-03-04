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
        # Route Displats
        self.xy_display = tk.Canvas(self.prog_btns, width=100, height=100, bg="white")
        self.xy_display.grid(column=0, row=3)
        self.xy_label = tk.Label(self.prog_btns, text="X Y")
        self.xy_label.grid(column=0, row=2)
        self.xz_display = tk.Canvas(self.prog_btns, width=100, height=100, bg="white")
        self.xz_display.grid(column=0, row=5)
        self.xz_label = tk.Label(self.prog_btns, text="X Z")
        self.xz_label.grid(column=0, row=4)
        self.yz_display = tk.Canvas(self.prog_btns, width=100, height=100, bg="white")
        self.yz_display.grid(column=0, row=7)
        self.yz_label = tk.Label(self.prog_btns, text="Y Z")
        self.yz_label.grid(column=0, row=6)
        self.xy_lines = self.xz_lines = self.yz_lines = []
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
        self.clear_paths()
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
        self.clear_paths()
        try:
            self.vm.run_program(self.program, self.simulation)
        except RuntimeSoftwareErrorException as exp:
            messagebox.showerror("Runtime Software Error", exp.message)
        except RuntimeHardwareErrorException as exp:
            messagebox.showerror("Runtime Hardware Error", exp.message)
        self.render_path()

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

    def clear_paths(self):
        for i in self.xy_lines:
            self.xy_display.delete(i)
        for i in self.xz_lines:
            self.xz_display.delete(i)
        for i in self.yz_lines:
            self.yz_display.delete(i)
        self.root.after(1)

    def render_path(self):
        # Determine some base values
        path = self.vm.drone_path
        x_values = list(map(lambda x: x[0], path))
        y_values = list(map(lambda y: y[1], path))
        z_values = list(map(lambda z: z[2], path))
        x_min = min(x_values)
        y_min = min(y_values)
        z_min = min(z_values)
        x_max = max(x_values)
        y_max = max(y_values)
        z_max = max(z_values)
        # Create 2D paths
        xy_path = []
        xz_path = []
        yz_path = []
        for point in path:
            x_val = DroneASMInterface.__scale_placement(point[0], x_min, x_max, 0, 100)
            y_val = DroneASMInterface.__scale_placement(point[1], y_min, y_max, 0, 100)
            z_val = DroneASMInterface.__scale_placement(point[2], z_min, z_max, 0, 100)
            xy_path.append((int(x_val), int(y_val)))
            xz_path.append((int(x_val), int(z_val)))
            yz_path.append((int(y_val), int(z_val)))
        # Render 2D paths
        for i in range(len(xy_path)-1):
            obj_id = self.xy_display.create_line(xy_path[i], xy_path[i+1], width=3)
            self.xy_lines.append(obj_id)
        for i in range(len(xz_path)-1):
            obj_id = self.xz_display.create_line(xz_path[i], xz_path[i+1], width=3)
            self.xz_lines.append(obj_id)
        for i in range(len(yz_path)-1):
            obj_id = self.yz_display.create_line(yz_path[i], yz_path[i+1], width=3)
            self.yz_lines.append(obj_id)
        self.root.after(1)


    def destroy(self):
        self.root.destroy()

    @staticmethod
    def __scale_placement(place: int, abs_min: int, abs_max: int, res_min: int, res_max: int, padding: int = 10):
        if int(abs_max - abs_min) == 0:
            return (res_max + res_min)/2
        res_max -= padding
        res_min += padding
        ratio = (res_max-res_min)/(abs_max-abs_min)
        place = (place-abs_min) * ratio
        return place + res_min

def main():
    interface = DroneASMInterface()
    interface.start()


if __name__ == '__main__':
    main()
