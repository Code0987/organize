import os
import re
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import yaml
from organize import Config
from organize.find_config import find_config, create_example_config, EXAMPLE_CONFIG
from organize.output import Default
import threading


class OrganizeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Organize - File Management Automation")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        self.config_path = None
        self.current_config = ""
        self._highlight_timer = None

        self.create_widgets()
        self.load_default_config()

    def create_widgets(self):
        # Main paned window
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left sidebar for navigation
        sidebar = ttk.Frame(main_pane, width=250)
        main_pane.add(sidebar, weight=1)

        # Config section
        config_frame = ttk.Labelframe(sidebar, text="Configuration", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(config_frame, text="New Config", command=self.new_config).pack(fill=tk.X, pady=2)
        ttk.Button(config_frame, text="Load Config", command=self.load_config).pack(fill=tk.X, pady=2)
        ttk.Button(config_frame, text="Save Config", command=self.save_config).pack(fill=tk.X, pady=2)
        ttk.Button(config_frame, text="Check Config", command=self.check_config).pack(fill=tk.X, pady=2)

        self.working_dir_var = tk.StringVar(value=str(Path.home()))
        ttk.Label(config_frame, text="Working Dir:").pack(anchor=tk.W)
        dir_frame = ttk.Frame(config_frame)
        dir_frame.pack(fill=tk.X)
        ttk.Entry(dir_frame, textvariable=self.working_dir_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.browse_working_dir).pack(side=tk.RIGHT)

        # Run controls
        run_frame = ttk.Labelframe(sidebar, text="Actions", padding=10)
        run_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(run_frame, text="Simulate", command=self.run_simulate).pack(fill=tk.X, pady=2)
        ttk.Button(run_frame, text="Run", command=self.run_organize).pack(fill=tk.X, pady=2)

        # Main area: editor and output
        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=4)

        # Config editor
        editor_frame = ttk.Labelframe(right_pane, text="Config Editor (YAML)", padding=10)
        right_pane.add(editor_frame, weight=3)

        self.editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, font=("Consolas", 10), undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True)
        # YAML syntax tags
        self.editor.tag_configure("key", foreground="blue")
        self.editor.tag_configure("string", foreground="green")
        self.editor.tag_configure("comment", foreground="gray")
        self.editor.tag_configure("number", foreground="purple")
        self.editor.bind("<KeyRelease>", self._debounce_highlight)

        # Output console
        output_frame = ttk.Labelframe(right_pane, text="Output", padding=10)
        right_pane.add(output_frame, weight=2)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Consolas", 9))
        self.output_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Log save controls
        log_controls = ttk.Frame(output_frame)
        log_controls.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(log_controls, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        self.auto_save_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(log_controls, text="Auto-save logs after run", variable=self.auto_save_var).pack(side=tk.LEFT)

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_config)
        file_menu.add_command(label="Open...", command=self.load_config)
        file_menu.add_command(label="Save", command=self.save_config)
        file_menu.add_command(label="Save As...", command=self.save_as_config)
        file_menu.add_command(label="Save Logs...", command=self.save_logs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Simulate", command=self.run_simulate)
        tools_menu.add_command(label="Run", command=self.run_organize)
        tools_menu.add_command(label="Check Config", command=self.check_config)
        tools_menu.add_command(label="Show Docs", command=self.show_docs)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def log(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def highlight_yaml(self):
        # Basic YAML syntax highlighting using tags
        self.editor.tag_remove("key", "1.0", "end")
        self.editor.tag_remove("string", "1.0", "end")
        self.editor.tag_remove("comment", "1.0", "end")
        self.editor.tag_remove("number", "1.0", "end")
        text = self.editor.get("1.0", "end")
        # Keys (before :)
        for match in re.finditer(r"^(\s*)(\w+):", text, re.MULTILINE):
            start = self.editor.index(f"1.0 + {match.start(2)} chars")
            end = self.editor.index(f"1.0 + {match.end(2)} chars")
            self.editor.tag_add("key", start, end)
        # Strings
        for match in re.finditer(r'["\']([^"\']*)["\']', text):
            start = self.editor.index(f"1.0 + {match.start(1)} chars")
            end = self.editor.index(f"1.0 + {match.end(1)} chars")
            self.editor.tag_add("string", start, end)
        # Comments
        for match in re.finditer(r"#.*$", text, re.MULTILINE):
            start = self.editor.index(f"1.0 + {match.start()} chars")
            end = self.editor.index(f"1.0 + {match.end()} chars")
            self.editor.tag_add("comment", start, end)
        # Numbers
        for match in re.finditer(r":\s*(\d+)", text):
            start = self.editor.index(f"1.0 + {match.start(1)} chars")
            end = self.editor.index(f"1.0 + {match.end(1)} chars")
            self.editor.tag_add("number", start, end)

    def _debounce_highlight(self, event=None):
        if hasattr(self, "_highlight_timer") and self._highlight_timer is not None:
            self.root.after_cancel(self._highlight_timer)
        self._highlight_timer = self.root.after(300, self.highlight_yaml)

    def load_default_config(self):
        try:
            config_path = find_config()
            self.config_path = config_path
            with open(config_path, "r", encoding="utf-8") as f:
                self.current_config = f.read()
            self.editor.delete(1.0, tk.END)
            self.editor.insert(tk.END, self.current_config)
            self.highlight_yaml()
            self.log(f"Loaded default config from: {config_path}")
        except Exception:
            # Create example if no config
            self.current_config = EXAMPLE_CONFIG
            self.editor.delete(1.0, tk.END)
            self.editor.insert(tk.END, self.current_config)
            self.highlight_yaml()
            self.log("No default config found, loaded example.")

    def new_config(self):
        self.config_path = None
        self.current_config = EXAMPLE_CONFIG
        self.editor.delete(1.0, tk.END)
        self.editor.insert(tk.END, self.current_config)
        self.highlight_yaml()
        self.clear_output()
        self.log("New configuration created.")

    def load_config(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.current_config = f.read()
                self.editor.delete(1.0, tk.END)
                self.editor.insert(tk.END, self.current_config)
                self.config_path = Path(file_path)
                self.highlight_yaml()
                self.log(f"Loaded config from: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        if not self.config_path:
            self.save_as_config()
            return
        try:
            self.current_config = self.editor.get(1.0, tk.END).strip()
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(self.current_config)
            self.log(f"Saved config to: {self.config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def save_as_config(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.current_config = self.editor.get(1.0, tk.END).strip()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.current_config)
                self.config_path = Path(file_path)
                self.highlight_yaml()
                self.log(f"Saved config as: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save config: {e}")

    def check_config(self):
        self.clear_output()
        self.log("Checking configuration...")
        try:
            config_text = self.editor.get(1.0, tk.END).strip()
            Config.from_string(config_text)
            self.log("Configuration is valid!")
            messagebox.showinfo("Success", "Configuration is valid.")
        except Exception as e:
            self.log(f"Config error: {e}")
            messagebox.showerror("Config Error", str(e))

    def save_logs(self):
        if not self.output_text.get(1.0, tk.END).strip():
            messagebox.showinfo("Info", "No logs to save.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.output_text.get(1.0, tk.END))
                self.log(f"Logs saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")

    def _auto_save_logs(self):
        # Auto-save with timestamped filename in current working dir
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        auto_path = Path(self.working_dir_var.get()) / f"organize_logs_{timestamp}.log"
        try:
            with open(auto_path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get(1.0, tk.END))
            self.log(f"Auto-saved logs to: {auto_path}")
        except Exception as e:
            self.log(f"Auto-save failed: {e}")

    def browse_working_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.working_dir_var.set(dir_path)
            config_file = Path(dir_path) / "config.yaml"
            if config_file.is_file():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        self.current_config = f.read()
                    self.editor.delete(1.0, tk.END)
                    self.editor.insert(tk.END, self.current_config)
                    self.config_path = config_file
                    self.highlight_yaml()
                    self.log(f"Auto-loaded config from working dir: {config_file}")
                except Exception as e:
                    self.log(f"Failed to auto-load config: {e}")

    def run_simulate(self):
        self.run_organize_command(simulate=True)

    def run_organize(self):
        if messagebox.askyesno("Confirm", "Run organize? This will modify files. Continue?"):
            self.run_organize_command(simulate=False)

    def run_organize_command(self, simulate=True):
        self.clear_output()
        self.log(f"Starting {'simulation' if simulate else 'organize run'}...")
        self.save_config()  # auto save before run

        def run_thread():
            try:
                config_text = self.editor.get(1.0, tk.END).strip()
                config = Config.from_string(config_text, self.config_path)
                working_dir = self.working_dir_var.get()

                # Use Default output but redirect prints? For GUI, capture via custom or subprocess for simplicity
                # For now, use subprocess to leverage full CLI output
                cmd = ["organize", "sim" if simulate else "run", "--format", "default"]
                if self.config_path:
                    cmd.append(str(self.config_path))
                if working_dir:
                    cmd.extend(["--working-dir", working_dir])

                # Run as subprocess to get output
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=working_dir
                )
                for line in process.stdout:
                    self.root.after(0, self.log, line.strip())
                process.wait()
                complete_msg = f"{'Simulation' if simulate else 'Run'} completed with return code: {process.returncode}"
                self.root.after(0, self.log, complete_msg)
                if self.auto_save_var.get():
                    self.root.after(0, self._auto_save_logs)
            except Exception as e:
                self.root.after(0, self.log, f"Error: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=run_thread, daemon=True).start()

    def show_docs(self):
        try:
            subprocess.Popen(["organize", "docs"])
            self.log("Opened documentation.")
        except Exception as e:
            self.log(f"Failed to open docs: {e}")

    def show_about(self):
        about_text = """Organize GUI Desktop App
Version: 1.0
A user-friendly desktop interface for the organize CLI tool.

Features:
- YAML config editing
- Simulate and run organization rules
- Log saving (manual + auto after runs)
- Cross-platform support (Windows, macOS, Linux)
- Custom settings and preferences

Core functionalities implemented:
- Rule management via config
- Filters and actions from CLI
- Simulation and execution
"""
        messagebox.showinfo("About", about_text)


def main():
    root = tk.Tk()
    app = OrganizeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
