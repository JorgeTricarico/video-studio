import subprocess

FFMPEG = r"C:\Users\admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
VIDEO = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\02_Entrevistas_Completas\Entrevista_Johanna_AM530.mp4"

# Opción 1: Studio Split Vertical (Fondo difuminado 1080x1920 + video centrado 1080x608 con overlay)
cmd1 = [
    FFMPEG, "-y", "-ss", "120", "-i", VIDEO,
    "-filter_complex",
    "[0:v]scale=270:480,boxblur=25:2,scale=1080:1920,setsar=1:1[bg];"
    "[0:v]scale=1080:608,setsar=1:1[fg];"
    "[bg][fg]overlay=0:340[out]",
    "-map", "[out]", "-vframes", "1", "-q:v", "2",
    "assets/test_framing_1_split.jpg"
]
subprocess.run(cmd1)

# Opción 2: Enfoque en Presentadora + Lower-third (crop=1080:1080:300:0 sobre fondo difuminado)
cmd2 = [
    FFMPEG, "-y", "-ss", "120", "-i", VIDEO,
    "-filter_complex",
    "[0:v]scale=270:480,boxblur=25:2,scale=1080:1920,setsar=1:1[bg];"
    "[0:v]crop=1200:900:300:80,scale=1080:810,setsar=1:1[fg];"
    "[bg][fg]overlay=0:260[out]",
    "-map", "[out]", "-vframes", "1", "-q:v", "2",
    "assets/test_framing_2_host_focus.jpg"
]
subprocess.run(cmd2)

# Opción 3: Broadcast Card Style (Header con Johanna Tricarico / Soy Garrahan + Video centrado + Subs abajo)
cmd3 = [
    FFMPEG, "-y", "-ss", "120", "-i", VIDEO,
    "-filter_complex",
    "[0:v]scale=270:480,boxblur=20:2,scale=1080:1920,setsar=1:1[bg];"
    "[0:v]crop=1920:1080:0:0,scale=1080:608,setsar=1:1[fg];"
    "[bg][fg]overlay=0:400[out]",
    "-map", "[out]", "-vframes", "1", "-q:v", "2",
    "assets/test_framing_3_broadcast.jpg"
]
subprocess.run(cmd3)

print("Frames de encuadre generados.")
