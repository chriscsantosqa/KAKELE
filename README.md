# Kakele Bot 🤖 - [YT](https://youtu.be/6NhE3GDJ5aw)

O Kakele Bot é gratuito e open source.
Bot leve e simples, com reconhecimento óptico de caracteres (OCR).

## Next-generation bootstrap

For the current next-generation bootstrap flow, use these documents first:
- `docs/OPERATIONAL_READINESS_PACKAGE.md`
- `docs/FIRST_USE_CHECKLIST.md`
- `docs/GPT_VISION_SETUP.md`
- `docs/USAGE_READINESS_AND_GPT_VISION_AGENT.md`

These documents describe:
- controlled first usage
- baseline validation
- ROI/OCR calibration
- AI-assisted visual diagnosis
- GO / NO-GO criteria

### Memory-first capture (kakele.exe)

O runtime next-gen agora suporta leitura direta de memória do processo `kakele.exe` (Windows), com fallback visual via OCR quando a memória não estiver disponível.

Configure no perfil (`profiles/<nome>.json`):

```json
{
  "memory": {
    "enabled": true,
    "prefer_for_healing": true,
    "prefer_for_target": true,
    "prefer_for_cavebot": true,
    "process_name": "kakele.exe",
    "addresses": {
      "hp": "0x00000000",
      "max_hp": "0x00000000",
      "mp": "0x00000000",
      "max_mp": "0x00000000",
      "x": "0x00000000",
      "y": "0x00000000",
      "z": "0x00000000",
      "has_target": "0x00000000",
      "target_id": "0x00000000"
    }
  }
}
```

> Substitua os endereços pelos offsets válidos da sua versão do client.

| Descrição                                                                                          | Imagem |
|----------------------------------------------------------------------------------------------------| --- |
| Iniciando o Bot por um login específico de algum usuário previamente cadastrado no banco de dados. | ![start](comp_out/samples/login.png) |
| Kakele Bot com todas as funcionalidades disponíveis até o momento.                                 | ![help](comp_out/samples/bot.png) |


## Principais bibliotecas utilizadas

- [Pytesseract](https://pypi.org/project/pytesseract/)
- [OpenCV](https://pypi.org/project/opencv-python/)
- [PyQt6](https://pypi.org/project/PyQt6/)

:snowflake: Bonus: As imagens são processadas em tempo de execuçao, sem precisar salvar.

## Estrutura do Projeto

O projeto está dividido em três partes principais:

- **comp_out/**: Contém os arquivos que são necessários para o funcionamento do bot, e não precisam ser compilados.
- **forms/**: Contém os arquivos de formulários do bot.
- **system/**: Contém os arquivos de funcionamento do bot.

``` shell
KL-Bot/
├── comp_out/
│   ├── recursos/
│   │   └── kake_icon2.ico
│   ├── samples/
│   │   └── ...
│   ├── targets/
│   │   └── enemy.png
│   ├── tesseract/
│   │   └── ...
├── forms/
│   ├── bot_form.ui
│   ├── bot_window_ui.py
│   ├── login_form.ui
│   └── login_window_ui.py
├── system/
│   ├── downloads.py
│   ├── features.py
│   ├── healing.py
│   └── hunt.py
├── hunt.json
├── kakelebot.py
├── login.py
├── README.md
├── requirements.txt
└── LICENSE
```

## Funcionalidades do bot

### :crossed_swords: Hunt

- [x] Ataque automático
- [x] Movimentação automática do personagem



- _A movimentação do personagem não buga quando um jogador ou monstro fica na frente dele_.

- _Movimente o personagem com teclas de direção pausadamente (sem pressionar a tecla por muito tempo)._

- _Pare o personagem no mesmo lugar que iniciou a movimentação (waypoint)._

### :heart: Healing

- [x] Curar personagem automaticamente (Vida e Mana)

### :gear: Outros

- [x] Aceleração do personagem

## Funcionalidades internas do bot

- [x] Definição de teclas de atalho
- [x] Definição de tempo de espera entre ações
- [x] Funcionamento do bot somente quando o jogo estiver em primeiro plano



## Como instalar?

### Instalando o Python

Primeiro, você precisa instalar o Python 3.6 ou superior. Você pode baixar o Python [aqui](https://www.python.org/downloads/).

### Instalando o Kakele Bot

Agora, você precisa clonar o repositório do Kakele Bot. Para isso, abra o terminal e digite:

`git clone https://github.com/marcellobatiista/KL-Bot.git && cd KL-Bot`

`pip install -r requirements.txt`

### Iniciando o Kakele Bot

Agora, você precisa iniciar o Kakele Bot. Para isso, abra o terminal e digite:

`python3 main.py`

### Gerando o executável

Você pode gerar um executável para o Kakele Bot. Para isso, abra o terminal e digite:

`pyinstaller --noconfirm --onefile --windowed --add-data "C:/CAMINHO/PARA/PASTA/system;system/" --add-data "C:/CAMINHO/PARA/PASTA/forms;forms/"  "C:/CAMINHO/PARA/ARQUIVO/main.py"`

### Iniciando o executável

Agora, você precisa iniciar o Kakele Bot. Para isso, coloque o `kakele.exe` ao lado da pasta `comp_out/` assim e executar:

``` shell
PASTA_QUALQUER/
├── comp_out/
└── main.exe
```

## Como contribuir?

Você pode contribuir com o Kakele Bot abrindo uma [issue](https://github.com/marcellobatiista/KL-Bot/issues)
:bug: **_Bug Report_** ou um [pull request](https://github.com/marcellobatiista/KL-Bot/pulls) 
:sparkles: **_New Feature_** no GitHub.

## Licença

O Kakele Bot é licenciado sob a [licença MIT](LICENSE) :page_facing_up: License.

## Créditos

O Kakele Bot foi feito por [@Marcelo](https://www.instagram.com/marcellobatiista).
