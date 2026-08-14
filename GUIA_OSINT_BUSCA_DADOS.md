# 🛡️ Manual Definitivo de OSINT & Busca de Dados Públicos
> **Plataforma GEONIV 3D — Guia de Inteligência em Fontes Abertas (OSINT), GEOINT e Segurança Cibernética**

---

## 🧭 O que é OSINT (Open Source Intelligence)?

**OSINT** (*Open Source Intelligence*) é a disciplina de coletar, analisar e correlacionar dados disponíveis publicamente (motores de busca, registros públicos, redes sociais, certificados SSL, registros DNS, metadados de arquivos e bancos de dados abertos) para produzir inteligência acionável.

Na **Segurança Cibernética**, o OSINT é utilizado de forma defensiva para:
1. **Mapeamento da Superfície de Ataque (*Attack Surface Management*):** Descobrir quais dados, e-mails, servidores e subdomínios da sua organização estão expostos na internet.
2. **Prevenção de Fraudes e Engenharia Social:** Identificar vazamentos de credenciais corporativas antes que criminosos as usem.
3. **Threat Intelligence & Resposta a Incidentes:** Investigar IPs maliciosos, criadores de malware e infraestruturas de phishing.

---

## 🏆 As Melhores Ferramentas por Categoria

Abaixo está o ranking das ferramentas mais eficientes, como funcionam e quando utilizá-las:

---

### 1. 📩 E-mail & Contas (Gmail / Outlook / Corporativo)

