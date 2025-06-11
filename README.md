# phispler

![MIT License](https://img.shields.io/badge/license-MIT-yellow)
![Language](https://img.shields.io/badge/language-python-brightgreen)

> (1) 本项目是一款仿制作品，原作为Pigeon Games 鸽游创作的《Phigros》。
>
> (2) 本项目仅为研究学习目的，不可商业使用、违法使用。

## 简单的部分功能介绍

- `main.py`: 谱面模拟器
- `phigros.py`: 还原Phigros游戏界面

## 环境配置

Python 版本: `3.12.8`, 如果你是 Win7 用户, 可尝试 [VxKex](https://github.com/i486/VxKex)

- Windows

```batch
git clone https://github.com/qaqFei/phispler
cd phispler\src
pip install -r requirements.txt
python main.py <chart> [args] [kwargs]
```

- Termux (运行 `main.py` 后访问 `https://qaqfei.github.io/phispler/src/web_canvas.html` 并触发 `touchstart` 连接 `127.0.0.1` 即可)

```bash
curl https://qaqfei.github.io/phispler/src/termux_install.sh -o install.sh
chmod 777 install.sh
./install.sh

cd phispler/src
python main.py <chart> --disengage-webview [args] [kwargs]
```

## 兼容

- [x] phi
- [x] rpe
- [x] pec
- [x] extra
- [x] phira resource pack
