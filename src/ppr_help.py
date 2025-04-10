HELP_ZH = '''\
使用: main <谱面文件> [<参数>...] [<关键字参数>...]

<参数>
  --debug: 显示webview调试窗口, 并显示判定线位置点
  --fullscreen: 使窗口全屏
  --loop: 自动循环谱面
  --noclicksound: 禁用点击音效
  --render-range-more: 渲染范围更多, 可以渲染出屏幕外, 并显示在屏幕上
  --frameless: 使窗口无边框
  --noautoplay: 禁用自动游玩
  --rtacc: 启用实时准度
  --lowquality: 低画质模式
  --showfps: 显示帧率
  --noplaychart: 不播放谱面, 立即结算
  --enable-controls: 启用rpe格式谱面中的note control类字段, 有极大的性能开销
  --wl-more-chinese: 替换文本为中文 (wl)
  --renderdemand: 按需渲染, 使用 requestAnimationFrame 限制帧率
  --renderasync: 异步渲染, 渲染同时可计算谱面数据
  --enable-jslog: 保留渲染的 JavaScript 代码并输出到文件 (路径为 --jslog-path 参数值)
  --enable-jscanvas-bitmap: 启用渲染时的 BitmapImage, 这会提升许多绘图性能, 但会失去抗锯齿
  --soundapi-downgrade: 降级音频API, 从 DirectSound 降级到 SDL2_mixer
  --nocleartemp: 不清理临时文件
  --disengage-webview: 脱离 WebView
  --nolocalhost: 禁用 localhost 作为内置服务器地址
  --usu169: 使用 16:9 的比例
  --render-video: 渲染视频
  --render-video-autoexit: 渲染视频后自动退出 (前置参数: --render-video)
  --mirror: 谱面镜像
  --disable-watermark: 禁用水印
  
<关键字参数>
  --combotips <字符串>: 设置连击提示文本
  --random-block-num <整数>: 打击特效随机块数量
  --scale-note <数字>: 设置音符缩放
  --size <整数> <整数>: 设置窗口大小
  --render-range-more-scale <数字>: 设置渲染范围更多的缩放. (前置参数: --render-range-more)
  --window-host <整数-窗口句柄>: 设置窗口宿主 窗口句柄
  --lowquality-scale <浮点数>: 设置低画质渲染缩放 默认: 2.0
  --res <资源路径>: 设置资源路径
  --speed <数字>: 设置谱面速度
  --clickeffect-randomblock-roundn <数字>: 设置打击效果方块的圆角系数 (0.0 = 方, 0.5 = 圆), 默认 = 0.0
  --clicksound-volume <数字>: 设置打击音效音量 (0.0 = 无声, 1.0 = 原音), 默认 = 1.0
  --musicsound-volume <数字>: 设置音乐音量 (0.0 = 无声, 1.0 = 原音), 默认 = 1.0
  --lowquality-imjscvscale-x <数字>: 设置低画质渲染缩放 (js调用层). 默认 = 1.0
  --phira-chart <谱面ID>: 使用 phira 谱面. (使用 phira 谱面时, 谱面文件将不会被加载)
  --phira-chart-save <字符串>: 保存 phira 谱面. (前置参数: --phira-chart)
  --skip-time <数字>: 播放时跳过的时间. 默认 = 0.0
  --jslog-path <文件路径字符串>: 设置 JavaScript 代码输出路径 (前置参数: --enable-jslog)
  --lowquality-imjs-maxsize <数字>: 设置低画质渲染最大尺寸 (js调用层). 默认 = 256
  --rpe-texture-scalemethod <by-width或by-height>: 设置 rpe 谱面纹理缩放方法. 默认 = by-width
  --extended <扩展文件>: 启用扩展
  --render-video-fps <数字>: 设置渲染视频的帧率, 默认 = 60.0 (前置参数: --render-video)
  --render-video-fourcc <字符串>: 设置生成视频编码 默认 = mp4v (前置参数: --render-video)
  --render-video-savefp <文件路径字符串>: 设置渲染视频的保存路径 (前置参数: --render-video)
  --rpeversion <数字>: 手动指定 rpe 谱面版本

<环境变量>
  ENABLE_JIT: 启用 JIT, 警告: 这会使启动慢 (默认: 0, 环境变量值: ["0", "1"])
'''
