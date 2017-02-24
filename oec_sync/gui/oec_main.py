from tkinter import *
from tkinter.ttk import *
import dialog as dlg
from interface import *
from syncutil import SrcPath
import threading
import logging
from random import randint
from tkinter import messagebox
import tempfile
from subprocess import call
from typing import List
import webbrowser
import os

EDITOR = os.environ.get('EDITOR', 'vim') \
    if os.name == 'posix' \
    else ''

# TODO Missing major documentation. Please fix


def grid(widget, sticky=W+E+N+S, **kw):
    """
    Calls grid manager with our default style parameters.
    """
    widget.grid(sticky=sticky, **kw)
    return widget

FOCUS = 0, ""


class AppStyle(Style):
    def __init__(self, parent="clam"):
        super().__init__()
        # self.theme_use(parent)
        style_dict = {
            "padding": 3,
            "foreground": "#002e4d",
            "background": "#eeeef0",
            "fieldbackground": "#eeeef0",
            "selectbackground": "#002e4d",
            "highlightcolor": "#6a86b4",
            "lightcolor": "#eeeef0",
            "darkcolor": "#002e4d",
            "relief": "#6a86b4",
        }

        self.configure(".", **style_dict, font=('Helvetica', 10))
        # self.configure("TLabel", foreground="black", background="?")
        # self.configure("TButton", foreground="?", background="?")
        # self.configure("TCheckbutton", foreground="?", background="?")
        # self.configure("TCombobox", foreground="?", background="?")
        # self.configure("TEntry", foreground="?", background="?")
        # self.configure("TFrame", foreground="?", background="?")
        # self.configure("TLabel", foreground="?", background="?")
        # self.configure("TLabelFrame", foreground="?", background="?")
        # self.configure("TMenubutton", foreground="?", background="?")
        # self.configure("TNotebook", foreground="?", background="?")
        # self.configure("TPanedwindow", foreground="?", background="?")
        # self.configure("Horizontal.TProgressbar", foreground="?", background="?")
        # self.configure("Vertical.TProgressbar", foreground="?", background="?")
        # self.configure("TRadiobutton", foreground="?", background="?")
        # self.configure("Horizontal.TScale", foreground="?", background="?")
        # self.configure("Vertical.TScale", foreground="?", background="?")
        # self.configure("Horizontal.TScrollbar", foreground="?", background="?")
        # self.configure("Vertical.TScrollbar", foreground="?", background="?")
        # self.configure("TSeparator", foreground="?", background="?")
        # self.configure("TSizegrip", foreground="?", background="?")
        self.configure("Treeview", **style_dict,
                       rowheight=25,
                       ipadx=1, ipady=1, padx=1, pady=1)


class ConsoleView(Frame):
    def __init__(self, master: Widget):
        Frame.__init__(self, master)
        self.grid()


class VertHoriScrolledTree(Frame):
    def __init__(self, master: Widget, name):
        Frame.__init__(self, master)
        # Frames
        vert_scroll_tree = Scrollbar(self, orient=VERTICAL)
        hori_scroll_tree = Scrollbar(self, orient=HORIZONTAL)
        tree = Treeview(self, yscrollcommand=vert_scroll_tree.set,
                        xscrollcommand=hori_scroll_tree.set)
        vert_scroll_tree.configure(command=tree.yview)
        hori_scroll_tree.configure(command=tree.xview)
        vert_scroll_tree.pack(fill=Y, side=RIGHT, expand=FALSE)
        hori_scroll_tree.pack(fill=X, side=BOTTOM, expand=FALSE)
        tree.xview_moveto(0)
        tree.yview_moveto(0)

        column_options = {
            "minwidth": 50,
            "width": 60,
        }
        tree["columns"] = ("Value", "Error", "IsLimit", "Unit")
        tree.column("Value", **column_options)
        tree.column("Error", **column_options)
        tree.column("IsLimit", **column_options)
        tree.column("Unit", **column_options)
        tree.heading("#0", text="Planets")
        tree.heading("Value", text="Value")
        tree.heading("Error", text="Error")
        tree.heading("IsLimit", text="IsLimit")
        tree.heading("Unit", text="Unit")
        tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        self.interior = tree
        self.name = name


