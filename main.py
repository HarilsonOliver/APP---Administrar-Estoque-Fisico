import tkinter as tk
from tkinter import messagebox, simpledialog
from database import init_oracle
from modulo_edicao import EdicaoEstoque
from modulo_relatorio import RelatoriosEstoque

class JanelaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Estoque 24HRS")
        self.geometry("400x300")
        init_oracle()
        self.show_menu()

    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_menu(self):
        self.limpar_tela()
        self.geometry("400x300")
        tk.Label(self, text="Menu", font=("Arial", 14)).pack(pady=20)
        tk.Button(self, text="📦 Alterar Estoque", command=self.verificar_senha, width=20).pack(pady=10)
        tk.Button(self, text="📊 Relatórios", command=self.abrir_relatorios, width=20).pack(pady=10)

    def verificar_senha(self):
        senha = simpledialog.askstring("Senha", "Digite a senha:", show='*')
        if senha == "13032743":
            self.abrir_edicao()
        else:
            messagebox.showerror("Erro", "Senha incorreta")

    def abrir_edicao(self):
        self.limpar_tela()
        self.geometry("950x700")
        modulo = EdicaoEstoque(self, self)
        modulo.pack(fill="both", expand=True)
        
    def abrir_relatorios(self):
        self.limpar_tela()
        self.geometry("900x600") # Tamanho ideal para relatórios
        modulo = RelatoriosEstoque(self, self)
        modulo.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = JanelaPrincipal()
    app.mainloop()