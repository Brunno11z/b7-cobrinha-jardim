# B7 Cobrinha Jardim 3D — Versão 3 (Groq AI, Som & Boca Frontal)

Jogo Python interativo para lives do TikTok com Ursina/Panda3D, visual 3D low poly e formato vertical 720 × 960 pronto para captura no OBS. A cobrinha azul com barriga verde-clara se movimenta de forma fluida e automática, respondendo em tempo real aos presentes e comentários da live.

## 🚀 Novidades desta Versão
1. **Inteligência Artificial Groq (Ultra-Rápida)**: Respostas em menos de 300ms na live usando `llama-3.3-70b-versatile` da Groq Cloud. Também suporta xAI Grok.
2. **Efeitos Sonoros**: Som crocante de mastigar/morder ao comer maçãs (`assets/eat_apple.wav`), som de explosão para bombas (`assets/bomb.wav`) e fanfarra ao completar a meta (`assets/victory.wav`).
3. **Boca Abrindo de Frente**: Abertura anatômica frontal da mandíbula com cavidade bucal vermelha, presas e língua animada, engolindo as maçãs que voam em direção à boca.
4. **Movimentos Incríveis & Crescimento na Tela**: A cobrinha cresce exponencialmente à medida que recebe maçãs, estendendo até 240 anéis tubulares e preenchendo quase toda a tela vertical do OBS em curvas sinuosas hipnóticas.
5. **Nunca Bate Nela Mesma**: A trajetória é uma curva multi-harmônica 3D contínua com desvio vertical suave nos cruzamentos, garantindo que o corpo nunca colida ou trave nele mesmo, ideal para transmissões 24/7 sem interrupções.

---

## 💻 Como Iniciar no Windows

1. Instale o **Python 3.12 (64 bits)**: [python.org/downloads](https://www.python.org/downloads/). Marque "Add Python to PATH".
2. Extraia o ZIP para uma pasta no seu computador.
3. Dê dois cliques em **INSTALAR.bat** (apenas na primeira vez, com internet).
4. Configure sua chave Groq (veja abaixo) ou use as falas locais automáticas.
5. Dê dois cliques em **INICIAR.bat**.
6. O painel abrirá automaticamente em `http://127.0.0.1:8765` (ou pressione `P` no jogo).
7. No **OBS Studio**, adicione uma fonte de **Captura de Jogo** ou **Captura de Janela** e selecione a janela da B7.

---

## 🔑 Configuração da API Groq (Respostas da Cobrinha)

A Groq oferece uma das APIs mais rápidas do mundo, ideal para transmissões ao vivo onde a resposta precisa ser imediata:

1. Crie sua conta gratuita em: https://console.groq.com/
2. Gere uma chave em **API Keys**: https://console.groq.com/keys
3. **Método 1 (Automático via BAT)**:
   - Copie o arquivo `CHAVE_GROQ_EXEMPLO.bat` e renomeie a cópia para `CHAVE_GROQ_LOCAL.bat`.
   - Abra o arquivo com o Bloco de Notas e troque `gsk_SUA_CHAVE_AQUI` pela sua chave da Groq.
   - O `INICIAR.bat` carrega automaticamente esse arquivo!
4. **Método 2 (Pelo Painel Web)**:
   - No painel `http://127.0.0.1:8765`, selecione o provedor **Groq**, cole sua chave no campo **Chave Groq API** e clique em **Salvar Configurações**.

*Observação*: Se você preferir usar o xAI Grok, basta selecionar xAI no painel ou preencher o `CHAVE_GROK_LOCAL.bat`. Se nenhuma chave estiver configurada, a cobrinha usa frases prontas locais divertidas sem custo.

---

## 🎵 Efeitos Sonoros e Áudio

- O jogo vem com sons WAV gerados procedurais na pasta `assets/`:
  - `eat_apple.wav`: som de mordida/crocância de maçã.
  - `bomb.wav`: estrondo de bomba.
  - `victory.wav`: toque festivo de vitória de meta.
- No painel, você pode testar cada som individualmente com os botões **Testar Som Maçã**, **Testar Bomba** e **Testar Vitória**.
- Você pode desativar ou ativar os sons a qualquer momento desmarcando a opção no painel.
- As falas da IA são narradas pelo sintetizador local de voz do Windows (pyttsx3).

---

## 🎁 Configuração de Presentes do TikTok

1. No painel web (`http://127.0.0.1:8765`), cadastre o ID do presente da sua live (ex: Rosa = 5655).
2. Escolha se o presente dá **Maçãs** (aumenta pontuação e faz o corpo crescer) ou **Bomba** (remove pontos com explosão).
3. Defina a quantidade de maçãs por unidade e adicione a imagem do presente se desejar.
4. Clique em **Salvar Presentes**.

### Teclas de atalho para teste (sem live):
- Tecla `1`: envia o presente de maçã.
- Tecla `2`: envia o presente de bomba.
- Tecla `C`: envia um comentário de teste.
- Tecla `P`: abre o painel no navegador.
- Tecla `ESC`: fecha o jogo.

---

## 📱 Conexão com TikTok LIVE

1. No painel, preencha o seu `@nomedeusuario` no campo do TikTok e salve.
2. Seu perfil precisa estar **AO VIVO** no TikTok para a biblioteca conectar.
3. Reinicie o jogo (`INICIAR.bat`). O status da conexão aparecerá no topo do painel.