class WaitFrame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        path_gears = SrcPath.abs("gui", "gears.gif")
        gears_image = PhotoImage(file=path_gears)
        gears_label = Label(self, image=gears_image)
        gears_label.image = gears_image  # don't remove this line!
        gears_label.place(relx=0.5, rely=0.5, anchor=CENTER)


class VerticalScrolledTree(Frame):
    def __init__(self, master: "OECSyncApp", type):
        Frame.__init__(self, master)
        # All the system updates as treeview
        vert_scroll_tree = Scrollbar(self, orient=VERTICAL)
        tree = Treeview(self, yscrollcommand=vert_scroll_tree.set)
        vert_scroll_tree.configure(command=tree.yview)
        vert_scroll_tree.pack(fill=Y, side=RIGHT, expand=FALSE)
        tree.xview_moveto(0)
        tree.yview_moveto(0)
        tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        tree.heading("#0", text='Systems')
        tree.bind("<Button-1>", self.on_selected)
        self.interior = tree
        self.master = master
        self.frames = {}
        self.type = type if type in ["remote", "local"] else "remote"
        self.fitem = None
        self.last_frame = None
        self.cur_frame = None

    def populate(self, requests: [str]):
        if requests and len(requests) > 0:
            i = 0
            for request_name in requests:
                self.interior.insert("", i, text=request_name)
                i += 1

    def create_frame(self, system: PlanetarySysUpdate):
        frame = VertHoriScrolledTree(self.master, system.name)
        self.last_frame.destroy() if self.last_frame is not None else None
        for j, planet in enumerate(system.planets):
            identity = frame.interior.insert("", 0, planet.name,
                                             text=planet.name, open=True)

            for field, value in planet.fields.items():
                frame.interior.insert(identity, "end",
                                      planet.name + field, text=field,
                                      values=(value.value, value.error,
                                              value.is_limit, value.unit))
        frame.grid(row=2, column=0, columnspan=3, rowspan=4, sticky="nsew")
        frame.tkraise()
        self.last_frame = frame
        return frame

    def on_selected(self, event):
        # fetch this object from the object list
        item = self.interior.identify("item", event.x, event.y)
        req_name = self.interior.item(item)["text"]
        self.on_req_selected(req_name)

    def on_req_selected(self, req_name):
        id_, req, type_ = Interface.find_system(req_name)
        self.create_frame(req.updates)

        mainview = self.master.vw

        def set_message(*ignored):
            req.message = mainview.vw_message.var.get()
            # print(req.message)

        def set_title(*ignored):
            req.title = mainview.vw_message_title.var.get()
            # print(req.title)

        mainview.vw_message.var.set(req.message)
        mainview.vw_message.set_observer(set_message)

        mainview.vw_message_title.var.set(req.title)
        mainview.vw_message_title.set_observer(set_title)

        global FOCUS
        FOCUS = id_, type_

    def delete_frame(self, id):
        # remove from dictionary of frame and list of systems
        sys_name = Interface.get_system_from_index(id)
        Interface.delete_system_at_index(id)


class RequestHistoryView(Frame):
    """

    """
    def __init__(self, master: Tk):
        Frame.__init__(self, master)
        grid(Label(master, text="Local Requests"), row=2, column=3)
        grid(Label(master, text="Remote Requests"), row=4, column=3)

        self.local_requests = VerticalScrolledTree(master, "local")
        self.remote_requests = VerticalScrolledTree(master, "remote")

        local_requests, remote_requests = Interface.populate_request_list()
        self.local_requests.populate(local_requests)
        self.remote_requests.populate(remote_requests)

        self.local_requests.grid(row=3, column=3, sticky=N + E + S + W)
        self.remote_requests.grid(row=5, column=3, sticky=N + E + S + W)

    def delete(self, id):
        return self.local_requests.delete_frame(id)


class EntryView(Frame):
    """
    Entry View
    """
    def __init__(self, master: Tk, label: str, var: StringVar):
        Frame.__init__(self, master)
        self.var = var
        self.trace = None

        self.columnconfigure(0, minsize=80, weight=0)
        self.columnconfigure(1, minsize=80, weight=1)

        self.label = grid(Label(self, text=label),
                          column=0, row=0)

        self.entry = Entry(self, textvariable=var)
        self.entry.anchor('ne')
        self.entry.insert(INSERT, var.get())
        self.entry.insert(END, "")
        grid(self.entry, column=1, row=0)

    def set_observer(self, callback):
        if self.trace:
            self.var.trace_vdelete("w", self.trace)
        self.trace = self.var.trace_variable("w", callback)


