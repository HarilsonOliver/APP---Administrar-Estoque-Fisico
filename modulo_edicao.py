import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import oracledb
from database import DB_CONFIG 

class EdicaoEstoque(tk.Frame): 
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.dados_completos = []
        self.filtro_depto = tk.BooleanVar(value=True)
        
        self.init_db_local()
        self.setup_ui()
        # Opcional: carregar os dados automaticamente ao abrir
        self.atualizar_tabela()

    def init_db_local(self):
        try:
            with sqlite3.connect('estoque_gerencial.db') as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS estoque_gerencial (
                        codprod INTEGER PRIMARY KEY,
                        descricao TEXT,
                        qt_separada REAL DEFAULT 0
                    )
                ''')
                #TABELA: Historico de Alteração
                conn.execute('''
                        CREATE TABLE IF NOT EXISTS historico_alteracoes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            codprod INTEGER,
                            descricao TEXT,
                            quantidade REAL,
                            data_hora TEXT
                        )
                    ''')
        except Exception as e:
            print(f"Erro banco local: {e}")

    def setup_ui(self):
        # Botão voltar no topo
        btn_voltar = tk.Button(self, text="⬅ Voltar ao Menu", 
                                command=self.controller.show_menu,
                                bg="#6c757d", fg="white", font=('Helvetica', 9, 'bold'))
        btn_voltar.pack(anchor="nw", padx=10, pady=5)

        # --- FRAME DE COMANDOS ---
        frame_topo = tk.LabelFrame(self, text=" Lançamento Gerencial ", padx=10, pady=10)
        frame_topo.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_topo, text="Cod. Prod:").pack(side=tk.LEFT)
        self.ent_cod = tk.Entry(frame_topo, width=10)
        self.ent_cod.pack(side=tk.LEFT, padx=5)

        tk.Label(frame_topo, text="Nova Qtd:").pack(side=tk.LEFT)
        self.ent_qt = tk.Entry(frame_topo, width=10)
        self.ent_qt.pack(side=tk.LEFT, padx=5)

        tk.Button(frame_topo, text="Salvar Gerencial", bg="#28a745", fg="white", font=('Helvetica', 9, 'bold'),
                command=self.adicionar_estoque).pack(side=tk.LEFT, padx=10)
        
        tk.Button(frame_topo, text="Sincronizar Vendas", bg="#007bff", fg="white", font=('Helvetica', 9, 'bold'),
                command=self.atualizar_tabela).pack(side=tk.LEFT, padx=10)
        
        tk.Button(frame_topo, text="Zerar Gerencial", bg="#dc3545", fg="white", font=('Helvetica', 9, 'bold'),
                command=self.zerar_estoque_gerencial).pack(side=tk.LEFT, padx=10)
        
        tk.Label(frame_topo, text=" | Filtro:").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(frame_topo, text="Depto 188", variable=self.filtro_depto, 
                value=True, command=self.atualizar_tabela).pack(side=tk.LEFT)
        tk.Radiobutton(frame_topo, text="Todos (Filial 3)", variable=self.filtro_depto, 
                value=False, command=self.atualizar_tabela).pack(side=tk.LEFT)


        # --- FRAME DE BUSCA ---
        frame_busca = tk.Frame(self, padx=10, pady=5)
        frame_busca.pack(fill=tk.X)

        tk.Label(frame_busca, text="🔍 Filtrar Produto:", font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT)
        self.ent_busca = tk.Entry(frame_busca, width=40)
        self.ent_busca.pack(side=tk.LEFT, padx=10)
        self.ent_busca.bind("<KeyRelease>", self.aplicar_filtro)

        # --- CONTAINER DA TABELA (FRAME + SCROLLBAR) ---
        container_tabela = tk.Frame(self)
        container_tabela.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Criar a barra de rolagem
        scrollbar_v = tk.Scrollbar(container_tabela, orient=tk.VERTICAL)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)

        # Criar a tabela dentro do container
        self.tree = ttk.Treeview(container_tabela, 
                                columns=("cod", "desc", "oficial", "gerencial", "vendas"), 
                                show='headings',
                                yscrollcommand=scrollbar_v.set) # Conecta a tabela à scrollbar
        
        # Configurar a scrollbar para rolar a tabela
        scrollbar_v.config(command=self.tree.yview)

        # Definições das colunas (mesmo código que você já tinha)
        self.tree.heading("cod", text="Cód. Prod")
        self.tree.heading("desc", text="Descrição")
        self.tree.heading("oficial", text="Qtd Oficial")
        self.tree.heading("gerencial", text="Qtd Gerencial")
        self.tree.heading("vendas", text="Vendas Hoje")
        
        self.tree.column("cod", width=80, anchor=tk.CENTER)
        self.tree.column("desc", width=350)
        self.tree.column("oficial", width=100, anchor=tk.CENTER)
        self.tree.column("gerencial", width=100, anchor=tk.CENTER)
        self.tree.column("vendas", width=80, anchor=tk.CENTER)
        
        for col in ("cod", "desc", "oficial", "gerencial", "vendas"):
            self.tree.heading(col, command=lambda c=col: self.ordenar_coluna(c, False))
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.selecionar_item)

    # --- MÉTODOS DE LÓGICA (Permanecem iguais, mas corrigindo referências de conexão) ---

    def ordenar_coluna(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.ordenar_coluna(col, not reverse))

    def selecionar_item(self, event):
        item_selecionado = self.tree.focus()
        if item_selecionado:
            valores = self.tree.item(item_selecionado)['values']
            self.ent_cod.delete(0, tk.END)
            self.ent_cod.insert(0, valores[0]) 
            self.ent_qt.delete(0, tk.END)
            self.ent_qt.focus()

    def buscar_dados_oracle(self):
        dados_oracle = {}
        try:
            conn = oracledb.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Base da query para a Filial 3
            sql_base = """
                SELECT E.CODPROD, P.DESCRICAO, E.QTEST 
                FROM PCEST E, PCPRODUT P 
                WHERE E.CODPROD = P.CODPROD 
                AND E.CODFILIAL = 3 
                AND E.QTEST >= 0
            """
            
            # Adiciona o filtro de departamento se a variável for True
            if self.filtro_depto.get():
                sql_base += " AND P.CODEPTO = 188"
                
            cursor.execute(sql_base)
            for row in cursor.fetchall():
                dados_oracle[row[0]] = {'desc': row[1], 'oficial': row[2], 'vendas': 0}

            # Query de vendas (mantendo os filtros de emitentes da Frijel)
            cursor.execute("""
                SELECT M.CODPROD, SUM(M.QT) 
                FROM PCNFSAID F, PCMOV M 
                WHERE F.NUMTRANSVENDA = M.NUMTRANSVENDA 
                AND F.DTSAIDA = TRUNC(SYSDATE) 
                AND F.CODFILIAL = 3 
                AND F.CODEMITENTE IN (156, 175) 
                AND F.CAIXA IS NOT NULL
                AND F.CAIXA <> 0
                AND F.DTCANCEL IS NULL
                GROUP BY M.CODPROD
            """)
            
            for row in cursor.fetchall():
                if row[0] in dados_oracle:
                    dados_oracle[row[0]]['vendas'] = row[1]
                    
            conn.close()
            return dados_oracle
        except Exception as e:
            messagebox.showerror("Erro Oracle", str(e))
            return {}

    def adicionar_estoque(self):
        cod = self.ent_cod.get().strip()
        qtd = self.ent_qt.get().strip()
        if not cod or qtd == "": return
        
        try:
            cod_int = int(cod)
            qtd_float = float(qtd)
            
            # Busca a descrição no cache para salvar no histórico
            desc_produto = "Não identificado"
            for d in self.dados_completos:
                if d[0] == cod_int:
                    desc_produto = d[1]
                    break

            with sqlite3.connect('estoque_gerencial.db') as conn:
                cursor = conn.cursor()
                
                # 1. Atualiza ou Insere no estoque gerencial
                cursor.execute('''
                    INSERT INTO estoque_gerencial (codprod, qt_separada) VALUES (?, ?) 
                    ON CONFLICT(codprod) DO UPDATE SET qt_separada = excluded.qt_separada
                ''', (cod_int, qtd_float))
                
                # 2. Registra o Log com data e hora atual
                # No arquivo modulo_edicao.py, dentro de adicionar_estoque:
                # Certifique-se de que a gravação use este formato:
                cursor.execute('''
                    INSERT INTO historico_alteracoes (codprod, descricao, quantidade, data_hora)
                    VALUES (?, ?, ?, STRFTIME('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
                ''', (cod_int, desc_produto, qtd_float))
                
                conn.commit()

            messagebox.showinfo("Sucesso", f"Produto {cod} atualizado com sucesso!")
            self.ent_qt.delete(0, tk.END)
            self.ent_cod.delete(0, tk.END) # Limpa o código também para evitar erro
            self.atualizar_tabela()
            
        except ValueError:
            messagebox.showerror("Erro", "Código ou Quantidade inválidos.")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", str(e))
            
    def zerar_estoque_gerencial(self):
        # Confirmação de segurança
        if not messagebox.askyesno("Confirmar", "Deseja realmente ZERAR todo o estoque gerencial?"):
            return
        
        try:
            with sqlite3.connect('estoque_gerencial.db') as conn:
                cursor = conn.cursor()
                
                # 1. Busca os itens atuais para registrar no histórico antes de apagar
                cursor.execute("SELECT codprod, qt_separada FROM estoque_gerencial WHERE qt_separada > 0")
                itens_atuais = cursor.fetchall()
                
                if itens_atuais:
                    for cod, qtd in itens_atuais:
                        # Busca a descrição no cache 'dados_completos'
                        desc_produto = "Zeramento Geral"
                        for d in self.dados_completos:
                            if d[0] == cod:
                                desc_produto = d[1]
                                break
                        
                        # Registra no histórico que foi zerado
                        cursor.execute('''
                            INSERT INTO historico_alteracoes (codprod, descricao, quantidade, data_hora)
                            VALUES (?, ?, ?, DATETIME('now', 'localtime'))
                        ''', (cod, f"ZERADO: {desc_produto}", 0))

                # 2. Limpa a tabela de estoque gerencial
                cursor.execute("DELETE FROM estoque_gerencial")
                conn.commit()

            messagebox.showinfo("Sucesso", "Estoque gerencial zerado e registrado no histórico!")
            self.atualizar_tabela()
            
        except Exception as e:
            messagebox.showerror("Erro ao zerar", str(e))

    def atualizar_tabela(self):
        dados_ora = self.buscar_dados_oracle()
        if not dados_ora: return
        
        with sqlite3.connect('estoque_gerencial.db') as conn_loc:
            cursor_loc = conn_loc.cursor()
            cursor_loc.execute("SELECT codprod, qt_separada FROM estoque_gerencial")
            dados_loc = {row[0]: row[1] for row in cursor_loc.fetchall()}

        self.dados_completos = []
        for cod, info in dados_ora.items():
            qtd_ger_bruta = dados_loc.get(cod, 0)
            vendas_hoje = info['vendas']
            saldo_ger_final = max(0, qtd_ger_bruta - vendas_hoje)
            self.dados_completos.append((cod, info['desc'], info['oficial'], saldo_ger_final, vendas_hoje))
        
        self.aplicar_filtro()

    def aplicar_filtro(self, event=None):
        termo = self.ent_busca.get().upper()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for d in self.dados_completos:
            if termo in str(d[0]) or termo in str(d[1]).upper():
                self.tree.insert("", tk.END, values=d)