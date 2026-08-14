# 💻 Guia Completo: Ferramentas OSINT Locais (100% Gratuitas e Sem Paywall)
> **Como instalar, rodar no terminal/Docker e quais dados cada ferramenta extrai sem depender de assinaturas ou planos pagos.**

---

## 🧭 Por que usar ferramentas locais em vez de sites comerciais?

A maioria dos sites comerciais (Truecaller, Hunter, etc.) impõe limites de créditos diários ou esconde os dados completos atrás de assinaturas caras. 

As ferramentas **Open Source (Código Aberto)** rodam diretamente no seu computador (Windows, Linux ou Mac), não possuem limite de buscas, não cobram mensalidade e garantem a sua privacidade (suas investigações não ficam salvas nos servidores de terceiros).

---

## 📋 Índice das Ferramentas Locais

1. [PhoneInfoga (Telefonia, Operadoras, VoIP e Dorking)](#1-phoneinfoga-telefonia)
2. [Holehe (Varredura de E-mails em +120 Serviços)](#2-holehe-e-mail--contas)
3. [GHunt (Investigação Profunda de Contas Google / Gmail)](#3-ghunt-google--gmail)
4. [Sherlock (Busca de Username em +400 Redes Sociais)](#4-sherlock-nomes-de-usuário)
5. [Maigret (Dossiês Completos e Grafos de Identidade)](#5-maigret-dossiê-avançado-de-perfil)
6. [theHarvester (Coleta de E-mails e Subdomínios Corporativos)](#6-theharvester-reconhecimento-corporativo)
7. [ExifTool (Extração Forense de Metadados e GPS em Arquivos)](#7-exiftool-metadados-e-geoint)

---

## 1. 📱 PhoneInfoga (Telefonia)

O PhoneInfoga é uma das ferramentas mais consagradas para reconhecimento de números internacionais.

### 📊 Que dados ele mostra?
- **País, DDD e Formato Internacional (E.164)**.
- **Operadora Original da Linha**.
- **Tipo de Linha:** Móvel (celular), Fixa ou **VoIP** (números descartáveis de internet usados por golpistas).
- **Google Dorks Automatizados:** Links diretos de busca para encontrar o número em PDFs expostos, processos jurídicos, cadastros de empresas e anúncios.

---

### ⚙️ Como Instalar e Rodar no Windows / Linux

#### Opção A: Executável Direto (Não precisa instalar nada)
1. Acesse os [Releases Oficiais do PhoneInfoga](https://github.com/sundowndev/phoneinfoga/releases).
2. Baixe o arquivo `.zip` correspondente ao seu sistema (ex: `phoneinfoga_Windows_x86_64.zip` para Windows).
3. Extraia o arquivo `phoneinfoga.exe` para uma pasta.
4. Abra o **PowerShell** ou **Prompt de Comando** nessa pasta e execute:
   ```powershell
   # Scan direto no terminal
   .\phoneinfoga.exe scan -n "+5511987654321"

   # Ou iniciar a Interface Web no seu navegador
   .\phoneinfoga.exe serve -p 8080
   ```
   *Se usar o comando `serve`, abra `http://localhost:8080` no navegador.*

#### Opção B: Rodar via Docker
```bash
docker run -it --rm -p 8080:8080 sundowndev/phoneinfoga serve
```

---

## 2. 📩 Holehe (E-mail & Contas)

O **Holehe** verifica onde um endereço de e-mail está cadastrado utilizando rotas públicas de recuperação de senha de mais de 120 serviços web, sem enviar alertas de segurança nem emails para o alvo.

### 📊 Que dados ele mostra?
- Confirmação de cadastro ativo em plataformas como: **Instagram, Twitter/X, Discord, Spotify, Mercado Livre, Samsung, Adobe, Deliveroo, GitHub, ProtonMail, Telegram, etc.**
- Ajuda a descobrir quais serviços a pessoa utiliza apenas a partir do e-mail.

---

### ⚙️ Como Instalar e Rodar (Requer Python)

1. Certifique-se de ter o [Python 3](https://www.python.org/) instalado.
2. Abra o terminal e instale com o comando:
   ```bash
   pip install holehe
   ```
3. Para executar uma busca:
   ```bash
   holehe alvo@email.com
   ```
4. **Legenda do resultado:**
   - `[+] Verde:` Conta cadastrada e confirmada no site.
   - `[-] Vermelho:` E-mail não encontrado no serviço.
   - `[x] Cinza:` O site bloqueou a requisição temporariamente.

---

## 3. 🔍 GHunt (Google & Gmail OSINT)

O **GHunt** é a ferramenta definitiva para auditar e investigar contas do ecossistema Google/Gmail.

### 📊 Que dados ele mostra?
- **Nome Real e Foto de Perfil em Alta Resolução**.
- **Gaia ID** (Identificador numérico exclusivo da conta Google).
- **Google Maps Reviews:** Locais, restaurantes e lojas que o usuário avaliou publicamente (permitindo mapear cidades por onde a pessoa passou).
- **Google Agenda Público**.
- **Canal do YouTube e Álbuns públicos de fotos**.
- **Modelo de celular / aplicativo** (caso tenha postado avaliações pelo Google Play).

---

### ⚙️ Como Instalar e Rodar

1. No terminal:
   ```bash
   pip install ghunt
   ```
2. **Configuração de Cookies (Necessário para a API do Google):**
   - Execute:
     ```bash
     ghunt login
     ```
   - O GHunt abrirá uma extensão no navegador para capturar os cookies de uma conta Google secundária (recomendado usar uma conta de pesquisa/sock puppet).
3. Para investigar o Gmail alvo:
   ```bash
   ghunt email alvo@gmail.com
   ```

---

## 4. 👤 Sherlock (Nomes de Usuário)

O **Sherlock** busca simultaneamente a presença de um mesmo apelido (handle/username) em mais de 400 redes sociais, fóruns e sites.

### 📊 Que dados ele mostra?
- Lista com os links diretos para os perfis públicos existentes com aquele nome de usuário (ex: `github.com/usuario`, `instagram.com/usuario`, `twitch.tv/usuario`, `steamcommunity.com/id/usuario`, etc.).

---

### ⚙️ Como Instalar e Rodar

1. Baixe o código pelo Git ou instale via pip:
   ```bash
   # Via pip
   pip install sherlock-project
   ```
2. Para executar:
   ```bash
   sherlock nomedeusuario
   ```
3. Para salvar os resultados em um arquivo de texto:
   ```bash
   sherlock nomedeusuario -o resultado_alvo.txt
   ```

---

## 5. 🕸️ Maigret (Dossiê Avançado de Perfil)

O **Maigret** é uma evolução direta do Sherlock com recursos avançados de mineração de dados.

### 📊 Que dados ele mostra?
- Além de verificar a existência do perfil, ele **baixa a foto de perfil, lê a biografia, extrai IDs internos e conexões entre contas**.
- Gera relatórios completos em formato **HTML**, **PDF** e **JSON**.
- Monta um **grafo visual** interativo ligando todas as redes sociais do mesmo indivíduo.

---

### ⚙️ Como Instalar e Rodar

1. Instalação via pip:
   ```bash
   pip install maigret
   ```
2. Execução gerando relatório em HTML:
   ```bash
   maigret nomedeusuario --html
   ```
   *Um arquivo `.html` será gerado na pasta com um painel visual completo e links clicáveis.*

---

## 6. 🌐 theHarvester (Reconhecimento Corporativo)

O **theHarvester** é a ferramenta padrão em testes de intrusão defensivos e auditorias de superfície de ataque corporativa.

### 📊 Que dados ele mostra?
- Lista de todos os e-mails públicos vinculados a um domínio (ex: `@empresa.com.br`).
- Nomes e cargos de colaboradores indexados no LinkedIn e Google.
- Subdomínios e IPs pertencentes à empresa.

---

### ⚙️ Como Instalar e Rodar

1. Instalação:
   ```bash
   pip install theHarvester
   ```
2. Executar busca varrendo motores de busca (Google, Bing, Yahoo, DuckDuckGo):
   ```bash
   theHarvester -d empresa.com.br -b all -l 500
   ```

---

## 7. 📸 ExifTool (Metadados Forenses & GEOINT)

Desenvolvido por Phil Harvey, o **ExifTool** é o padrão mundial da perícia digital para leitura de metadados em imagens, PDFs e vídeos.

### 📊 Que dados ele mostra?
- **Coordenadas GPS exatas** (Latitude, Longitude e Altitude).
- **Modelo e fabricante da câmera/celular** (ex: *iPhone 14 Pro, Samsung Galaxy S23*).
- **Data e Hora original da captura** (com fuso horário).
- **Configurações da lente:** Distância focal, abertura ISO, tempo de exposição.
- **Software utilizado:** Se a imagem foi alterada no Photoshop, Lightroom, GIMP ou Canva.

---

### ⚙️ Como Instalar e Rodar

#### No Windows:
1. Acesse [exiftool.org](https://exiftool.org/).
2. Baixe o pacote `exiftool-XX.XX.zip`.
3. Extraia o arquivo e renomeie `exiftool(-k).exe` para `exiftool.exe`.
4. Mova para uma pasta no seu computador e execute no terminal:
   ```cmd
   exiftool.exe foto_suspeita.jpg
   ```

#### Apenas coordenadas GPS e Câmera:
```cmd
exiftool.exe -GPSPosition -Model -CreateDate foto_suspeita.jpg
```

---

## 🚀 Resumo Comparativo das Ferramentas Locais

| Ferramenta | Alvo Principal | Linguagem / Requisito | Gera Interface Gráfica? |
| :--- | :--- | :--- | :---: |
| **PhoneInfoga** | Telefone | Go / Binário `.exe` ou Docker | ✅ Sim (`serve -p 8080`) |
| **Holehe** | E-mail | Python (`pip`) | ❌ Terminal colorido |
| **GHunt** | Gmail / Google | Python (`pip`) | ❌ Terminal estruturado |
| **Sherlock** | Username | Python (`pip`) | ❌ Terminal + Arquivo TXT |
| **Maigret** | Username | Python (`pip`) | ✅ Relatório em HTML/PDF |
| **theHarvester**| Domínio / Empresa | Python (`pip`) | ✅ Exporta HTML/JSON |
| **ExifTool** | Imagens / Arquivos | C / Binário `.exe` | ❌ Linha de comando |

---

## 🛡️ Dica de Segurança & Ambiente Isolado
Para rodar essas ferramentas sem alterar o seu ambiente principal do Windows:
- Utilize o **WSL2 (Windows Subsystem for Linux)** ou **Docker Desktop**.
- Crie um ambiente virtual em Python para não misturar dependências:
  ```bash
  python -m venv osint_env
  # No Windows:
  .\osint_env\Scripts\activate
  # No Linux/Mac:
  source osint_env/bin/activate
  ```
