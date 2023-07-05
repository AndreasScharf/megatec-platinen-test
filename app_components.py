import tkinter as tk


class navigator:
    def __init__(self, window, ):
        self.navigator_wrapper = tk.Frame(window)
        self.navigator_wrapper.pack(pady=5, fill=tk.X, expand=True)
        
        self.navigator_back = tk.Button(
            master=self.navigator_wrapper, bg='#F0FFFF', font=("Arial", 16), text="Zurück", command=self.backBtnClicked)
        self.navigator_back.pack(side='left', padx=5)

        self.title = tk.Label(
            master=self.navigator_wrapper, text='Hello', font=("Arial", 16))
        self.title.pack(side='left', fill=tk.X, expand=True)

        self.navigator_next = tk.Button(
            master=self.navigator_wrapper, bg='#F0FFFF', font=("Arial", 16), text="Weiter", command=self.nextBtnClicked)
        self.navigator_next.pack(side='left', padx=5)
        
    def backBtnClicked(self):
        if self.back and callable(self.back):
            self.back()
        
    def nextBtnClicked(self):
        if self.next and callable(self.next):
            self.next()
    def setTitle(self, text):
        self.title.configure(text=text)
