import const

HELP_ZH = '''\
使用: main <谱面文件> [<参数>...] [<关键字参数>...]

<参数>
{$ARGS$}
  
<关键字参数>
{$KWARGS$}

<环境变量>
  ENABLE_JIT: 启用 JIT, 警告: 这会使启动慢 (默认: 0, 环境变量值: ["0", "1"])
''' \
.replace("{$ARGS$}", "\n".join(map(lambda x: f"  --{x[1]}: {x[0]}", const.PPR_CMDARGS["args"]))) \
.replace("{$KWARGS$}", "\n".join(map(lambda x: f"  --{x[1]} <{x[3]}>{"" if x[2] is None else f" default = {x[2]}"}: {x[0]}", const.PPR_CMDARGS["kwargs"])))