class MainView(Frame):
    """
    Main view contains all the widgets.
    """
    def __init__(self, master: Tk):
        Frame.__init__(self, master)

        # TODO Toggle View for remote Requests. What does view mean?

        # column0, row7 with column span
        reject_button = Button(master, text="REJECT",
                               command=
                               lambda: self.submit_with_busy_bar(reject=True))
        self.reject_button_grid = grid(reject_button, row=7, column=0)

        # Menu bar
        self.menu = Menu(master)
        self.menu.add_command(label='Exit', command=self.on_quit)
        master.config(menu=self.menu)

        # Banner
        self.banner = grid(
                Label(master,
                      text="OEC Synchronizer",
                      font="Helvetica 15 bold"),
                padx=0, pady=0,
                row=0, column=0,
                columnspan=3)

        # Message title view, row6, column1 with column span
        # Starts at row 5, column starts at 1 and ends at 2
        self.vw_message_title = grid(EntryView(master,
                                               "Title",
                                               StringVar()),
                                     padx=0, pady=0,
                                     row=6, column=1, columnspan=3)

        # Message view, row6, column1 with column span
        # Starts at row 7, column starts at 1 and ends at 2
        self.vw_message = grid(EntryView(master,
                                         "Message",
                                         StringVar()),
                               padx=0, pady=0,
                               row=7, column=1, columnspan=3)

        # History view, row2, column3.
        # Starts at row 2 - Label is at row 2, content starts at row 3
        requests_view = RequestHistoryView(master)
        self.requests = requests_view
        self.vw_history = grid(requests_view,
                               padx=0, pady=0,
                               row=2, column=3, rowspan=3)

        # column0, row5 with column span
        send_button = Button(master, text="SEND",
                             command=self.submit_with_busy_bar)
        self.send_button_grid = grid(send_button, row=6, column=0)

        sync_button = Button(master, text="SYNC",
                             command=self.sync_with_busy_bar)
        self.sync_button_grid = grid(sync_button, row=0, column=3)

        wait_vw = WaitFrame(master)
        self.vw_planet = grid(wait_vw, padx=0, pady=0, row=2, column=0,
                              columnspan=3, rowspan=4)

        # indefinite progress bar
        self.console = grid(ConsoleView(master), padx=0, pady=0, row=8,
                            column=0, columnspan=4)

        self.after(1000, self.sync_with_busy_bar)

    def on_quit(self):
        quit()

    def submit(self, progress: Progressbar, reject: bool=False, ) -> None:
        """
        The subroutine to submit/reject an update request
        """
        # get the index of the clicked object
        message, url = None, None
        selected_req, type = FOCUS

        if reject:
            if type == "remote":
                messagebox.showerror("Not Allowed", "Cannot reject remote "
                                                    "request")
                progress.master.destroy()
                progress.destroy()
            else:
                message, url = Interface.reject(selected_req)
        else:
            if type == "remote":
                messagebox.showerror("Not Allowed", "Cannot send remote "
                                                    "request")
                progress.master.destroy()
                progress.destroy()
            else:
                message, url = Interface.send(selected_req, self.edit)
        if ((message is not None and message != "") and
                (url is not None and url != "")):
            if messagebox.askokcancel(message, "View PR on github?"):
                webbrowser.open(url)

            # delete the object from the local request list
            self.requests.delete(selected_req)

            # refresh the remote and local requests
            get_updates = self.load_requests(progress)
            get_updates.start()
        else:
            progress.master.destroy()
            progress.destroy()

    def load_requests(self, progress: Progressbar):
        def show__requests():
            requests_view = RequestHistoryView(self.master)
            vw_history = grid(requests_view, padx=0, pady=0, row=2, column=3,
                              rowspan=3)
            firstsysname = Interface.get_system_from_index()
            requests_view.local_requests.on_req_selected("local-"+firstsysname)
            progress.master.destroy()
            progress.destroy()
            return requests_view, vw_history

        get_updates = threading.Thread(group=None,
                                       target=show__requests,
                                       name="get_updates")

        return get_updates

    def sync_with_busy_bar(self):
        def task():
            ft = Frame(self.master)
            grid(ft, row=8, column=0, columnspan=4)
            bar = Progressbar(ft, orient='horizontal',
                                    mode='indeterminate')
            bar.start(50)
            grid(bar, row=8, column=0, columnspan=4)
            t1 = threading.Thread(target=lambda: Interface.
                                  sync(self.load_requests(bar).start))
            t1.start()

        task()

    def submit_with_busy_bar(self, reject: bool=False):
        def task():
            ft = Frame(self.master)
            grid(ft, row=8, column=0, columnspan=4)
            bar = Progressbar(ft, orient='horizontal',
                                    mode='indeterminate')
            bar.start(50)
            grid(bar, row=8, column=0, columnspan=4)
            t1 = threading.Thread(target=lambda: self.
                                  submit(bar, reject))
            t1.start()

        task()

    def edit(self, content: str) -> str:
        tf_name = ""
        with tempfile.NamedTemporaryFile(suffix=".xml",
                                         delete=False) as tf:
            tf_name = tf.name
            tf.write(content.encode('utf-8'))

        proceed = messagebox.askyesnocancel("Edit", "Edit the file? "
                                            "This will launch the default"
                                            " editor '%s'" % EDITOR)
        if proceed is None:
            return
        elif (proceed == YES):
            while True:
                if os.name == 'posix':
                    call([EDITOR, tf_name])
                else:
                    call(['cmd.exe', '/c', tf_name])

                if messagebox.askyesno("Confirm",
                                       "Finished editing and submit?"):
                    break

        with open(tf_name, 'r', encoding='utf-8') as f:
            new_content = f.read()
        return new_content


