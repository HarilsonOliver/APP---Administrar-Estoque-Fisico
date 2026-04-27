# Gestão de Estoque

Sistema especializado para auditoria e controlo de stock híbrido, integrando dados do ERP WinThor (TOTVS/Oracle) com um banco de dados local (SQLite) para gestão de quantidades gerenciais vs. oficiais.

## 🚀 Funcionalidades

- **Integração Oracle (WinThor):** Consulta em tempo real de faturamento, vendas e posições de stock oficial.
- **Controlo Gerencial:** Interface para inserção de quantidades manuais (stock de balcão/conferência) persistidas em SQLite.
- **Relatório de Vendas (Fita Térmica):** Geração de PDF otimizado para impressoras térmicas (80mm) com:
  - Listagem detalhada de produtos.
  - Colunas de Quantidade Vendida, Stock Gerencial e Saldo (Diferença).
  - Resumo financeiro por tipo de cobrança.
  - Identificação do operador e timestamps de autorização da SEFAZ.
- **Auditoria de Alterações:** Histórico de modificações no stock com registo de data, hora e valores anteriores.
- **Interface Intuitiva:** Desenvolvido em Python com Tkinter, focado na produtividade dos operadores.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.13.12
- **Interface Gráfica:** Tkinter
- **Bancos de Dados:** - Oracle Database
  - SQLite (Armazenamento local)
- **Relatórios:** ReportLab (Geração de PDFs de alta precisão)

## 📋 Pré-requisitos

Para executar o projeto, necessita de ter instalado:

1. **Python 3.13.12**
2. **Oracle Instant Client**
3. **Bibliotecas Python:**
   ```bash
   pip install cx_Oracle reportlab
