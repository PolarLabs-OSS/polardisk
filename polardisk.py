"""PolarDisk - read-only directory analyzer, PolarLabs-OSS."""
import os
import csv
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BG="#091623"; PANEL="#122537"; FG="#EAF6FA"; ACC="#27D6D0"; MUTED="#9BB5C2"
def fmt(n):
    for u in ("B","KB","MB","GB","TB"):
        if abs(n)<1024 or u=="TB":return f"{n:.1f} {u}"
        n/=1024

def walk_files(folder, cancel=None):
    """Enumerate regular files without following symlinks or Windows junctions."""
    stack=[Path(folder)]
    while stack:
        if cancel and cancel.is_set():return
        directory=stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if cancel and cancel.is_set():return
                    try:
                        if entry.is_symlink():continue
                        if entry.is_dir(follow_symlinks=False):
                            if os.name=="nt" and entry.stat(follow_symlinks=False).st_file_attributes & 0x400:
                                continue
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            yield entry.path
                    except (OSError,PermissionError):
                        continue
        except (OSError,PermissionError):
            continue

def scan(folder, cancel=None, progress=None):
    """Two passes: count files, then measure sizes with real percentage progress."""
    base=Path(folder)
    if not base.is_dir():raise ValueError("La cartella non esiste")
    if progress:progress("count",0,0)
    total=0
    for path in walk_files(base,cancel):
        total+=1
        if progress and total%250==0:progress("count",total,0)
    if cancel and cancel.is_set():return [],0
    if progress:progress("scan",0,total)
    items=[];errors=0;done=0
    for path in walk_files(base,cancel):
        try:
            items.append((path,os.stat(path,follow_symlinks=False).st_size))
        except (OSError,PermissionError):
            errors+=1
        done+=1
        if progress and (done%100==0 or done==total):progress("scan",done,total)
    if progress:progress("scan",done,total)
    return items,errors

def folders_summary(paths,root):
    root=Path(root)
    result={}
    for p,size in paths:
        rel=Path(p).relative_to(root)
        group=rel.parts[0] if len(rel.parts)>1 else "(file nella cartella principale)"
        result[group]=result.get(group,0)+size
    return sorted(result.items(),key=lambda row:row[1],reverse=True)