# TODO Implement Help

# TODO Implement Search Update Request

# TODO Implement write to logfile instead of console esp if it was launch
    # by clicking


class OECSyncApp(Tk):
    """
    Window definition; set window properties, decide which columns and rows
    in grid
    """
    def __init__(self):
        Tk.__init__(self)

        style = AppStyle()

        # TODO insert some space filler at row 6 and 7 column 3
        self.title('OEC Synchronizer')
        self.grid()
        self.minsize(width=400, height=300)     # min size

        ws = self.winfo_screenwidth()  # width of the screen
        hs = self.winfo_screenheight()  # height of the screen
        win_width = 8.0/14.0 * ws  # default width
        win_height = 10.0/14.0 * hs  # default height

        x_position = (ws / 2) - (win_width / 2)
        y_position = (hs / 2) - (win_height / 2)

        # set the dimensions of the scree and position
        self.geometry('%dx%d+%d+%d' % (win_width, win_height, x_position,
                                       y_position))
        # default size
        self.configure(background="gray64")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, minsize=200, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, weight=1)
        self.vw = MainView(self)
        self.lift()  # place above all window


class WelcomeWindow(Tk):
    # TODO Documnet this class
    def __init__(self):
        Tk.__init__(self)
        self.overrideredirect(1)  # eliminate title bar

        ws = self.winfo_screenwidth()  # width of the screen
        hs = self.winfo_screenheight()  # height of the screen

        welcome_screen = ["Logo1_800.gif", "Logo2_800.gif"]
        path_welcome_screen = SrcPath.abs("gui", welcome_screen[randint(0, 1)])
        background_image = PhotoImage(file=path_welcome_screen)
        win_width = 13.9/14.0 * background_image.width()  # eliminates root bg
        win_height = 13.9/14.0 * background_image.height()

        # calculate x and y coordinates for the Tk root window
        x_position = (ws * 1.0 / 2.0) - (win_width * 1.0 / 2.0)
        y_position = (hs * 1.0 / 2.0) - (win_height * 1.0 / 2.0)

        background_label = Label(self, image=background_image)
        background_label.image = background_image  # don't remove this line!
        # eliminates root bezels
        background_label.place(relx=0.5, rely=0.5, anchor=CENTER)

        self.geometry('%dx%d+%d+%d' % (win_width, win_height, x_position,
                                       y_position))
        self.wait_visibility()
        self.lift()  # place above all window
        self.after(2000, self.destroy)


def launch(config: str):
    """
    Launches the GUI.
    :param config: config file
    """
    try:
        logging.debug("Init interface")
        init = threading.Thread(target=Interface.init, args=(config,))
        init.start()
        logging.debug("Init welcome window")
        welcome = WelcomeWindow()
        welcome.mainloop()
        init.join()

        app = OECSyncApp()
        app.mainloop()

    except Exception as e:
        dlg.error(e)

if __name__ == '__main__':
    launch()

