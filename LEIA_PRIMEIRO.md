# 🐍 B7 • Cobrinha Jardim 3D (Versão 3.1)

Jogo 3D completo em Python / Ursina para lives do TikTok e OBS Studio (formato vertical 720x960), com movimentação dinâmica de jogador humano, boca 3D articulada que abre de frente, efeitos sonoros crocantes ao comer maçãs, integração com API Groq ultra-rápida e painel web responsivo em tempo real.

---

## 🚀 Novidades desta Atualização (V3.1)

1. **Painel Web 100% Responsivo e Sincronizado**:
   - Correção total de comunicação CORS e JavaScript no `panel.html`.
   - Botões de **Enviar Presente**, **Enviar Comentário**, **Testar Sons** e **Zerar Rodada** respondem instantaneamente no jogo.
2. **HUD Limpo sem Texto no Topo**:
   - Removido o texto "B7 | COBRINHA JARDIM" do topo para deixar a captura do OBS e live muito mais limpa e profissional.
   - Barra de pontuação com maçãs atuais, meta e vitórias mantida com destaque discreto e elegante.
3. **Movimentos como se Fosse Alguém Jogando**:
   - A cobrinha agora caça ativamente maçãs espalhadas pelo jardim 3D.
   - Curvas dinâmicas com inércia, ondulação serpenteante lateral e desvio inteligente das cercas.
   - **Nunca bate nela mesma**: algoritmo de evasão ativa do próprio corpo e elevação em camadas verticais nos cruzamentos, garantindo 100% de fluidez contínua sem game-over ou travamentos na live.
4. **Boca Articulada que Abre de Frente**:
   - Ao se aproximar das maçãs ou mastigar presentes, a mandíbula inferior desce e gira para frente, revelando a cavidade interna vermelha, presas brancas e língua bifurcada animada.
5. **Corpo que Preenche a Tela**:
   - O corpo tubular 3D é reconstruído continuamente a partir da trajetória percorrida pelo jogador e cresce de 3.6 até mais de 30 unidades de comprimento conforme acumula maçãs, preenchendo quase toda a tela vertical do OBS.
6. **Efeitos Sonoros Nativos**:
   - Sons WAV inclusos: mordida crocante de maçã (`eat_apple.wav`), explosão de bomba (`bomb.wav`) e fanfarra de vitória (`victory.wav`).

---

## ⚡ Como Rodar o Jogo

1. Abra a pasta do jogo.
2. Se for a primeira vez, dê dois cliques em **`INSTALAR.bat`**.
3. (Opcional) Edite **`CHAVE_GROQ_LOCAL.bat`** e insira sua chave da Groq (`gsk_...`). Você também pode colocar a chave diretamente no painel web.
4. Dê dois cliques em **`INICIAR.bat`** para abrir o jogo e o painel web.
5. No navegador, acesse **`http://localhost:8765`** para controlar tudo.

---

## 🎮 Teclas de Atalho no Teclado
- **1**: Simula recebimento de 1 Maçã (+1).
- **2**: Simula bomba (-10 maçãs).
- **C**: Simula comentário de espectador na live.
- **P**: Abre o painel web de controle no navegador.
- **ESC**: Fecha o jogo.
