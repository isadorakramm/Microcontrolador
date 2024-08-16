import binascii
import time
import board
import busio
import digitalio
import espcamera
import wifi
import socketpool
import ssl
import adafruit_requests
import os

def connect_to_wifi():
    #ssid = os.getenv('WIFI_SSID')
    #password = os.getenv('WIFI_PASSWORD')
    ssid = "kramm2@148"
    password = "5134992001"
    while not wifi.radio.connected:
        try:
            print("Conectando ao Wi-Fi...")
            wifi.radio.connect(ssid, password)
            print("Conectado ao Wi-Fi!")
            print(f"IP address: {wifi.radio.ipv4_address}")
        except Exception as e:
            print(f"Erro ao conectar ao Wi-Fi: {e}")
            time.sleep(5)  # Espera 5 segundos antes de tentar novamente

connect_to_wifi()

# Configuração da câmera
def init_camera():
    print("Inicializando a câmera...")
    cam = espcamera.Camera(
        # Pinos
        data_pins=board.CAMERA_DATA,
        external_clock_pin=board.CAMERA_XCLK,
        pixel_clock_pin=board.CAMERA_PCLK,
        vsync_pin=board.CAMERA_VSYNC,
        href_pin=board.CAMERA_HREF,
        i2c=board.I2C(),
        external_clock_frequency=20_000_000,
        
        #Pixel Format
        pixel_format=espcamera.PixelFormat.JPEG, #Formato JPEG para compactação de imagem.

        #Frame Size
        #frame_size=espcamera.FrameSize.QQVGA,	#: 160x120 pixels.
        #frame_size=espcamera.FrameSize.QVGA,	#: 320x240 pixels.
        #frame_size=espcamera.FrameSize.SVGA,	#: 800x600 pixels.
        #frame_size=espcamera.FrameSize.XGA,		#: 1024x768 pixels.
        #frame_size=espcamera.FrameSize.SXGA,	#: 1280x1024 pixels.
        frame_size=espcamera.FrameSize.UXGA,	#: 1600x1200 pixels.
        
        grab_mode=espcamera.GrabMode.WHEN_EMPTY
    )
    # Ajustar o brilho e o contraste
    cam.brightness = 2  # Valores típicos são entre -2 a 2
    cam.contrast = 2  # Valores típicos são entre -2 a 2
    cam.saturation = 2  # Valores típicos são entre -2 a 2
    #cam.sharpness = 1  # Valores típicos são entre -2 a 2
    
    # White Balance
    cam.whitebal = True
    
    #Gain
    #Ajusta o ganho da imagem para condições de baixa luz.
    cam.gain_ctrl = True

    #Exposure
    #Quando Truea câmera tenta controlar automaticamente a exposição.
    #Quando False, o aec_value a configuração é usada em seu lugar. 
    cam.exposure_ctrl = True
    
    
    #wb_mode : int ​
    #O modo de balanço de branco. 0 é o balanço de branco automático.
    #Os valores típicos variam de 0 a 4 inclusive. 
    cam.wb_mode = 1
    
    
    #ae_level : int 
    #O deslocamento de exposição para exposição automática. Os valores típicos variam de -2 a +2.
    cam.ae_level = -2
    
    
    #bpc : bool
    #Quando True, “compensação de ponto preto” está habilitada.
    #Isso pode tornar as partes pretas da imagem mais escuras.
    cam.bpc = True


    #wpc : bool
    #Quando True, “compensação de ponto branco” está habilitada.
    #Isso pode tornar as partes brancas da imagem mais brancas.
    cam.wpc = True
    
    
    #raw_gma: bool
    #Quando True, o modo gama bruto está ativado. 
    cam.raw_gma = True

    
    print("Modelo: ",cam.sensor_name)
    print("height: ",cam.height," x width: ",cam.width)

    
    #cam.vflip = True  # Inverte verticalmente
    #cam.hflip = True  # Inverte horizontalmente
    #cam.night_mode = True  # Ativa o modo noturno

    print("Câmera inicializada com sucesso!")
    return cam

cam = init_camera()

# Configuração do pool de soquetes e da sessão de requisições
print("Configurando o pool de soquetes e a sessão de requisições...")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
print("Configuração concluída!")

# URL do servidor Flask
url = "http://192.168.200.73:5000/upload"

while True:
    if not wifi.radio.connected:
        print("Reconectando ao Wi-Fi...")
        connect_to_wifi()

    print("Capturando imagem...")
    frame = cam.take(1)
    frame = cam.take(1)
    if isinstance(frame, memoryview):
        jpeg = frame
        print(f"Captured {len(jpeg)} bytes of jpeg data")

        # Codificar imagem em base64
        encoded_data = binascii.b2a_base64(jpeg).strip()

        # Parar a câmera antes de enviar os dados
        print("Desativando a câmera para enviar os dados...")
        cam.deinit()

        # Enviar imagem para o servidor via HTTP POST
        try:
            print("Enviando imagem para o servidor...")
            response = requests.post(url, data=encoded_data)
            print("Imagem enviada com sucesso.")
            print("Resposta do servidor:", response.text)
        except Exception as e:
            print(f"Erro ao enviar a imagem: {e}")
            # Desconectar e reconectar a rede caso ocorra erro de envio
            wifi.radio.disconnect()
            time.sleep(5)
            connect_to_wifi()

        # Reativar a câmera após enviar os dados
        print("Reativando a câmera após enviar os dados...")
        cam = init_camera()

    time.sleep(10)