class App:
    def __init__(self,root):
        self.root=root;root.title("PolarDisk | PolarLabs-OSS")
        root.geometry("1050x740");root.configure(bg=BG)
        self.items=[];self.root_folder="";self.cancel=threading.Event();self.running=False
        box=tk.Frame(root,bg=BG,padx=25,pady=20);box.pack(fill="both",expand=True)
        tk.Label(box,text="POLAR / DISK",fg=ACC,bg=BG,font=("Segoe UI",26,"bold")).pack(anchor="w")
        tk.Label(box,text="Analizza spazio e file più grandi  •  Sola lettura  •  Nessuna cancellazione",fg=MUTED,bg=BG).pack(anchor="w",pady=(0,15))
        bar=tk.Frame(box,bg=BG);bar.pack(fill="x",pady=6)
        self.button(bar,"Seleziona cartella / disco",self.pick,True).pack(side="left",padx=(0,9))
        self.button(bar,"Interrompi",lambda:self.cancel.set()).pack(side="left",padx=(0,9))
        self.button(bar,"Esporta CSV",self.export).pack(side="left")
        self.path=tk.StringVar(value="Nessuna cartella selezionata")
        tk.Label(box,textvariable=self.path,fg=FG,bg=BG,anchor="w").pack(fill="x",pady=(10,10))
        self.stats=tk.StringVar(value="Seleziona una directory per iniziare")
        tk.Label(box,textvariable=self.stats,fg=ACC,bg=BG,font=("Segoe UI",13,"bold")).pack(anchor="w",pady=(0,12))
        notebook=ttk.Notebook(box);notebook.pack(fill="both",expand=True)
        style=ttk.Style();style.theme_use("clam")
        style.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=FG,rowheight=28)
        style.configure("Treeview.Heading",background="#1B3850",foreground=FG)
        self.filetree=ttk.Treeview(notebook,columns=("name","size"),show="headings")
        self.filetree.heading("name",text="Percorso del file");self.filetree.heading("size",text="Dimensione")
        self.filetree.column("name",width=780);self.filetree.column("size",width=140,anchor="e")
        self.foldertree=ttk.Treeview(notebook,columns=("name","size","share"),show="headings")
        for k,label,w in (("name","Sottocartella",580),("size","Dimensione",160),("share","Quota",120)):
            self.foldertree.heading(k,text=label);self.foldertree.column(k,width=w)
        notebook.add(self.filetree,text="File più grandi")
        notebook.add(self.foldertree,text="Spazio per sottocartella")
        self.progress=ttk.Progressbar(box,mode="indeterminate",maximum=100)
        self.progress.pack(fill="x",pady=(14,6))
        self.percent=tk.StringVar(value="0%")
        tk.Label(box,textvariable=self.percent,fg=ACC,bg=BG,font=("Segoe UI",12,"bold")).pack(anchor="e")
        self.status=tk.StringVar(value="Pronto")
        tk.Label(box,textvariable=self.status,fg=MUTED,bg=BG).pack(anchor="w")
        tk.Label(box,text="PolarLabs-OSS • Strumento offline • I file non vengono aperti né modificati",fg=MUTED,bg=BG,font=("Segoe UI",8)).pack(anchor="w",pady=(10,0))
    def button(self,parent,label,command,primary=False):
        return tk.Button(parent,text=label,command=command,bg=ACC if primary else PANEL,fg=BG if primary else FG,relief="flat",padx=13,pady=8)
    def pick(self):
        if self.running:return
        p=filedialog.askdirectory(title="Scegli cartella o unità")
        if not p:return
        self.root_folder=p;self.path.set(p);self.run()
    def run(self):
        self.running=True;self.cancel.clear();self.progress.start(12);self.status.set("Scansione in corso…")
        for tree in (self.filetree,self.foldertree):
            for row in tree.get_children():tree.delete(row)
        def worker():
            try:
                items,errors=scan(self.root_folder,self.cancel,self.report_progress)
                self.root.after(0,lambda:self.done(items,errors))
            except Exception as e:
                self.root.after(0,lambda msg=str(e):self.failed(msg))
        threading.Thread(target=worker,daemon=True).start()
    def report_progress(self,phase,done,total):
        self.root.after(0,lambda:self.show_progress(phase,done,total))
    def show_progress(self,phase,done,total):
        if phase=="count":
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
            self.percent.set("Conteggio…")
            self.status.set(f"Conteggio iniziale: {done:,} file individuati")
        else:
            self.progress.stop()
            self.progress.configure(mode="determinate",maximum=100)
            value=min(100,round(done*100/total)) if total else 100
            self.progress["value"]=value
            self.percent.set(f"{value}%  ({done:,}/{total:,} file)")
            self.status.set("Analisi delle dimensioni in corso…")
    def failed(self,message):
        self.running=False;self.progress.stop();messagebox.showerror("PolarDisk",message)
    def done(self,items,errors):
        self.running=False;self.progress.stop();self.items=items
        total=sum(size for _,size in items)
        self.stats.set(f"{len(items):,} file  •  {fmt(total)} analizzati")
        for index,(p,size) in enumerate(sorted(items,key=lambda x:x[1],reverse=True)[:1000]):
            self.filetree.insert("","end",values=(p,fmt(size)))
        for name,size in folders_summary(items,self.root_folder):
            self.foldertree.insert("","end",values=(name,fmt(size),f"{size/total*100:.1f}%" if total else "0%"))
        self.status.set(("Interrotto. Risultati parziali. " if self.cancel.is_set() else "Scansione completata. ")+f"Cartelle/file non accessibili: {errors}")
    def export(self):
        if not self.items:return messagebox.showinfo("PolarDisk","Prima esegui una scansione")
        filename=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if filename:
            try:
                with open(filename,"w",newline="",encoding="utf-8-sig") as f:
                    writer=csv.writer(f);writer.writerow(["Path","Size (bytes)"])
                    writer.writerows(sorted(self.items,key=lambda r:r[1],reverse=True))
                self.status.set("Report CSV esportato")
            except OSError as e:messagebox.showerror("PolarDisk",str(e))
from ui_theme import apply_theme

if __name__=="__main__":
    root=tk.Tk();App(root);apply_theme(root);root.mainloop()
