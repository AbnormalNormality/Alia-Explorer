from tkinter import Tk, Frame, Button, Listbox, messagebox, Entry, StringVar, Toplevel, simpledialog
from AliasTkFunctions.tkfunctions import fix_resolution_issue, resize_window
from os import listdir, startfile, rename
from os.path import join, exists, ismount, isdir, isfile, dirname, basename, splitext
from platform import system
from subprocess import call
from pyperclip import copy as copy2
from filetype import guess

fix_resolution_issue()

main = Tk()
resize_window(main, 3, 2, False)
main.title("Alia Explorer")

button_frame = Frame()
button_frame.pack(side="bottom")

path = StringVar()
entry = Entry(textvariable=path)
entry.pack(side="top", fill="x", pady=(0, 5))
entry.bind("<Return>", lambda event=None: open_selected(forced=path.get()))
entry.bind("<FocusIn>", lambda event=None: entry.selection_range(0, "end"))

explorer = Listbox(main)
explorer.pack(side="top", fill="both", expand=True)
explorer.bind("<Double-Button-1>", lambda event=None: open_selected())
explorer.bind("<Button-3>", lambda event: on_right_click(event))


def on_right_click(event):
    index = explorer.nearest(event.y)
    explorer.selection_clear(0, "end")
    explorer.selection_set(index)
    explorer.focus_set()
    open_menu()


def list_drives():
    if system() == 'Windows':
        return [f"{chr(i)}:\\" for i in range(ord("A"), ord("Z") + 1) if exists(f"{chr(i)}:\\")]
    elif system() in ["Darwin", "Linux"]:
        path = "/Volumes" if exists("/Volumes") else "/media"
        return [join(path, name) for name in listdir(path) if ismount(join(path, name))]
    return []


current_dir = ""


def open_selected(forced=None, reload=False):
    global current_dir
    if not explorer.curselection() and forced is None:
        return

    if not reload:
        if forced is not None:
            forced = forced.lstrip("\"").rstrip("\"")
            if not (isdir(forced) or isfile(forced)) and forced != "":
                messagebox.showinfo("Error opening file", f"Error opening file \"{forced}\"")
                return
            selected = forced

        elif explorer.get(explorer.curselection()[0])[0] == "<":
            selected = explorer.get(explorer.curselection()[0]).split("< ")[-1]
            if selected == "Home":
                selected = ""

        else:
            selected = join(current_dir, explorer.get(explorer.curselection()[0]))

    else:
        selected = current_dir

    try:
        if selected == "":
            path.set(selected)
            explorer.delete(0, "end")
            for i in list_drives():
                explorer.insert("end", i)

        elif isdir(selected):
            current_dir = selected
            path.set(selected)
            explorer.delete(0, "end")
            if dirname(selected) != selected:
                explorer.insert("end", f"< {dirname(selected)}")
            else:
                explorer.insert("end", f"< Home")

            for i in [i for i in listdir(selected) if isdir(join(selected, i))]:
                explorer.insert("end", i)
                explorer.itemconfig("end", {"fg": "#000"})

            for i in [i for i in listdir(selected) if isfile(join(selected, i))]:
                explorer.insert("end", i)
                explorer.itemconfig("end", {"fg": "#777"})

        elif isfile(selected):
            try:
                if system() == "Windows":
                    startfile(selected)
                elif system() == "Darwin":
                    call(["open", selected])
                elif system() == "Linux":
                    call(["xdg-open", selected])
            except OSError:
                messagebox.showinfo("Error opening file", f"No application is associated with the file type "
                                                          f".{selected.split('.')[-1]}")

    except PermissionError:
        messagebox.showinfo("Error opening file", f"No permissions to open {selected}")

    open("aliaExplorer", "w").write(current_dir)


def open_menu():
    selected = explorer.get(explorer.curselection()[0])
    if selected[0] == "<":
        return

    modal = Toplevel()
    resize_window(modal, 10, 4, False)
    modal.overrideredirect(True)
    modal.bind("<FocusOut>", lambda event: modal.destroy())
    modal.focus_force()

    modal.update()
    x, y = modal.winfo_pointerxy()
    modal.geometry(f"+{x+10}+{y-5}")

    def copy_path():
        copy2(f"\"{join(current_dir, selected)}\"")
        modal.destroy()
    Button(modal, text="Copy path", command=copy_path).pack(side="top", fill="both", expand=True)

    def rename_file():
        try:
            old_name = selected.split("\\")[-1]
            if not old_name:
                return
            new_name = simpledialog.askstring("Input", "Please enter your input:", initialvalue=old_name)
            rename(join(current_dir, old_name), join(current_dir, new_name))
            open_selected(new_name, reload=True)

        except PermissionError:
            messagebox.showinfo("Error renaming file", f"No permissions to rename {selected}")

    if selected.split("\\")[-1]:
        Button(modal, text="Rename", command=rename_file).pack(side="top", fill="both", expand=True)

    if isdir(join(current_dir, selected)):
        pass

    elif isfile(join(current_dir, selected)):
        def fix_file_type():
            try:
                file_type = guess(join(current_dir, selected))

                if file_type is None or file_type.EXTENSION is None:
                    modal.destroy()
                    return

                old_name = basename(selected)
                name_without_extension = splitext(old_name)[0]

                rename(join(current_dir, old_name), join(current_dir, f"{name_without_extension}.{file_type.EXTENSION}"))
                open_selected(name_without_extension, reload=True)

                modal.destroy()

            except PermissionError:
                messagebox.showinfo("Error renaming file", f"No permissions to rename {selected}")
        Button(modal, text="Fix file type", command=fix_file_type).pack(side="top", fill="both", expand=True)


if not (exists("aliaExplorer") or isdir(open("aliaExplorer", "r").read())):
    open("aliaExplorer", "w").write("")
open_selected(open("aliaExplorer", "r").read())

Button(button_frame, text="Open", command=open_selected).pack(side="left")
main.bind("<Return>", lambda event=None: open_selected())
Button(button_frame, text="Menu", command=open_menu).pack(side="left")

main.mainloop()
