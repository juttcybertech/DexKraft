import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import sys
import shutil
import zipfile
import urllib.request
import platform
import webbrowser



# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dex Kraft")
        self.geometry("900x700")
        
        # Explorer state
        self.current_folder = None
        self.folder_history = []
        self.expanded_dirs = set()

        # Configure grid for resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkLabel(self, text="Dex Kraft", font=ctk.CTkFont(size=24, weight="bold"), text_color="#1f538d")
        self.header.grid(row=0, column=0, padx=20, pady=(20, 0))
        self.sub_header = ctk.CTkLabel(self, text="Developed by Jutt Cyber Tech", font=ctk.CTkFont(size=14, underline=True), text_color="#00ffff", cursor="hand2")
        self.sub_header.grid(row=1, column=0, padx=20, pady=(0, 10))
        self.sub_header.bind("<Button-1>", lambda e: webbrowser.open("https://juttcybertech.com/"))


        # Tabs
        self.tabview = ctk.CTkTabview(self, width=850, height=600)
        self.tabview.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_jadx = self.tabview.add("JADX (Analyze Code)")
        self.tab_apktool = self.tabview.add("Apktool (Mod & Recompile)")
        self.tab_editor = self.tabview.add("Code Editor")
        self.tab_info = self.tabview.add("System Info")
        
        self.setup_editor_tab()
        self.setup_jadx_tab()
        self.setup_apktool_tab()
        self.setup_system_info_tab()

        
        # Check JDX directory on startup
        self.check_jdx_directory()


    def check_jdx_directory(self):
        jdx_path = os.path.join(os.getcwd(), "jdx")
        if os.path.exists(jdx_path):
            files = os.listdir(jdx_path)
            if not files:
                messagebox.showinfo("JDX Directory", "The 'jdx' directory is empty.")
        else:
            # Optionally create it or just warn
            pass

    def set_exec_permission(self, path):
        """Ensure the file at path has executable permissions on non-Windows systems."""
        if os.name != 'nt' and os.path.exists(path):
            try:
                st = os.stat(path)
                os.chmod(path, st.st_mode | 0o111)
            except Exception as e:
                print(f"Warning: Could not set executable permission for {path}: {e}")

    def get_openssl_path(self):
        # 1. Check local openssl
        local_openssl = os.path.join(os.path.dirname(__file__), 'openssl', 'openssl.exe' if os.name == 'nt' else 'openssl')
        if os.path.exists(local_openssl):
            self.set_exec_permission(local_openssl)
            return local_openssl
        # 2. Check system
        import shutil
        sys_openssl = shutil.which('openssl')
        if sys_openssl:
            return sys_openssl
        return None






    def setup_editor_tab(self):
        tab = self.tab_editor
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(tab, height=40)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Open Folder", width=100, command=self.open_folder_in_editor).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="Back", width=80, fg_color="gray", command=self.go_back_in_explorer).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="Save File", width=100, fg_color="green", command=self.save_current_file).pack(side="left", padx=5)
        self.current_file_label = ctk.CTkLabel(toolbar, text="No file selected")
        self.current_file_label.pack(side="left", padx=20)

        # File Explorer (Left)
        self.file_tree_frame = ctk.CTkScrollableFrame(tab, width=250, label_text="Project Files")
        self.file_tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Editor (Right)
        self.editor_text = ctk.CTkTextbox(tab, font=("Consolas", 14), wrap="none")
        self.editor_text.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.current_editor_file_path = None

    def open_folder_in_editor(self, folder_path=None):
        if not folder_path:
            folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        # Track navigation history
        if self.current_folder and self.current_folder != folder_path:
            self.folder_history.append(self.current_folder)
        self.current_folder = folder_path
        # Clear existing
        for widget in self.file_tree_frame.winfo_children():
            widget.destroy()
        self.tabview.set("Code Editor")
        self.populate_tree(folder_path)

    def go_back_in_explorer(self):
        if self.folder_history:
            prev_folder = self.folder_history.pop()
            self.current_folder = prev_folder
            self.populate_tree(prev_folder)

    def populate_tree(self, folder_path):
        # Expand/collapse logic for file explorer
        def add_items(path, indent=0):
            try:
                items = sorted(os.listdir(path))
            except Exception:
                return
            for item in items:
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                pad = "    " * indent
                if is_dir:
                    expanded = full_path in self.expanded_dirs
                    btn_text = f"{pad}{'[-]' if expanded else '[+]'} {item}"
                    btn = ctk.CTkButton(
                        self.file_tree_frame,
                        text=btn_text,
                        anchor="w",
                        fg_color="transparent",
                        text_color=("black", "white"),
                        height=24,
                        command=lambda p=full_path: self.toggle_dir_expand(p, folder_path)
                    )
                    btn.pack(fill="x")
                    if expanded:
                        add_items(full_path, indent + 1)
                else:
                    file_btn = ctk.CTkButton(
                        self.file_tree_frame,
                        text=f"{pad}    📄 {item}",
                        anchor="w",
                        fg_color="transparent",
                        height=20,
                        command=lambda p=full_path: self.load_file(p)
                    )
                    file_btn.pack(fill="x")

        # Clear existing
        for widget in self.file_tree_frame.winfo_children():
            widget.destroy()
        self.expanded_dirs.add(folder_path)  # Always expand root
        add_items(folder_path, indent=0)

    def toggle_dir_expand(self, dir_path, root_path):
        if dir_path in self.expanded_dirs:
            self.expanded_dirs.remove(dir_path)
        else:
            self.expanded_dirs.add(dir_path)
        self.populate_tree(root_path)

    def on_file_click(self, path):
        if os.path.isdir(path):
            pass # Expand?
        else:
            self.load_file(path)

    def load_file(self, path):
        self.current_editor_file_path = path
        self.current_file_label.configure(text=os.path.basename(path))

        # Handle files that need JADX decompilation (.dex, .jar, .class, .kotlin_module, .kotlin_metadata, .kotlin, .kotlin_builtins)
        jadx_extensions = ('.dex', '.jar', '.class', '.kotlin_module', '.kotlin_metadata', '.kotlin', '.kotlin_builtins')


        if path.lower().endswith(jadx_extensions):
            self.editor_text.delete("0.0", "end")
            self.editor_text.insert("0.0", f"Processing {os.path.splitext(path)[1].upper()} file with JADX (Kotlin-aware), please wait...\n")

            import threading
            dex_dir = os.path.dirname(path)
            dex_name = os.path.splitext(os.path.basename(path))[0]
            jadx_out = os.path.join(dex_dir, f"{dex_name}_jadx_out")
            os.makedirs(jadx_out, exist_ok=True)
            jadx = self.find_tool("jadx", os.path.join("jadx", "bin", "jadx.bat" if os.name == 'nt' else "jadx"))
            if not jadx:
                messagebox.showerror("Error", "JADX not found. Please restart the app to run the dependency setup.")
                return

            def run_jadx_task():
                self.set_exec_permission(jadx)
                self.editor_text.insert("end", f"\nDecompiling {os.path.splitext(path)[1].upper()} with JADX...\nOutput: {jadx_out}\n")
                # Kotlin-aware flags: --deobf-parse-kotlin-metadata and --use-kotlin-methods-for-var-names apply
                cmd = [jadx, '-d', jadx_out, '--show-bad-code', '--deobf', '--deobf-parse-kotlin-metadata', '--use-kotlin-methods-for-var-names', 'apply', path]
                try:
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                    for line in p.stdout:
                        self.editor_text.insert("end", line)
                    p.wait()
                except Exception as e:
                    self.editor_text.insert("end", f"\nError: {e}\n")
                    return
                # Open in Code Editor (show decompiled sources)
                src_dir = os.path.join(jadx_out, "sources")
                if os.path.exists(src_dir):
                    self.after(0, lambda: self.open_folder_in_editor(src_dir))
                else:
                    self.editor_text.insert("end", "\nJADX did not produce sources. Falling back to binary strings view...\n")
                    self.after(500, lambda: self.show_binary_view(path))

            threading.Thread(target=run_jadx_task, daemon=True).start()
            return

        # Handle .rsa file: show certificate info
        if path.lower().endswith('.rsa'):
            self.editor_text.delete("0.0", "end")
            self.editor_text.insert("0.0", "Processing .RSA file, please wait...\n")
            import threading
            def show_rsa_info():
                import shutil
                import subprocess
                
                # Try Keytool first (usually part of JDK/JRE)
                keytool_path = shutil.which('keytool')
                if keytool_path:
                    try:
                        cmd = [keytool_path, "-printcert", "-file", path]
                        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                             creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                        out, err = p.communicate()
                        if out:
                            self.editor_text.delete("0.0", "end")
                            self.editor_text.insert("0.0", f"[Keytool Certificate Info]\n{out}")
                            return
                    except Exception:
                        pass

                # Try OpenSSL as fallback
                openssl_path = self.get_openssl_path()
                if openssl_path:
                    try:
                        cmd = [openssl_path, "pkcs7", "-inform", "DER", "-print_certs", "-in", path]
                        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                             creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                        out, err = p.communicate()
                        if out:
                            self.editor_text.delete("0.0", "end")
                            self.editor_text.insert("0.0", f"[OpenSSL Certificate Info]\n{out}")
                            return
                        elif err:
                            self.editor_text.delete("0.0", "end")
                            self.editor_text.insert("0.0", f"[OpenSSL error]\n{err}")
                            return
                    except Exception as e:
                        pass
                
                # Error: Neither found
                self.editor_text.delete("0.0", "end")
                self.editor_text.insert("0.0", "Error: Neither 'keytool' (Java) nor 'openssl' were found on your system to process this .RSA file.\n\nPlease ensure Java is installed or provide OpenSSL.")

            threading.Thread(target=show_rsa_info, daemon=True).start()
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor_text.delete("0.0", "end")
            self.editor_text.insert("0.0", content)
        except UnicodeDecodeError:
            self.show_binary_view(path)

        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")

    def show_binary_view(self, path):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            # Extract printable strings (min 4 chars) - using a more inclusive regex for metadata
            import re
            # Use a wider range of characters for metadata detection
            printable_strings = re.findall(rb'[\w\.\$/<>-]{4,}', data)

            strings_view = ""
            if printable_strings:
                # Filter and decode
                decoded_strings = []
                for s in printable_strings:
                    try:
                        decoded_strings.append(s.decode('ascii'))
                    except:
                        continue
                if decoded_strings:
                    strings_view = "[Strings Extraction]\n" + "\n".join(decoded_strings) + "\n\n"

            import binascii
            hexstr = binascii.hexlify(data).decode('ascii')
            lines = [hexstr[i:i+32] for i in range(0, len(hexstr), 32)]
            hexview = "[Binary file preview - hex]\n" + '\n'.join(lines)
            
            self.editor_text.delete("0.0", "end")
            self.editor_text.insert("0.0", f"{strings_view}{hexview}")
        except Exception as e:
            self.editor_text.delete("0.0", "end")
            self.editor_text.insert("0.0", f"[Error reading binary: {e}]")

    def save_current_file(self):
        if not self.current_editor_file_path: return
        
        content = self.editor_text.get("0.0", "end-1c") # -1c to remove extra newline
        try:
            with open(self.current_editor_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Saved", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    def setup_jadx_tab(self):
        tab = self.tab_jadx
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(3, weight=1) # Log expands

        # APK/DEX/JAR Selection
        ctk.CTkLabel(tab, text="APK/DEX/JAR File:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.jadx_apk_entry = ctk.CTkEntry(tab, placeholder_text="Select APK to analyze")
        self.jadx_apk_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        file_types = [("Android Files", "*.apk *.dex *.jar *.class"), ("All Files", "*.*")]
        ctk.CTkButton(tab, text="Browse", command=lambda: self.browse_file(self.jadx_apk_entry, file_types)).grid(row=0, column=2, padx=10)

        # Output
        ctk.CTkLabel(tab, text="Output:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.jadx_out_entry = ctk.CTkEntry(tab, placeholder_text="Output folder")
        self.jadx_out_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(tab, text="Browse", command=lambda: self.browse_dir(self.jadx_out_entry)).grid(row=1, column=2, padx=10)

        # Decompile Button
        self.jadx_btn = ctk.CTkButton(tab, text="Decompile to Java", fg_color="green", command=self.run_jadx)
        self.jadx_btn.grid(row=2, column=0, columnspan=3, pady=20)

        # Log
        self.jadx_log = ctk.CTkTextbox(tab, height=300, font=("Consolas", 12))
        self.jadx_log.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def setup_apktool_tab(self):
        tab = self.tab_apktool
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(3, weight=1) # Log expands

        # === DECOMPILE SECTION ===
        frame_dec = ctk.CTkFrame(tab)
        frame_dec.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        frame_dec.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_dec, text="1. Decompile (Apktool)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.mod_apk_entry = ctk.CTkEntry(frame_dec, placeholder_text="APK to Mod")
        self.mod_apk_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(frame_dec, text="Browse APK", command=lambda: self.browse_file(self.mod_apk_entry)).grid(row=1, column=2, padx=10)
        
        self.mod_out_entry = ctk.CTkEntry(frame_dec, placeholder_text="Project Folder (Output)")
        self.mod_out_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(frame_dec, text="Select Folder", command=lambda: self.browse_dir(self.mod_out_entry)).grid(row=2, column=2, padx=10)

        ctk.CTkButton(frame_dec, text="Decompile Resources", command=self.run_apktool_d).grid(row=3, column=0, columnspan=3, pady=10)

        # === COMPILE SECTION ===
        frame_com = ctk.CTkFrame(tab)
        frame_com.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        frame_com.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_com, text="2. Recompile & Sign", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ctk.CTkButton(frame_com, text="Build APK", fg_color="orange", command=self.run_apktool_b).grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Log
        self.mod_log = ctk.CTkTextbox(tab, height=200, font=("Consolas", 12))
        self.mod_log.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    # --- Dependencies Logic ---
    def check_dependencies(self):
        missing = []
        # Check JADX
        jadx_rel = os.path.join("jadx", "bin", "jadx.bat" if os.name == 'nt' else "jadx")
        jadx_path = os.path.join(os.path.dirname(__file__), jadx_rel)
        if not os.path.exists(jadx_path):
            missing.append("JADX")
        # Check Apktool
        apktool_rel = os.path.join("apktool", "apktool.bat" if os.name == 'nt' else "apktool")
        apktool_path = os.path.join(os.path.dirname(__file__), apktool_rel)
        apktool_jar = os.path.join(os.path.dirname(__file__), "apktool", "apktool.jar")
        if not os.path.exists(apktool_path) or not os.path.exists(apktool_jar):
            missing.append("Apktool")

        if missing:
            msg = f"The following dependencies are missing:\n{', '.join(missing)}\n\nThey will be downloaded and set up automatically."
            messagebox.showinfo("Missing Dependencies", msg)
            auto_setup = [m for m in missing if m in ("JADX", "Apktool")]
            if auto_setup:
                self.start_dependency_setup(auto_setup)


    def start_dependency_setup(self, missing_items):
        # Create a progress window
        self.setup_window = ctk.CTkToplevel(self)
        self.setup_window.title("Setting up Dependencies")
        self.setup_window.geometry("400x150")
        self.setup_window.transient(self) # Keep on top
        
        self.setup_label = ctk.CTkLabel(self.setup_window, text="Initializing setup...")
        self.setup_label.pack(pady=20)
        
        self.setup_progress = ctk.CTkProgressBar(self.setup_window)
        self.setup_progress.pack(pady=10, padx=20)
        self.setup_progress.set(0)
        
        threading.Thread(target=self.run_setup_process, args=(missing_items,), daemon=True).start()

    def run_setup_process(self, missing_items):
        try:
            base_dir = os.path.dirname(__file__)
            
            if "JADX" in missing_items:
                self.update_setup_status("Downloading JADX...")
                jadx_url = "https://github.com/skylot/jadx/releases/download/v1.4.7/jadx-1.4.7.zip"
                jadx_dir = os.path.join(base_dir, "jadx")
                zip_path = os.path.join(base_dir, "jadx.zip")
                
                self.download_file(jadx_url, zip_path)
                
                self.update_setup_status("Extracting JADX...")
                os.makedirs(jadx_dir, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(jadx_dir)
                
                os.remove(zip_path) # Cleanup
                
            if "Apktool" in missing_items:
                self.update_setup_status("Downloading Apktool...")
                apktool_dir = os.path.join(base_dir, "apktool")
                os.makedirs(apktool_dir, exist_ok=True)
                
                # JAR
                jar_url = "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar"
                jar_path = os.path.join(apktool_dir, "apktool.jar")
                self.download_file(jar_url, jar_path)
                
                # Wrapper
                if os.name == 'nt':
                    wrapper_url = "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/windows/apktool.bat"
                    wrapper_path = os.path.join(apktool_dir, "apktool.bat")
                else:
                    wrapper_url = "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool"
                    wrapper_path = os.path.join(apktool_dir, "apktool")
                
                self.download_file(wrapper_url, wrapper_path)
                self.set_exec_permission(wrapper_path)
            
            self.update_setup_status("Setup Complete!")
            self.setup_window.after(1000, self.setup_window.destroy)
            messagebox.showinfo("Success", "Dependencies installed successfully.")
            
        except Exception as e:
            self.update_setup_status(f"Error: {e}")
            messagebox.showerror("Setup Error", f"Failed to setup dependencies: {e}")
            self.setup_window.after(0, self.setup_window.destroy)

    def download_file(self, url, dest):
        with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
            total_size = int(response.getheader('Content-Length', 0))
            block_size = 8192
            count = 0
            while True:
                data = response.read(block_size)
                if not data: break
                out_file.write(data)
                count += len(data)
                if total_size > 0:
                    percent = count / total_size
                    # Update progress bar in main thread
                    self.after(0, lambda p=percent: self.setup_progress.set(p))

    def update_setup_status(self, text):
        self.after(0, lambda: self.setup_label.configure(text=text))

    # --- Utilities ---
    def browse_file(self, entry, file_types=None):
        if not file_types:
            file_types = [("APK", "*.apk")]
        f = filedialog.askopenfilename(filetypes=file_types)
        if f: 
            entry.delete(0, "end")
            entry.insert(0, f)
            # Auto fill output if empty
            if entry == self.jadx_apk_entry:
                self.auto_fill_out(f, self.jadx_out_entry, "_src")
            elif entry == self.mod_apk_entry:
                self.auto_fill_out(f, self.mod_out_entry, "_mod")

    def auto_fill_out(self, apk_path, out_entry, suffix):
        d = os.path.splitext(apk_path)[0] + suffix
        out_entry.delete(0, "end")
        out_entry.insert(0, d)

    def browse_dir(self, entry):
        d = filedialog.askdirectory()
        if d:
            entry.delete(0, "end")
            entry.insert(0, d)

    def log(self, textbox, msg):
        textbox.configure(state="normal")
        textbox.insert("end", msg + "\n")
        textbox.see("end")
        textbox.configure(state="disabled")

    # --- JADX Logic ---
    def run_jadx(self):
        apk = self.jadx_apk_entry.get()
        out = self.jadx_out_entry.get()
        if not apk or not out:
            return

        def task():
            self.log(self.jadx_log, "Checking JADX...")
            jadx = self.find_tool("jadx", os.path.join("jadx", "bin", "jadx.bat" if os.name == 'nt' else "jadx"))
            if not jadx:
                self.log(self.jadx_log, "ERROR: JADX not found. Please restart app to run setup.")
                return
            
            self.set_exec_permission(jadx)

            # Kotlin-aware flags: --deobf-parse-kotlin-metadata and --use-kotlin-methods-for-var-names apply
            cmd = [jadx, '-d', out, '--show-bad-code', '--deobf', '--deobf-parse-kotlin-metadata', '--use-kotlin-methods-for-var-names', 'apply', apk]
            self.run_subprocess(cmd, self.jadx_log)
            # After decompilation, open the full output folder in the Code Editor
            if os.path.exists(out):
                self.log(self.jadx_log, "Opening decompiled source folder in editor...")
                self.after(0, lambda: [self.tabview.set("Code Editor"), self.open_folder_in_editor(out)])
            else:
                self.log(self.jadx_log, "Decompilation failed or output folder not found.")

        threading.Thread(target=task, daemon=True).start()

    # --- Apktool Logic ---
    def run_apktool_d(self):
        apk = self.mod_apk_entry.get()
        out = self.mod_out_entry.get()
        if not apk or not out: return

        def task():
            self.log(self.mod_log, "Checking Apktool...")
            tool = self.find_tool("apktool", os.path.join("apktool", "apktool.bat" if os.name == 'nt' else "apktool"))
            if not tool:
                self.log(self.mod_log, "ERROR: Apktool not found. Please restart app to run setup.")
                return
            
            self.set_exec_permission(tool)
            
            # apktool d <apk> -o <out> -f
            cmd = [tool, 'd', apk, '-o', out, '-f']
            self.run_subprocess(cmd, self.mod_log)
            self.log(self.mod_log, "Decompilation Done. Opening Editor...")
            self.after(0, lambda: self.open_folder_in_editor(out))

        threading.Thread(target=task, daemon=True).start()

    def run_apktool_b(self):
        # Build from the Project Folder
        folder = self.mod_out_entry.get()
        if not folder: return

        def task():
            tool = self.find_tool("apktool", os.path.join("apktool", "apktool.bat" if os.name == 'nt' else "apktool"))
            if not tool: return
            
            self.set_exec_permission(tool)
            
            # apktool b <folder> -o <folder>/dist/modded.apk
            # usually apktool b <folder> output goes to <folder>/dist/
            self.log(self.mod_log, f"Building APK from {folder}...")
            cmd = [tool, 'b', folder]
            self.run_subprocess(cmd, self.mod_log)
            
            dist_path = os.path.join(folder, "dist")
            if os.path.exists(dist_path):
                 self.log(self.mod_log, f"Build Success! Output in: {dist_path}")
                 try:
                     if os.name == 'nt':
                         os.startfile(dist_path)
                     elif platform.system() == 'Darwin':
                         subprocess.run(['open', dist_path])
                     else:
                         subprocess.run(['xdg-open', dist_path])
                 except Exception:
                     pass
            else:
                 self.log(self.mod_log, "Build failed. Check errors above.")

        threading.Thread(target=task, daemon=True).start()

    # --- Helpers ---
    def find_tool(self, name, local_rel):
        # 1. Local
        local = os.path.abspath(os.path.join(os.path.dirname(__file__), local_rel))
        if os.path.exists(local): return local
        # 2. Path
        return shutil.which(name)

    def run_subprocess(self, cmd, log_widget):
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            output_lines = []
            for line in p.stdout:
                output_lines.append(line.rstrip())
                self.log(log_widget, line.rstrip())
            p.wait()
            # After process, check for common JADX warnings/errors
            output_text = '\n'.join(output_lines)
            if 'WARN' in output_text or 'ERROR' in output_text or 'skipped' in output_text:
                self.log(log_widget, '\n[!] Some classes/resources may have been skipped or failed to decompile. Please review the log above for details.\n')
        except Exception as e:
            self.log(log_widget, f"Error: {e}")

    def setup_system_info_tab(self):
        tab = self.tab_info
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        info_text = ctk.CTkTextbox(tab, font=("Consolas", 14))
        info_text.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Gather system info
        details = [
            ("Application Name", "Dex Kraft"),
            ("Developer", "Jutt Cyber Tech"),
            ("Website", "https://juttcybertech.com/"),
            ("", ""), # Spacer
            ("Operating System", platform.system()),
            ("OS Release", platform.release()),
            ("OS Version", platform.version()),
            ("Machine", platform.machine()),
            ("Processor", platform.processor()),
            ("", ""), # Spacer
            ("Python Version", sys.version),
            ("Executable", sys.executable),
            ("Current Directory", os.getcwd())
        ]

        display_str = "SYSTEM INFORMATION\n" + "="*50 + "\n\n"
        for label, value in details:
            if label:
                display_str += f"{label:<20}: {value}\n"
            else:
                display_str += "\n"

        info_text.insert("0.0", display_str)
        info_text.configure(state="disabled") # Read-only

if __name__ == "__main__":
    app = App()
    app.after(100, app.check_dependencies) # Run check shortly after startup
    app.mainloop()
