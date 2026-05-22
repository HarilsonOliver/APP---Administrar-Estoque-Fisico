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
        
    def formatar_data_input(self, event):
        """Formata a data automaticamente conforme o usuário digita (DD-MM-AAAA)"""
        entry = event.widget
        texto = entry.get().replace("-", "")[:8]
        novo_texto = ""
        
        if event.keysym == "BackSpace": return

        for i, char in enumerate(texto):
            if i == 2 or i == 4:
                novo_texto += "-"
            novo_texto += char
        
        entry.delete(0, tk.END)
        entry.insert(0, novo_texto)

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
        frame_filtros_hist = tk.LabelFrame(self.tab_historico, text=" Filtros de Histórico ", padx=10, pady=10)
        frame_filtros_hist.pack(fill=tk.X, padx=10, pady=5)

        # Data Início
        tk.Label(frame_filtros_hist, text="Data Início (DD-MM-AAAA):").grid(row=0, column=0)
        self.ent_hist_ini = tk.Entry(frame_filtros_hist, width=12)
        self.ent_hist_ini.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.ent_hist_ini.grid(row=0, column=1, padx=5)
        self.ent_hist_ini.bind("<KeyRelease>", self.formatar_data_input)

        # Data Fim
        tk.Label(frame_filtros_hist, text="Data Fim (DD-MM-AAAA):").grid(row=0, column=2)
        self.ent_hist_fim = tk.Entry(frame_filtros_hist, width=12)
        self.ent_hist_fim.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.ent_hist_fim.grid(row=0, column=3, padx=5)
        self.ent_hist_fim.bind("<KeyRelease>", self.formatar_data_input)

        tk.Button(frame_filtros_hist, text="🔍 Filtrar Histórico", bg="#007bff", fg="white",
                command=self.carregar_historico_local).grid(row=0, column=4, padx=10)
        
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
        
        self.tree_hist.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.carregar_historico_local()

    def setup_aba_vendas(self):
        frame_filtros = tk.LabelFrame(self.tab_vendas, text=" Filtros de Venda ", padx=10, pady=10)
        frame_filtros.pack(fill=tk.X, padx=10, pady=5)

        # Coluna 0 e 1: Data Início
        tk.Label(frame_filtros, text="Data Início:").grid(row=0, column=0)
        self.ent_data_ini = tk.Entry(frame_filtros, width=11)
        self.ent_data_ini.insert(0, datetime.now().strftime("%d-%m-%Y")) # Já inicia com data atual
        self.ent_data_ini.grid(row=0, column=1, padx=2)
        # Vincula a máscara automática
        self.ent_data_ini.bind("<KeyRelease>", self.formatar_data_input)
        
        # Coluna 2 e 3: Hora Início
        tk.Label(frame_filtros, text="Hora (HH:MM):").grid(row=0, column=2)
        self.ent_hora_ini = tk.Entry(frame_filtros, width=7)
        self.ent_hora_ini.insert(0, "00:00")
        self.ent_hora_ini.grid(row=0, column=3, padx=2)

        # Coluna 4 e 5: Data Fim
        tk.Label(frame_filtros, text="Data Fim:").grid(row=0, column=4)
        self.ent_data_fim = tk.Entry(frame_filtros, width=11)
        self.ent_data_fim.insert(0, datetime.now().strftime("%d-%m-%Y")) # Já inicia com data atual
        self.ent_data_fim.grid(row=0, column=5, padx=2)
        # Vincula a máscara automática
        self.ent_data_fim.bind("<KeyRelease>", self.formatar_data_input)

        # Coluna 6 e 7: Emitente
        tk.Label(frame_filtros, text="Emitente:").grid(row=0, column=6)
        self.combo_emitente = ttk.Combobox(frame_filtros, values=["156","175","128", "126", "127", "129"], width=8)
        self.combo_emitente.set("127")
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
        
    def gerar_pdf_termico_vendas(self, titulo, dados, periodo, total_geral, resumo_cob, operador=""):
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
    
        c.setFont("Helvetica", 6)
        c.drawCentredString(largura_fita/2, y, f"OPERADOR: {operador}")
        y -= 5 * mm
        
        c.line(5*mm, y, 75*mm, y)
        y -= 5 * mm
        
        

        # Cabeçalho da Tabela de Itens 
        c.setFont("Helvetica-Bold", 5)
        c.drawString(5*mm, y, "COD")
        c.drawString(15*mm, y, "PRODUTO")
        c.drawRightString(55*mm, y, "VENDAS")
        c.drawRightString(65*mm, y, "ESTOQ.")
        c.drawRightString(75*mm, y, "SALDO")
        y -= 4 * mm

        # Listagem de Itens 
        c.setFont("Helvetica", 6)
        for item in dados:
            c.drawString(5*mm, y, str(item[0]))      # CODPROD
            c.drawString(15*mm, y, str(item[1])[:25]) # DESCRIÇÃO
            
            qtd_vendida = f"{float(item[2]):.2f}"
            est_gerencial = f"{float(item[3]):.2f}"
            saldo = f"{float(item[4]):.2f}"
            
            c.drawRightString(55*mm, y, qtd_vendida) # QTD VENDIDA
            c.drawRightString(65*mm, y, est_gerencial) # ESTOQUE GERENCIAL
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


    def imprimir_vendas_oracle(self):
        """Relatório com Estoque Inicial (Lançamento) e Abatimento de Vendas Pós-Alteração"""
        agrupado_operador = {} # {codprod: [desc, qtd_vend_operador_no_periodo]}
        totais_por_cobradora = {}
        valor_total_geral = 0.0
        datas_horas = []
        nome_operador = "" 
        notas_processadas = set()

        filhos = self.tree_vendas.get_children()
        if not filhos:
            messagebox.showwarning("Aviso", "Pesquise as vendas primeiro.")
            return

        # 1. Coleta o que o operador vendeu no período da tela
        for child in filhos:
            v = self.tree_vendas.item(child)["values"]
            if not nome_operador: nome_operador = v[9]
            
            num_nota = v[0]
            if num_nota not in notas_processadas:
                valor_total_geral += float(v[3])
                totais_por_cobradora[str(v[2])] = totais_por_cobradora.get(str(v[2]), 0) + float(v[3])
                notas_processadas.add(num_nota)
            
            if v[4]: datas_horas.append(v[4])
            
            cod_prod, desc_prod, qtd_vend = v[5], v[6], float(v[7])
            
            if cod_prod in agrupado_operador:
                agrupado_operador[cod_prod][1] += qtd_vend
            else:
                agrupado_operador[cod_prod] = [desc_prod, qtd_vend]

        itens_finais = []
        try:
            conn_ora = oracledb.connect(**DB_CONFIG)
            cursor_ora = conn_ora.cursor()
            
            with sqlite3.connect('estoque_gerencial.db') as conn_sql:
                cursor_sql = conn_sql.cursor()
                
                for cod, dados in agrupado_operador.items():
                    desc, q_vend_pelo_operador = dados
                    
                    # 2. Busca a ÚLTIMA alteração manual deste produto
                    cursor_sql.execute("""
                        SELECT quantidade, data_hora 
                        FROM historico_alteracoes 
                        WHERE codprod = ? 
                        ORDER BY data_hora DESC LIMIT 1
                    """, (cod,))
                    res_hist = cursor_sql.fetchone()
                    
                    if res_hist:
                        estoque_inicial = float(res_hist[0])
                        data_da_alteracao = res_hist[1]
                        
                        # 3. Busca VENDAS GLOBAIS desde a alteração até AGORA
                        # Isso garante que o saldo considere saídas de outros caixas também
                        cursor_ora.execute("""
                            SELECT SUM(M.QT) FROM PCMOV M, PCNFSAID F
                            WHERE M.NUMTRANSVENDA = F.NUMTRANSVENDA
                            AND M.CODPROD = :cod AND F.CODFILIAL = 3
                            AND F.DTCANCEL IS NULL
                            AND F.DTHORAAUTORIZACAOSEFAZ > TO_DATE(:dt_alt, 'YYYY-MM-DD HH24:MI:SS')
                        """, {'cod': cod, 'dt_alt': data_da_alteracao})
                        
                        vendas_globais_pos_alteracao = cursor_ora.fetchone()[0] or 0
                        saldo_atual = estoque_inicial - float(vendas_globais_pos_alteracao)
                    else:
                        estoque_inicial = 0.0
                        saldo_atual = 0.0 - q_vend_pelo_operador
                    
                    # No PDF: (Cód, Desc, Venda do Operador, Estoque Inicial Lançado, Saldo Calculado)
                    itens_finais.append((cod, desc, q_vend_pelo_operador, estoque_inicial, saldo_atual))
            
            conn_ora.close()
        except Exception as e:
            messagebox.showerror("Erro de Cálculo", f"Erro: {e}")
            return

        itens_finais.sort(key=lambda x: x[1])
        periodo = f"{min(datas_horas)} até {max(datas_horas)}" if datas_horas else ""

        # Chama a geração do PDF (ajustada para os novos nomes de colunas)
        self.gerar_pdf_termico_vendas(
            titulo="RESUMO DE VENDAS",
            dados=itens_finais,
            periodo=periodo,
            total_geral=valor_total_geral,
            resumo_cob=totais_por_cobradora,
            operador=nome_operador
        )
    # --- LÓGICA DE DADOS ---

    def carregar_historico_local(self):
        """Busca dados convertendo o input brasileiro para o padrão SQLite"""
        dt_ini_raw = self.ent_hist_ini.get().strip()
        dt_fim_raw = self.ent_hist_fim.get().strip()

        try:
            # Converte DD-MM-AAAA para AAAA-MM-DD para o SQLite entender
            dt_ini = datetime.strptime(dt_ini_raw, "%d-%m-%Y").strftime("%Y-%m-%d")
            dt_fim = datetime.strptime(dt_fim_raw, "%d-%m-%Y").strftime("%Y-%m-%d")

            for item in self.tree_hist.get_children():
                self.tree_hist.delete(item)
            
            with sqlite3.connect('estoque_gerencial.db') as conn:
                cursor = conn.cursor()
                query = """
                    SELECT id, codprod, descricao, quantidade, data_hora 
                    FROM historico_alteracoes 
                    WHERE date(data_hora) BETWEEN ? AND ?
                    ORDER BY id DESC
                """
                cursor.execute(query, (dt_ini, dt_fim))
                for row in cursor.fetchall():
                    self.tree_hist.insert("", tk.END, values=row)
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Use DD-MM-AAAA")
        except Exception as e:
            messagebox.showerror("Erro SQLite", f"Erro: {e}")

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

            # 4. Query no Oracle (Adicionado campo de data/hora bruta para cálculo)
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
                E.NOME,
                F.DTHORAAUTORIZACAOSEFAZ -- Campo [10] para lógica de tempo
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
                AND F.DTCANCEL IS NULL
                {filtro_emitente}
            ORDER BY F.DTHORAAUTORIZACAOSEFAZ ASC
            """
            cursor.execute(sql, params)
            vendas = cursor.fetchall()

            # 5. Cruzamento com SQLite e Cálculo de Saldo Respeitando Todas as Vendas
            with sqlite3.connect('estoque_gerencial.db') as conn_sql:
                cursor_sql = conn_sql.cursor()
                
                for row in vendas:
                    codprod = row[5]
                    data_venda_atual = row[10] # Objeto datetime do Oracle
                    
                    # Busca o último lançamento gerencial feito ANTES ou no momento desta venda
                    cursor_sql.execute("""
                        SELECT quantidade, data_hora, descricao 
                        FROM historico_alteracoes 
                        WHERE codprod = ? AND data_hora <= ?
                        ORDER BY data_hora DESC LIMIT 1
                    """, (codprod, data_venda_atual.strftime("%Y-%m-%d %H:%M:%S")))
                    
                    res_hist = cursor_sql.fetchone()
                    
                    if res_hist:
                        # Verifica se o lançamento foi um 'Zerar Gerencial'
                        # O seu sistema grava "ZERADO: [Nome]" ou "ZERADO: Zeramento Geral"
                        if "ZERADO:" in str(res_hist[2]):
                            qtd_inicial_gerencial = 0.0
                        else:
                            qtd_inicial_gerencial = float(res_hist[0])
                            
                        data_hora_estoque = res_hist[1]
                        
                        # O sistema agora vai contar as vendas APENAS a partir deste momento
                        cursor.execute("""
                            SELECT SUM(M.QT)
                            FROM PCMOV M, PCNFSAID F
                            WHERE M.NUMTRANSVENDA = F.NUMTRANSVENDA
                            AND M.CODPROD = :cod
                            AND F.CODFILIAL = 3
                            AND F.DTCANCEL IS NULL
                            AND F.DTHORAAUTORIZACAOSEFAZ > TO_DATE(:dt_estoque, 'YYYY-MM-DD HH24:MI:SS')
                            AND F.DTHORAAUTORIZACAOSEFAZ <= :dt_venda
                        """, {
                            'cod': codprod,
                            'dt_estoque': data_hora_estoque,
                            'dt_venda': data_venda_atual
                        })
                        
                        vendas_totais_no_periodo = cursor.fetchone()[0] or 0
                        saldo_calculado = qtd_inicial_gerencial - float(vendas_totais_no_periodo)
                    else:
                        # Se não houver histórico de estoque, o saldo é apenas a venda negativa
                        qtd_inicial_gerencial = 0.0
                        saldo_calculado = 0.0 - float(row[7])
                    
                    # Prepara a linha para o Treeview (mantendo as colunas originais e adicionando os cálculos)
                    valores_finais = list(row[:10]) + [qtd_inicial_gerencial, saldo_calculado]
                    self.tree_vendas.insert("", tk.END, values=valores_finais)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Erro ao buscar ou cruzar dados: {e}")