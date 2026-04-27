import sqlite3
import tkinter as tk
import os
import oracledb
from tkinter import messagebox, ttk
from database import DB_CONFIG
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

class RelatoriosEstoque(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.setup_ui()

    def setup_ui(self):
        # Botão Voltar
        btn_voltar = tk.Button(self, text="⬅ Voltar ao Menu", 
                                command=self.controller.show_menu,
                                bg="#6c757d", fg="white", font=('Helvetica', 9, 'bold'))
        btn_voltar.pack(anchor="nw", padx=10, pady=5)

        # Notebook (Abas) para separar os relatórios
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- ABA 1: HISTÓRICO DE ALTERAÇÕES ---
        self.tab_historico = tk.Frame(self.notebook)
        self.notebook.add(self.tab_historico, text="📝 Alterações")
        self.setup_aba_historico()

        # --- ABA 2: RELATÓRIO DE VENDAS ---
        self.tab_vendas = tk.Frame(self.notebook)
        self.notebook.add(self.tab_vendas, text="📊 Vendas")
        self.setup_aba_vendas()

    def setup_aba_historico(self):
        frame_controles = tk.Frame(self.tab_historico)
        frame_controles.pack(fill=tk.X, pady=5)

        tk.Button(frame_controles, text="🔄 Atualizar Histórico", 
                command=self.carregar_historico_local).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_controles, text="🖨 Imprimir Fita", 
                command=self.imprimir_estoque_gerencial, bg="#495057", fg="white").pack(side=tk.LEFT, padx=10)

        # Tabela de Histórico
        self.tree_hist = ttk.Treeview(self.tab_historico, 
                                    columns=("id", "cod", "desc", "qtd", "data"), 
                                    show='headings')
        
        self.tree_hist.heading("id", text="ID")
        self.tree_hist.heading("cod", text="Cód.")
        self.tree_hist.heading("desc", text="Descrição")
        self.tree_hist.heading("qtd", text="Qtd Informada")
        self.tree_hist.heading("data", text="Data/Hora")
        
        self.tree_hist.column("id", width=50)
        self.tree_hist.column("cod", width=80)
        self.tree_hist.column("desc", width=300)
        self.tree_hist.column("qtd", width=100)
        self.tree_hist.column("data", width=150)
        
        self.tree_hist.pack(fill=tk.BOTH, expand=True)
        self.carregar_historico_local()

    def setup_aba_vendas(self):
        frame_filtros = tk.LabelFrame(self.tab_vendas, text=" Filtros de Venda ", padx=10, pady=10)
        frame_filtros.pack(fill=tk.X, padx=10, pady=5)

        # Coluna 0 e 1: Data Início
        tk.Label(frame_filtros, text="Data Início:").grid(row=0, column=0)
        self.ent_data_ini = tk.Entry(frame_filtros, width=11)
        self.ent_data_ini.grid(row=0, column=1, padx=2)
        
        # Coluna 2 e 3: Hora Início
        tk.Label(frame_filtros, text="Hora (HH:MM):").grid(row=0, column=2)
        self.ent_hora_ini = tk.Entry(frame_filtros, width=7)
        self.ent_hora_ini.insert(0, "00:00")
        self.ent_hora_ini.grid(row=0, column=3, padx=2)

        # Coluna 4 e 5: Data Fim (Estava repetindo column 2 e 3)
        tk.Label(frame_filtros, text="Data Fim:").grid(row=0, column=4)
        self.ent_data_fim = tk.Entry(frame_filtros, width=11)
        self.ent_data_fim.grid(row=0, column=5, padx=2)

        # Coluna 6 e 7: Emitente
        tk.Label(frame_filtros, text="Emitente:").grid(row=0, column=6)
        self.combo_emitente = ttk.Combobox(frame_filtros, values=["TODOS", "156", "175", "128", "126", "127", "129"], width=8)
        self.combo_emitente.set("TODOS")
        self.combo_emitente.grid(row=0, column=7, padx=5)

        # Botões nas colunas seguintes
        tk.Button(frame_filtros, text="🔍 Pesquisar", bg="#007bff", fg="white",
                command=self.carregar_vendas_oracle).grid(row=0, column=8, padx=10)
        tk.Button(frame_filtros, text="🖨 Imprimir", bg="#495057", fg="white",
                command=self.imprimir_vendas_oracle).grid(row=0, column=9, padx=10)

        # Tabela de Vendas
        # No método setup_aba_vendas
        self.tree_vendas = ttk.Treeview(self.tab_vendas, 
                            columns=("nota", "data", "codcob", "vltotal", "sefaz", "codprod", "desc", "qtd", "total_item", "emitente", "est_gerencial", "diferenca"), 
                            show='headings')

        # Ajuste os títulos para facilitar a leitura
        titulos = {
            "nota": "NOTA", "data": "DATA", "codcob": "COBRANÇA", 
            "vltotal": "VL. TOTAL NF", "sefaz": "DATA/HORA",
            "codprod": "CÓD. PROD", "desc": "DESCRIÇÃO", 
            "qtd": "QTD. VEND", 
            "total_item": "VLR. TOTAL ITEM", 
            "emitente": "EMITENTE",
            "est_gerencial": "EST. GERENCIAL", 
            "diferenca": "SALDO (EST-VEN)"    
        }

        for col in self.tree_vendas["columns"]:
            self.tree_vendas.heading(
                col, 
                text=titulos.get(col, col.upper()), 
                # Adicione a linha abaixo para habilitar a ordenação ao clicar
                command=lambda _col=col: self.ordenar_coluna(self.tree_vendas, _col, False)
            )
            self.tree_vendas.column(col, width=100)
            
        self.tree_vendas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def ordenar_coluna(self, tree, col, reverse):
        # Obtém todos os itens da coluna
        lista = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        # Tenta converter para número se possível, para ordenação correta (10 vir antes de 2)
        try:
            lista.sort(key=lambda t: float(t[0].replace(',', '.')), reverse=reverse)
        except ValueError:
            lista.sort(reverse=reverse)

        # Reorganiza os itens no Treeview
        for index, (val, k) in enumerate(lista):
            tree.move(k, '', index)

        # Inverte o comando para o próximo clique
        tree.heading(col, command=lambda _col=col: self.ordenar_coluna(tree, _col, not reverse))
        
    def gerar_pdf_termico_vendas(self, titulo, dados, periodo, total_geral, resumo_cob):
        largura_fita = 80 * mm
        altura_estimada = (len(dados) * 5 * mm) + (len(resumo_cob) * 5 * mm) + 120 * mm
        nome_arquivo = "relatorio_vendas_fita.pdf"

        c = canvas.Canvas(nome_arquivo, pagesize=(largura_fita, altura_estimada))
        y = altura_estimada - 10 * mm

        # Cabeçalho
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(largura_fita/2, y, "FRIJEL - 24HRS")
        y -= 5 * mm
        c.setFont("Helvetica", 9)
        c.drawCentredString(largura_fita/2, y, titulo)
        y -= 5 * mm
        if periodo:
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(largura_fita/2, y, f"PERÍODO: {periodo}")
            y -= 7 * mm
        
        c.line(5*mm, y, 75*mm, y)
        y -= 5 * mm

        # Cabeçalho da Tabela de Itens (Fonte 5 para o cabeçalho)
        c.setFont("Helvetica-Bold", 5)
        c.drawString(5*mm, y, "COD")
        c.drawString(15*mm, y, "PRODUTO")
        c.drawRightString(48*mm, y, "VENDAS")
        c.drawRightString(62*mm, y, "ESTOQ.")
        c.drawRightString(75*mm, y, "SALDO")
        y -= 4 * mm

        # Listagem de Itens (Fonte 4 conforme solicitado)
        c.setFont("Helvetica", 4)
        for item in dados:
            c.drawString(5*mm, y, str(item[0]))      # CODPROD
            c.drawString(15*mm, y, str(item[1])[:25]) # DESCRIÇÃO
            
            qtd_vendida = f"{float(item[2]):.2f}"
            est_gerencial = f"{float(item[3]):.2f}"
            saldo = f"{float(item[4]):.2f}"
            
            c.drawRightString(48*mm, y, qtd_vendida) # QTD VENDIDA
            c.drawRightString(62*mm, y, est_gerencial) # ESTOQUE GERENCIAL
            c.drawRightString(75*mm, y, saldo) # SALDO (EST - VEND)
            y -= 3 * mm # Espaçamento menor para fonte pequena

        y -= 5 * mm
        c.line(15*mm, y, 65*mm, y)
        y -= 7 * mm

        # RESUMO POR COBRANÇA
        c.setFont("Helvetica-Bold", 9)
        c.drawString(5*mm, y, "Resumo Financeiro:")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        for cob, valor in resumo_cob.items():
            c.drawString(10*mm, y, f"Forma de pagamento: {cob}")
            c.drawRightString(70*mm, y, f"R$ {valor:.2f}")
            y -= 4 * mm

        # TOTAL GERAL
        y -= 3 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5*mm, y, "Total:")
        c.drawRightString(75*mm, y, f"R$ {total_geral:.2f}")
        
        # ASSINATURAS
        y -= 20 * mm
        c.line(10*mm, y, 70*mm, y)
        y -= 4 * mm
        c.drawCentredString(largura_fita/2, y, "Funcionario 1")
        
        y -= 15 * mm
        c.line(10*mm, y, 70*mm, y)
        y -= 4 * mm
        c.drawCentredString(largura_fita/2, y, "Funcionario 2")

        c.save()
        os.startfile(nome_arquivo)

    # --- Métodos para acionar a impressão nas abas ---

    def imprimir_estoque_gerencial(self):
        """Extrai dados do histórico local para o PDF"""
        try:
            with sqlite3.connect('estoque_gerencial.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT codprod, descricao, quantidade FROM historico_alteracoes ORDER BY id DESC LIMIT 50")
                dados = cursor.fetchall()
                if not dados:
                    messagebox.showwarning("Aviso", "Não há dados para imprimir.")
                    return
                self.gerar_pdf_termico_vendas("ALTERAÇÕES ESTOQUE", ["COD", "DESC", "QTD"], dados)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def imprimir_vendas_oracle(self):
        """Extrai dados da tabela para o PDF térmico com totais e resumo"""
        itens = []
        totais_por_cobradora = {}
        valor_total_geral = 0.0
        datas_horas = []

        filhos = self.tree_vendas.get_children()
        if not filhos:
            messagebox.showwarning("Aviso", "Pesquise as vendas primeiro.")
            return

        for child in filhos:
            v = self.tree_vendas.item(child)["values"]
            
            cod_cob = str(v[2])
            valor_nf = float(v[3])
            data_sefaz = str(v[4])
            
            if data_sefaz:
                datas_horas.append(data_sefaz)
                
            valor_total_geral += valor_nf
            totais_por_cobradora[cod_cob] = totais_por_cobradora.get(cod_cob, 0) + valor_nf
            
            # Captura: CodProd(5), Desc(6), QtdVend(7), EstGerencial(10), Saldo(11)
            itens.append((v[5], v[6], v[7], v[10], v[11]))

        # Determina o período
        periodo = ""
        if datas_horas:
            periodo = f"{datas_horas[0]} até {datas_horas[-1]}"

        self.gerar_pdf_termico_vendas(
            titulo="RESUMO DE VENDAS",
            dados=itens,
            periodo=periodo,
            total_geral=valor_total_geral,
            resumo_cob=totais_por_cobradora
        )
    # --- LÓGICA DE DADOS ---

    def carregar_historico_local(self):
        """Busca dados da tabela historico_alteracoes do SQLite"""
        for item in self.tree_hist.get_children():
            self.tree_hist.delete(item)
            
        try:
            with sqlite3.connect('estoque_gerencial.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, codprod, descricao, quantidade, data_hora FROM historico_alteracoes ORDER BY id DESC")
                for row in cursor.fetchall():
                    self.tree_hist.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Erro SQLite", str(e))

    def carregar_vendas_oracle(self):
        dt_ini = self.ent_data_ini.get()
        dt_fim = self.ent_data_fim.get()
        hora_ini = self.ent_hora_ini.get() 
        emitente_sel = self.combo_emitente.get()

        if not dt_ini or not dt_fim or not hora_ini:
            messagebox.showwarning("Aviso", "Preencha data e hora corretamente.")
            return

        for item in self.tree_vendas.get_children():
            self.tree_vendas.delete(item)

        try:
            # 1. Conexão com Oracle
            conn = oracledb.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 2. Tratamento da hora
            raw_hora = hora_ini.strip() if hora_ini.strip() else "0"
            hora_formatada = raw_hora.replace(':', '.').split('.')[0]
            valor_hora = int(hora_formatada) if hora_formatada.isdigit() else 0

            # 3. Definição de parâmetros
            params = {
                'DATAI': dt_ini, 
                'DATAF': dt_fim, 
                'HORAI': valor_hora 
            }
            
            if emitente_sel != "TODOS":
                filtro_emitente = "AND F.CODEMITENTE = :EMIT"
                params['EMIT'] = emitente_sel
            else:
                filtro_emitente = "AND F.CODEMITENTE IN (156,175,128,126,127,129)"

            # 4. Execução da Query no Oracle
            sql = f"""
            SELECT
                F.NUMNOTA,
                TO_CHAR(F.DTSAIDA, 'DD/MM/YYYY'),
                F.CODCOB,
                F.VLTOTAL,
                TO_CHAR(F.DTHORAAUTORIZACAOSEFAZ, 'DD/MM HH24:MI'),
                M.CODPROD,
                P.DESCRICAO,
                M.QT,
                (M.PUNIT * M.QT) AS TOTAL_ITEM,
                E.NOME
            FROM
                PCNFSAID F, PCMOV M, PCPRODUT P, PCEMPR E
            WHERE
                F.NUMTRANSVENDA = M.NUMTRANSVENDA    
                AND M.CODPROD = P.CODPROD            
                AND F.CODEMITENTE = E.MATRICULA   
                AND F.DTSAIDA BETWEEN TO_DATE(:DATAI, 'DD/MM/YYYY') AND TO_DATE(:DATAF, 'DD/MM/YYYY')
                AND TRUNC(F.HORALANC) >= :HORAI 
                AND F.CODFILIAL IN (3)
                AND F.CAIXA IS NOT NULL
                AND F.CAIXA <> 0
                {filtro_emitente}
            ORDER BY F.NUMNOTA
            """
            cursor.execute(sql, params)
            vendas = cursor.fetchall()

            # 5. Cruzamento com SQLite (Estoque Gerencial)
            with sqlite3.connect('estoque_gerencial.db') as conn_sql:
                cursor_sql = conn_sql.cursor()
                
                for row in vendas:
                    codprod = row[5]      # M.CODPROD
                    qtd_vendida = row[7]  # M.QT
                    
                    # Busca a última alteração registrada para este produto no histórico
                    cursor_sql.execute(
                        "SELECT quantidade FROM historico_alteracoes WHERE codprod = ? ORDER BY id DESC LIMIT 1", 
                        (codprod,)
                    )
                    res = cursor_sql.fetchone()
                    
                    qtd_gerencial = float(res[0]) if res else 0.0
                    subtracao = qtd_gerencial - float(qtd_vendida)
                    
                    # Adiciona os novos campos ao final da linha original
                    valores_finais = list(row) + [qtd_gerencial, subtracao]
                    self.tree_vendas.insert("", tk.END, values=valores_finais)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Erro ao buscar ou cruzar dados: {e}")