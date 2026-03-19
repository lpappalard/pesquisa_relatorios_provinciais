# pesquisa_relatorios_provinciais

## Setup
1. Crie e ative o venv:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode localmente:
   ```bash
   streamlit run app_busca_2026.py
   ```

## Deploy no Streamlit Cloud
1. Vá em https://streamlit.io/cloud e entre com sua conta GitHub.
2. Clique em “New app”.
3. Escolha o repositório `lpappalard/pesquisa_relatorios_provinciais`.
4. Branch: `main`; File: `app_busca_2026.py`.
5. Clique em Deploy.

### Atualizar app existente
1. Edite `app_busca_2026.py` localmente.
2. Commit + push:
   ```bash
   git add app_busca_2026.py
   git commit -m "Atualiza app"
   git push
   ```
3. O Streamlit Cloud reimplanta automaticamente no app existente.

Se quiser, adicione o link público do app no README para compartilhamento rápido.

