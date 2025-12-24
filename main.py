import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import messagebox

def load_AM92(file_path = 'am92(AM92).csv'):
    df = pd.read_csv(file_path, skiprows = 4, header = None)
    df.columns = ['Age_x', 'Duration_0', 'Duration_1', 'Durations_2+']
    df = df.dropna(subset=['Age_x'])                                            #去除缺失年龄
    df['Age_x'] = pd.to_numeric(df['Age_x'], errors='coerce')
    df = df.dropna(subset=['Age_x'])
    df['Age_x'] = df['Age_x'].astype(int)                                       #年龄转化成整数
    df.set_index('Age_x', inplace=True)
    df['Duration_0'] = df['Duration_0'].fillna(df['Durations_2+'])
    df['Duration_1'] = df['Duration_1'].fillna(df['Durations_2+'])
    return df

def get_q_x(table, x, entry_age):                                               #获取死亡概率
    duration = x - entry_age
    if duration == 0 and x in table.index:                                      #期限为0用q_x
        return table.at[x, "Duration_0"]
    elif duration == 1 and x in table.index:                                    #期限为1用q_x+1
        return table.at[x, "Duration_1"]
    else:
        if x in table.index:                                                    #其余用q_x+2+
            return table.at[x, "Durations_2+"]
        else:
            return 1.0                                                          #超出极限年龄即死
        
def calculate_k_p_x(table, entry_age, k):                                       #计算活过k年的概率
    if k == 0:                                                                  
        return 1.0
    p = 1.0                                                                     #递推活过p年的概率
    for t in range(k):
        age = entry_age + t
        q = get_q_x(table, age, entry_age)
        p *= (1-q)
    return p

def whole_life_assurance(table, x, i, max_age=120):                        #Whole Life Assurance
    v = 1 / (1 + i)
    A = 0.0
    for k in range(max_age - x + 1):
        p_k = calculate_k_p_x(table, x, k)
        q_next = get_q_x(table, x + k, x)
        A += v**(k+1) * p_k * q_next
    return A

def term_assurance(table, x, n, i):                                        #Term Assurance
    v = 1 / (1 + i)
    A = 0.0
    for k in range(n):
        p_k = calculate_k_p_x(table, x, k)
        q_next = get_q_x(table, x + k, x)
        A += v**(k + 1) * p_k * q_next
    return A

def endowment_assurance(table, x, n, i):                                   #Endowment Assurance
    term = term_assurance(table, x, n, i)
    v = 1 / (1 + i)
    survival = calculate_k_p_x(table, x, n)
    return term + v**n * survival

def whole_life_annuity(table, x, i, max_age=120):                          #Whole Life Annuity
    v = 1 / (1 + i)
    a = 0.0
    for k in range(max_age - x + 1):
        p_k = calculate_k_p_x(table, x, k)
        a += v**k * p_k
    return a + 1

def term_annuity(table, x, n, i):                                          #Term Annuity
    v = 1 / (1 + i)
    a = 0.0
    for k in range(n):
        p_k = calculate_k_p_x(table, x, k)
        a += v**k * p_k
    return a + 1

class AM92Calculator(tk.Tk):                                                    #UI
    def __init__(self):
        super().__init__()
        self.title("AM92 Calculator")
        self.geometry("600x600")
        self.resizable(True, True)
        
        self.table = load_AM92()
        self.create_widgets()

    def create_widgets(self):
        pad = {'padx': 10, 'pady': 8}
        
        tk.Label(self, text="Product Type:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky='w', **pad)
        self.product_var = tk.StringVar(value="whole_life_assurance")
        products = [("Whole Life Assurance", "whole_life_assurance"), ("Term Assurance", "term_assurance"), ("Endowment Assurance", "endowment_assurance"), ("Whole Life Annuity","whole_life_annuity"), ("Term Annuity", "term_annuity")]
        for i, (text, value) in enumerate(products):
            tk.Radiobutton(self, text=text, variable=self.product_var, value=value, command=self.toggle_term_entry).grid(row=i+1, column=0, columnspan=3, sticky='w', padx=30, pady=4)
            
        tk.Label(self, text="Age").grid(row=7, column=0, sticky='e', **pad)
        self.age_entry = tk.Entry(self, width=15)
        self.age_entry.grid(row=7, column=1, sticky='w', **pad)
        self.age_entry.insert(0, "40")
        
        tk.Label(self, text="Interest Rate:").grid(row=8, column=0, sticky='e', **pad)
        self.rate_entry = tk.Entry(self, width=15)
        self.rate_entry.grid(row=8, column=1, sticky='w', **pad)
        self.rate_entry.insert(0, "0.04")
        
        tk.Label(self, text="Duration").grid(row=9, column=0, sticky='e', **pad)
        self.term_entry = tk.Entry(self, width=15)
        self.term_entry.grid(row=9, column=1, sticky='w', **pad)
        self.term_entry.insert(0, "20")
        self.term_entry.config(state='disabled')                               #默认禁用
        
        self.cal_btn = tk.Button(self, text="Calculate", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", command=self.calculate)
        self.cal_btn.grid(row=10, column=0, columnspan=3, pady=20)
        
        self.result = tk.Label(self, text="Result:", font=("Arial", 14), fg="blue", wraplength=500)
        self.result.grid(row=11, column=0, columnspan=3, **pad)
        
    def toggle_term_entry(self):
        if self.product_var.get() in ["term_assurance", "endowment_assurance", "term_annuity"]:
            self.term_entry.config(state = 'normal')
        else:
            self.term_entry.config(state = 'disabled')
            
    def calculate(self):
        try:
            x = int(self.age_entry.get())
            i = float(self.rate_entry.get())
            product = self.product_var.get()
            
            if x < 17 or x > 120:
                raise ValueError("Age should between 17 and 120")
                
            if product in ["term_assurance", "endowment_assurance", "term_annuity"]:
                n = int(self.term_entry.get())
                if n <= 0:
                    raise ValueError("Duration should be positive interger")
            else:
                n = None
                
            if product == "whole_life_assurance":
                    val = whole_life_assurance(self.table, x, i)
                    symbol = f"A_{x}"
            elif product == "term_assurance":
                    val = term_assurance(self.table, x, n, i)
                    symbol = f"A¹_{{{x}:{n}}}"
            elif product == "endowment_assurance":
                    val = endowment_assurance(self.table, x, n, i)
                    symbol = f"A_{{{x}:{n}}}"
            elif product == "whole_life_annuity":
                    val = whole_life_annuity(self.table, x, i)
                    symbol = f"ä_{x}"
            elif product == "term_annuity":
                    val = term_annuity(self.table, x, n, i)
                    symbol = f"ä_{{{x}:{n}}}"

            self.result.config(text=f"{symbol} = {val:.6f}")
                
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))
            
if __name__ == "__main__":
    app = AM92Calculator()
    app.mainloop()