| Ferramenta | Tipo | Link / Fonte | Para que serve? |
| :--- | :--- | :--- | :--- |
| **Holehe** | CLI (Python) | [github.com/megadose/holehe](https://github.com/megadose/holehe) | Verifica se um e-mail possui cadastro ativo em mais de **120 serviços web** (Twitter, Instagram, Discord, Mercado Livre, etc.) sem alertar o usuário. |
| **Epios** | Web | [epios.klaz.dev](https://epios.klaz.dev/) | Especialista em **contas Google/Gmail**. Revela avaliações feitas no Google Maps, ID do usuário (Gaia ID), álbuns públicos e agenda. |
| **Hunter.io** | Web / API | [hunter.io](https://hunter.io/) | Descobre o **padrão de e-mails corporativos** de empresas (ex: `primeironome.sobrenome@empresa.com`) e lista e-mails públicos por domínio. |
| **EmailRep.io** | API / Web | [emailrep.io](https://emailrep.io/) | Analisa a **reputação e confiabilidade** do e-mail (se é conta descartável, idade do domínio, presença em listas de spam). |
| **theHarvester** | CLI (Python) | [github.com/laramies/theHarvester](https://github.com/laramies/theHarvester) | Coleta massiva de e-mails corporativos, nomes e hosts indexados em buscadores (Google, Bing, Yahoo). |

---

### 2. 📱 Telefonia & Contatos Telefônicos (Phone OSINT)

| Ferramenta | Tipo | Link / Fonte | Para que serve? |
| :--- | :--- | :--- | :--- |
| **PhoneInfoga** | CLI / Web | [github.com/sundowndev/phoneinfoga](https://github.com/sundowndev/phoneinfoga) | Scanner avançado para validação de número, código de país, operadora original e automação de Google Dorks para achar menções do número. |
| **Truecaller** | Web / App | [truecaller.com](https://www.truecaller.com/) | Maior base colaborativa do mundo para identificação de **nome do titular** e histórico de chamadas spam. |
| **Sync.me** | Web / App | [sync.me](https://sync.me/) | Cruza a agenda de contatos com perfis em redes sociais para associar nomes e fotos ao número. |
| **Tellows Brasil** | Web | [tellows.com.br](https://www.tellows.com.br/) | Focado em território nacional para identificar chamadas de **golpes, telemarketing abusivo** e spoofing telefônico. |
| **WhatsApp Direct** | Web / API | `https://wa.me/55NUMERO` | Permite verificar se o número possui conta de WhatsApp ativa e visualizar a foto pública de perfil. |

---

### 3. 👤 Nomes de Usuário, Perfis & Redes Sociais

| Ferramenta | Tipo | Link / Fonte | Para que serve? |
| :--- | :--- | :--- | :--- |
| **Sherlock** | CLI (Python) | [github.com/sherlock-project/sherlock](https://github.com/sherlock-project/sherlock) | Busca a existência de um **mesmo apelido (username)** em mais de 400 plataformas sociais, fóruns e sites. |
| **WhatsMyName** | Web | [whatsmyname.app](https://whatsmyname.app/) | Interface web ultrarrápida para testar usernames categorizados (jogos, tecnologia, redes adultas, compras). |
| **Maigret** | CLI (Python) | [github.com/soxoj/maigret](https://github.com/soxoj/maigret) | Evolução do Sherlock: extrai biografias, fotos, IDs e gera um **grafo de conexões** entre contas do mesmo usuário. |
| **Blackbird** | CLI (Python) | [github.com/p1ngul1n0/blackbird](https://github.com/p1ngul1n0/blackbird) | Alternativa moderna e veloz para checagem de usernames com suporte a exportação em PDF e JSON. |

---

### 4. 🌍 Imagens, Metadados & Geolocalização (GEOINT)

| Ferramenta | Tipo | Link / Fonte | Para que serve? |
| :--- | :--- | :--- | :--- |
| **GeoSpy AI** | Web / IA | [geospy.ai](https://geospy.ai/) | **Inteligência Artificial** que analisa vegetação, relevo, placas, arquitetura e clima da foto para prever as coordenadas aproximadas. |
| **Yandex Visual** | Web | [yandex.com/images/search](https://yandex.com/images/search) | O motor mais potente para correspondência de fachadas de prédios, roupas, paisagens e reconhecimento facial público. |
| **Google Lens** | Web / App | [lens.google.com](https://lens.google.com/) | Excelente para identificar produtos, espécies de plantas, logotipos e marcos históricos. |
| **SunCalc** | Web | [suncalc.org](https://www.suncalc.org/) | Calcula a posição do sol e **sombras** em qualquer data/hora histórica para validar o momento exato em que uma foto foi tirada. |
| **ExifTool** | CLI | [exiftool.org](https://exiftool.org/) | O padrão da indústria forense para leitura e extração de todos os metadados EXIF, IPTC e XMP de imagens e documentos. |
| **Overpass Turbo** | Web | [overpass-turbo.eu](https://overpass-turbo.eu/) | Realiza buscas avançadas no OpenStreetMap por combinações de elementos físicos (ex: *igreja a 50m de um trilho de trem*). |

---

### 5. 🌐 Infraestrutura, Domínios, Subdomínios & Redes

| Ferramenta | Tipo | Link / Fonte | Para que serve? |
| :--- | :--- | :--- | :--- |
| **Shodan** | Web / CLI | [shodan.io](https://www.shodan.io/) | Motor de busca para dispositivos conectados: servidores, roteadores, bancos de dados abertos e portas expostas. |
| **crt.sh** | Web | [crt.sh](https://crt.sh/) | Consulta os logs mundiais de **Transparência de Certificados SSL**, revelando subdomínios ocultos (`admin.`, `vpn.`, `dev.`). |
| **SecurityTrails** | Web | [securitytrails.com](https://securitytrails.com/) | Histórico completo de DNS e Whois para ver quem foi o dono antigo e quais IPs o domínio já apontou. |
| **DNSDumpster** | Web | [dnsdumpster.com](https://dnsdumpster.com/) | Mapeamento e visualização gráfica de servidores DNS, MX e registros A de uma organização. |
| **Wayback Machine**| Web | [web.archive.org](https://web.archive.org/) | Histórico de páginas e sites antigos, recuperando arquivos e informações que foram apagadas do ar. |
| **BuiltWith** | Web | [builtwith.com](https://builtwith.com/) | Identifica quais tecnologias, frameworks, CDNs e servidores alimentam qualquer site na web. |

---

### 6. 🔓 Vazamentos de Dados & Threat Intelligence

| Ferramenta | Tipo | Link / Fonte | Para que serve? |
| :--- | :--- | :--- | :--- |
| **Have I Been Pwned?** | Web | [haveibeenpwned.com](https://haveibeenpwned.com/) | Consulta se um e-mail ou telefone esteve presente em grandes vazamentos de dados públicos mundiais. |
| **VirusTotal** | Web / API | [virustotal.com](https://www.virustotal.com/) | Analisador com mais de 70 motores de antivírus para checar hashes forenses (MD5, SHA-256), domínios e IPs suspeitos. |

---

## 🎯 Fluxos Práticos de Investigação (Pivôs OSINT)

### Fluxo 1: Investigando a partir de um E-mail
1. **Validação e Reputação:** Use `EmailRep.io` para checar se o domínio é corporativo ou temporário.
2. **Mapeamento de Contas:** Execute o `Holehe` para descobrir onde esse e-mail possui cadastro (ex: GitHub, Spotify, Twitter).
3. **Pivô Google:** Se for `@gmail.com`, consulte no `Epios` para descobrir o nome real e reviews públicos no Google Maps.
4. **Verificação de Vazamentos:** Consulte o `HaveIBeenPwned` para checar incidentes de segurança prévios.

### Fluxo 2: Investigando a partir de um Número de Telefone
1. **Análise de Prefixo e DDD:** Utilize o GEONIV ou `PhoneInfoga` para determinar Estado, Cidade e operadora original.
2. **Identificação de Titularidade:** Consulte no `Truecaller` e `Sync.me` para obter o nome atribuído na agenda comunitária.
3. **Verificação de Presença:** Abra no `WhatsApp Direct` (`wa.me/55...`) e Telegram para checar se a conta está ativa e se há foto pública.
4. **Histórico de Denúncias:** Busque no `Tellows Brasil` para saber se há queixas de golpes vinculadas ao número.

### Fluxo 3: Investigando a partir de uma Imagem
1. **Extração de Metadados:** Passe a foto pelo extrator forense do **GEONIV** para recuperar câmera, data original e coordenadas GPS nativas.
2. **Caso NÃO tenha GPS:**
   - Analise se o nome do arquivo tem pistas (ex: `IMG-...-WA` do WhatsApp indica que o GPS foi removido na compressão).
   - Use o **GeoSpy AI** para obter uma estimativa de país e relevo.
   - Use o **Yandex Visual** e **Google Lens** para encontrar a fachada exata ou outros ângulos do local.
   - Se houver sombras visíveis, use o **SunCalc** para aferir a hora aproximada da foto.

---

## 🔎 Dorks Essenciais (Google Hacking)

Operadores avançados de busca para localizar arquivos e páginas expostas:

```text
# Encontrar PDFs expostos em um domínio específico com dados sensíveis
site:alvo.com.br filetype:pdf "cpf" OR "relatório"

# Encontrar planilhas Excel públicas
site:alvo.com.br filetype:xlsx OR filetype:csv

# Encontrar diretórios com listagem aberta de arquivos (Directory Listing)
intitle:"index of /" "parent directory" site:alvo.com.br

# Localizar menções a um e-mail ou número de telefone exato
"alvo@email.com" OR "(11) 98765-4321"
```

---

## ⚖️ Aspectos Legais, Ética e LGPD

> [!IMPORTANT]
> **Princípio da Finalidade e Legalidade:**
> - O uso de OSINT deve ser estritamente **defensivo, acadêmico, de pesquisa ou autorizado** (como auditorias de segurança e proteção de infraestrutura própria).
> - O tratamento de dados pessoais no Brasil é regulamentado pela **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)**. Dados públicos não significam autorização para uso abusivo, assédio ou invasão de privacidade.
> - O acesso não autorizado a sistemas protegidos ou quebra de senhas é crime previsto no Artigo 154-A do Código Penal Brasileiro.

---

*Manual integrado à plataforma GEONIV 3D.*
